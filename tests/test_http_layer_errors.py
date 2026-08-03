"""Tests for the typed read-path failure surface (v4.4 Tier 0.3, PR 1 of 8).

Two contracts are locked here:

1. `classify_read_failure` maps every failure the read path can produce onto
   the seven-code vocabulary, and never onto NOT_FOUND unless ServiceNow
   actually said 404. A timeout reported as not-found is the bug this tier
   exists to remove.
2. The `_legacy_none_shim` keeps behavior identical on main for callers nobody
   has migrated yet, while already raising for callers that opt in. Both
   branches are exercised so PRs 2-7 cannot silently break either one.
"""
import json

import httpx
import pytest

from http_layer.errors import (
    ALL_ERROR_CODES,
    ErrorCode,
    ServiceNowRequestError,
    classify_read_failure,
)
import http_layer.request_dispatcher as dispatcher


def _status_error(status: int) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "https://example.service-now.com/api/now/table/incident")
    response = httpx.Response(status, request=request)
    return httpx.HTTPStatusError(f"HTTP {status}", request=request, response=response)


class TestErrorVocabulary:
    def test_all_codes_are_exactly_the_seven(self):
        assert ALL_ERROR_CODES == {
            "VALIDATION", "NOT_FOUND", "AUTH", "FORBIDDEN", "TIMEOUT", "HTTP", "INTERNAL",
        }

    def test_error_dict_shape(self):
        error = ServiceNowRequestError(ErrorCode.AUTH, "nope", status_code=401)
        assert error.to_error_dict() == {"error": {"code": "AUTH", "message": "nope"}}

    def test_error_dict_carries_no_extra_keys(self):
        """§3.1: the failure shape is exactly {"error": {"code", "message"}}."""
        error = ServiceNowRequestError(ErrorCode.TIMEOUT, "slow", retryable=True)
        assert set(error.to_error_dict()["error"]) == {"code", "message"}

    def test_message_is_the_exception_str(self):
        error = ServiceNowRequestError(ErrorCode.HTTP, "boom")
        assert str(error) == "boom"


class TestClassifyStatusCodes:
    @pytest.mark.parametrize("status,expected_code,expected_retryable", [
        (400, ErrorCode.VALIDATION, False),
        (401, ErrorCode.AUTH, False),
        (403, ErrorCode.FORBIDDEN, False),
        (404, ErrorCode.NOT_FOUND, False),
        (408, ErrorCode.TIMEOUT, True),
        (429, ErrorCode.HTTP, True),
        (418, ErrorCode.HTTP, False),
        (500, ErrorCode.HTTP, True),
        (502, ErrorCode.HTTP, True),
        (503, ErrorCode.HTTP, True),
    ])
    def test_status_mapping(self, status, expected_code, expected_retryable):
        error = classify_read_failure(_status_error(status))
        assert error.code == expected_code
        assert error.status_code == status
        assert error.retryable is expected_retryable


class TestClassifyTransportFailures:
    def test_anyio_deadline_is_timeout(self):
        """anyio.fail_after raises the builtin TimeoutError, not an httpx one."""
        error = classify_read_failure(TimeoutError())
        assert error.code == ErrorCode.TIMEOUT
        assert error.retryable is True
        assert error.status_code is None

    def test_httpx_timeout_is_timeout(self):
        error = classify_read_failure(httpx.ReadTimeout("too slow"))
        assert error.code == ErrorCode.TIMEOUT
        assert error.retryable is True

    def test_connect_error_is_retryable_http_not_timeout(self):
        """Unreachable host is retryable, but it is not a deadline expiry."""
        error = classify_read_failure(httpx.ConnectError("no route"))
        assert error.code == ErrorCode.HTTP
        assert error.retryable is True

    def test_json_decode_error_is_internal_and_not_retryable(self):
        error = classify_read_failure(json.JSONDecodeError("bad", "{", 0))
        assert error.code == ErrorCode.INTERNAL
        assert error.retryable is False

    def test_unknown_exception_is_internal_never_not_found(self):
        error = classify_read_failure(RuntimeError("who knows"))
        assert error.code == ErrorCode.INTERNAL
        assert error.code != ErrorCode.NOT_FOUND

    def test_already_typed_error_passes_through_unchanged(self):
        original = ServiceNowRequestError(ErrorCode.FORBIDDEN, "denied", status_code=403)
        assert classify_read_failure(original) is original


class TestLegacyNoneShim:
    """PR 1 must not change behavior on main. PRs 2-7 flip modules one at a time."""

    def test_typed_callers_is_empty_in_pr1(self):
        assert dispatcher._TYPED_CALLERS == frozenset()

    @pytest.mark.asyncio
    async def test_unmigrated_caller_still_gets_none(self, monkeypatch):
        async def boom(url):
            raise _status_error(500)

        monkeypatch.setattr(dispatcher, "make_oauth_request", boom)
        result = await dispatcher.make_nws_request("https://example.service-now.com/api/now/table/incident")
        assert result is None

    @pytest.mark.asyncio
    async def test_migrated_caller_gets_typed_error(self, monkeypatch):
        async def boom(url):
            raise _status_error(403)

        monkeypatch.setattr(dispatcher, "make_oauth_request", boom)
        monkeypatch.setattr(dispatcher, "_TYPED_CALLERS", frozenset({__name__}))

        with pytest.raises(ServiceNowRequestError) as excinfo:
            await dispatcher.make_nws_request("https://example.service-now.com/api/now/table/incident")

        assert excinfo.value.code == ErrorCode.FORBIDDEN
        assert excinfo.value.status_code == 403

    @pytest.mark.asyncio
    async def test_timeout_reaches_migrated_caller_as_timeout_not_not_found(self, monkeypatch):
        """The headline bug: a 30s deadline must never look like a missing record."""
        async def slow(url):
            raise TimeoutError()

        monkeypatch.setattr(dispatcher, "make_oauth_request", slow)
        monkeypatch.setattr(dispatcher, "_TYPED_CALLERS", frozenset({__name__}))

        with pytest.raises(ServiceNowRequestError) as excinfo:
            await dispatcher.make_nws_request("https://example.service-now.com/api/now/table/incident")

        assert excinfo.value.code == ErrorCode.TIMEOUT
        assert excinfo.value.retryable is True

    @pytest.mark.asyncio
    async def test_success_path_untouched_by_the_shim(self, monkeypatch):
        async def ok(url):
            return {"result": [{"number": "INC0012345"}]}

        monkeypatch.setattr(dispatcher, "make_oauth_request", ok)
        monkeypatch.setattr(dispatcher, "_TYPED_CALLERS", frozenset({__name__}))

        result = await dispatcher.make_nws_request("https://example.service-now.com/api/now/table/incident")
        assert result == {"result": [{"number": "INC0012345"}]}

    @pytest.mark.asyncio
    async def test_empty_result_is_success_not_an_error(self, monkeypatch):
        """Empty is success. Deciding it means not-found is the consumer's job."""
        async def empty(url):
            return {"result": []}

        monkeypatch.setattr(dispatcher, "make_oauth_request", empty)
        monkeypatch.setattr(dispatcher, "_TYPED_CALLERS", frozenset({__name__}))

        result = await dispatcher.make_nws_request("https://example.service-now.com/api/now/table/incident")
        assert result == {"result": []}


class TestCallingModuleResolution:
    def test_resolves_to_the_caller_outside_http_layer(self):
        assert dispatcher._calling_module() == __name__

    def test_skips_intermediate_http_layer_frames(self, monkeypatch):
        """An http_layer frame between the consumer and the walk must not mask it.

        `_legacy_none_shim` lives in http_layer and calls `_calling_module()`
        one frame deeper, so reaching this module's name proves the walk climbs
        out of the package instead of stopping at the nearest frame.
        """
        monkeypatch.setattr(dispatcher, "_TYPED_CALLERS", frozenset({__name__}))
        error = ServiceNowRequestError(ErrorCode.AUTH, "denied", status_code=401)

        with pytest.raises(ServiceNowRequestError):
            dispatcher._legacy_none_shim(error)

    def test_unlisted_caller_swallowed_by_shim(self):
        error = ServiceNowRequestError(ErrorCode.AUTH, "denied", status_code=401)
        assert dispatcher._legacy_none_shim(error) is None
