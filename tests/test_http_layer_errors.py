"""Tests for the typed read-path failure surface (v4.4 Tier 0.3).

Three contracts are locked here:

1. `classify_read_failure` maps every failure the read path can produce onto
   the seven-code vocabulary, and never onto NOT_FOUND unless ServiceNow
   actually said 404. A timeout reported as not-found is the bug this tier
   exists to remove.
2. A failed GET raises for every caller, unconditionally, and an empty result
   is still a success. The migration shim that used to convert the raise back
   into `None` for unmigrated callers is gone.
3. Every module that calls `make_nws_request` on the read path handles the
   raise. That set is derived by scanning the tree, not from a list -- the
   migration's own planning documents undercounted it by one.
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
        assert "not valid JSON" in error.message

    def test_plain_value_error_is_not_reported_as_a_json_problem(self):
        """ServiceNowOAuthClient raises ValueError('Missing OAuth configuration').

        JSONDecodeError subclasses ValueError, so pairing the two would label a
        missing-.env failure "not valid JSON" and send whoever is fixing it in
        the wrong direction. It must fall through to INTERNAL with the real text.
        """
        error = classify_read_failure(ValueError("Missing OAuth configuration for instance"))
        assert error.code == ErrorCode.INTERNAL
        assert "not valid JSON" not in error.message
        assert "Missing OAuth configuration" in error.message

    def test_unknown_exception_is_internal_never_not_found(self):
        error = classify_read_failure(RuntimeError("who knows"))
        assert error.code == ErrorCode.INTERNAL
        assert error.code != ErrorCode.NOT_FOUND

    def test_already_typed_error_passes_through_unchanged(self):
        original = ServiceNowRequestError(ErrorCode.FORBIDDEN, "denied", status_code=403)
        assert classify_read_failure(original) is original


class TestClassifyOAuthFailures:
    """A token-endpoint failure means what the same failure on the table API means."""

    def test_authentication_error_is_auth_not_internal(self):
        from oauth.exceptions import ServiceNowAuthenticationError

        error = classify_read_failure(ServiceNowAuthenticationError("bad client secret"))
        assert error.code == ErrorCode.AUTH
        assert error.retryable is False
        assert "bad client secret" in error.message

    def test_authorization_error_is_forbidden(self):
        from oauth.exceptions import ServiceNowAuthorizationError

        error = classify_read_failure(ServiceNowAuthorizationError("scope denied"))
        assert error.code == ErrorCode.FORBIDDEN

    def test_connection_error_is_retryable_http(self):
        from oauth.exceptions import ServiceNowConnectionError

        error = classify_read_failure(ServiceNowConnectionError("token endpoint unreachable"))
        assert error.code == ErrorCode.HTTP
        assert error.retryable is True

    def test_a_wrong_secret_and_a_401_agree(self):
        """Same semantic failure, two transports — one code."""
        from oauth.exceptions import ServiceNowAuthenticationError

        via_oauth = classify_read_failure(ServiceNowAuthenticationError("bad secret"))
        via_http = classify_read_failure(_status_error(401))
        assert via_oauth.code == via_http.code == ErrorCode.AUTH


class TestReadFailuresPropagate:
    def test_every_read_path_consumer_handles_the_raise(self):
        """Derived from the CODE, not from a list. The list was wrong once already.

        The migration inventory named four consumer modules. There were five:
        `Table_Tools.table_tools`, whose two functions are registered MCP tools
        with no exception handling at all. Nothing failed while the shim was
        feeding it None, and it would have started raising out of a live tool the
        moment the shim went.

        This replaces the shim-era completeness check. Completeness of an opt-in
        set stopped being the property that matters once the raise became
        unconditional; what matters now is that every module reading through this
        path is prepared to catch. A new consumer added without a handler fails
        here, named.

        Two things this deliberately does NOT buy, so nobody over-trusts it:

        * It cannot prove a handler is correct, only that the module has one.
          Correctness per module lives in the five `test_typed_read_*.py` files,
          each of which drives a real failure through the real dispatcher.
        * It is per-module, not per-call-site. A module with a handler in one
          function and none in another passes. Today none of the five has such a
          gap (checked by hand); a scan that could prove it wouldn't be a scan.

        Consumers are detected by IMPORT rather than by a `make_nws_request(`
        text match, via the AST: an aliased import
        (`from http_layer import make_nws_request as fetch`) binds the name and
        then never spells it at the call site, so a text match would miss the
        module entirely — silently, which is the failure mode that makes a guard
        worse than no guard. Parsing also ignores mentions in comments.
        """
        import ast
        import pathlib

        repo = pathlib.Path(__file__).resolve().parent.parent
        # dist/ holds a packaging copy of the tree; http_layer defines the
        # function; tests mock it. None of those are consumers.
        skip = {".venv", "venv", "dist", "build", "tests", "http_layer",
                ".git", "graphify-out", "__pycache__"}

        def imports_the_read_entry_point(tree):
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.Import):
                    names = [a.name.rsplit(".", 1)[-1] for a in node.names]
                else:
                    continue
                if "make_nws_request" in names:
                    return True
            return False

        def handles_the_typed_error(tree):
            for node in ast.walk(tree):
                if not isinstance(node, ast.ExceptHandler) or node.type is None:
                    continue
                caught = node.type.elts if isinstance(node.type, ast.Tuple) else [node.type]
                for exc in caught:
                    name = exc.attr if isinstance(exc, ast.Attribute) else getattr(exc, "id", None)
                    if name == "ServiceNowRequestError":
                        return True
            return False

        unhandled = []
        consumers = []
        for path in sorted(repo.rglob("*.py")):
            if any(part in skip for part in path.relative_to(repo).parts):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            if not imports_the_read_entry_point(tree):
                continue
            rel = str(path.relative_to(repo))
            consumers.append(rel)
            if not handles_the_typed_error(tree):
                unhandled.append(rel)

        assert len(consumers) >= 5, (
            f"scan found only {len(consumers)} consumers ({consumers}); it is "
            f"probably broken rather than the codebase having shrunk"
        )
        assert not unhandled, (
            f"read-path consumer(s) with no `except ServiceNowRequestError`: "
            f"{unhandled}. A failed GET raises unconditionally, so these would "
            f"propagate an exception to MCP clients."
        )

    @pytest.mark.asyncio
    async def test_get_failure_raises_typed_error(self, monkeypatch):
        async def boom(url):
            raise _status_error(403)

        monkeypatch.setattr(dispatcher, "make_oauth_request", boom)

        with pytest.raises(ServiceNowRequestError) as excinfo:
            await dispatcher.make_nws_request("https://example.service-now.com/api/now/table/incident")

        assert excinfo.value.code == ErrorCode.FORBIDDEN
        assert excinfo.value.status_code == 403

    @pytest.mark.asyncio
    async def test_timeout_is_a_timeout_not_a_not_found(self, monkeypatch):
        """The headline bug: a 30s deadline must never look like a missing record."""
        async def slow(url):
            raise TimeoutError()

        monkeypatch.setattr(dispatcher, "make_oauth_request", slow)

        with pytest.raises(ServiceNowRequestError) as excinfo:
            await dispatcher.make_nws_request("https://example.service-now.com/api/now/table/incident")

        assert excinfo.value.code == ErrorCode.TIMEOUT
        assert excinfo.value.retryable is True

    @pytest.mark.asyncio
    async def test_success_path_unaffected(self, monkeypatch):
        async def ok(url):
            return {"result": [{"number": "INC0012345"}]}

        monkeypatch.setattr(dispatcher, "make_oauth_request", ok)

        result = await dispatcher.make_nws_request("https://example.service-now.com/api/now/table/incident")
        assert result == {"result": [{"number": "INC0012345"}]}

    @pytest.mark.asyncio
    async def test_empty_result_is_success_not_an_error(self, monkeypatch):
        """Empty is success. Deciding it means not-found is the consumer's job."""
        async def empty(url):
            return {"result": []}

        monkeypatch.setattr(dispatcher, "make_oauth_request", empty)

        result = await dispatcher.make_nws_request("https://example.service-now.com/api/now/table/incident")
        assert result == {"result": []}


class TestResponseParsingStaysGuarded:
    """The pre-v4.4 blanket except covered the flattener for every read caller."""

    @pytest.mark.asyncio
    async def test_flattener_failure_is_classified_as_internal(self, monkeypatch):
        async def ok(url):
            return {"result": [{"number": "INC0001"}]}

        def exploding_flattener(payload):
            raise RuntimeError("parser blew up")

        monkeypatch.setattr(dispatcher, "make_oauth_request", ok)
        monkeypatch.setattr(dispatcher, "extract_display_values", exploding_flattener)

        with pytest.raises(ServiceNowRequestError) as excinfo:
            await dispatcher.make_nws_request("https://example.service-now.com/api/now/table/incident")

        assert excinfo.value.code == ErrorCode.INTERNAL
