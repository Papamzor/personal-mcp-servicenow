"""Typed read failures in the private-task tools (v4.4 Tier 0.3, PR D).

The module has exactly one read, and it is the sensitive kind: the pre-write
`sys_id` lookup in
`update_private_task`. Its answer decides whether a write happens, so
conflating "the task does not exist" with "the lookup failed" both mislabelled
the failure AND withheld the write (decision (d)).

`None` still means absent at `_get_task_sys_id`'s own boundary — that is what
keeps the existing `_get_task_sys_id -> None` mocks meaningful. What changed is
that a *failure* no longer arrives as None.
"""
import pytest
from unittest.mock import AsyncMock, patch

from constants import PRIVATE_TASK_NOT_FOUND_UPDATE
from http_layer.errors import ErrorCode, ServiceNowRequestError
from Table_Tools.vtb_task_tools import _get_task_sys_id, update_private_task

TIMEOUT = ServiceNowRequestError(
    ErrorCode.TIMEOUT, "ServiceNow request timed out", retryable=True
)
FORBIDDEN = ServiceNowRequestError(
    ErrorCode.FORBIDDEN, "ServiceNow returned HTTP 403", status_code=403
)
SYS_ID = "a" * 32


def _assert_plain_failure(response, code):
    assert isinstance(response, dict), response
    assert set(response) == {"error"}, response
    assert set(response["error"]) == {"code", "message"}
    assert response["error"]["code"] == code


class TestPreWriteLookup:
    @pytest.mark.asyncio
    async def test_failed_lookup_is_not_task_not_found(self):
        with patch(
            "Table_Tools.vtb_task_tools._get_task_sys_id",
            new=AsyncMock(side_effect=TIMEOUT),
        ), patch(
            "Table_Tools.vtb_task_tools._write_private_task", new=AsyncMock()
        ) as write:
            result = await update_private_task("VTB0001234", {"comments": "hi"})

        write.assert_not_called()
        _assert_plain_failure(result, ErrorCode.TIMEOUT)
        assert result != PRIVATE_TASK_NOT_FOUND_UPDATE

    @pytest.mark.asyncio
    async def test_forbidden_lookup_keeps_its_own_code(self):
        with patch(
            "Table_Tools.vtb_task_tools._get_task_sys_id",
            new=AsyncMock(side_effect=FORBIDDEN),
        ):
            result = await update_private_task("VTB0001234", {"comments": "hi"})
        _assert_plain_failure(result, ErrorCode.FORBIDDEN)

    @pytest.mark.asyncio
    async def test_absent_task_keeps_its_not_found_message(self):
        """Decision (b): absent is still absent, and the message is unchanged."""
        with patch(
            "Table_Tools.vtb_task_tools._get_task_sys_id",
            new=AsyncMock(return_value=None),
        ), patch(
            "Table_Tools.vtb_task_tools._write_private_task", new=AsyncMock()
        ) as write:
            result = await update_private_task("VTB9999999", {"comments": "hi"})

        write.assert_not_called()
        assert result == {"error": {"code": "NOT_FOUND", "message": PRIVATE_TASK_NOT_FOUND_UPDATE}}

    @pytest.mark.asyncio
    async def test_found_task_still_writes(self):
        with patch(
            "Table_Tools.vtb_task_tools._get_task_sys_id",
            new=AsyncMock(return_value=SYS_ID),
        ), patch(
            "Table_Tools.vtb_task_tools._write_private_task",
            new=AsyncMock(return_value={"number": "VTB0001234"}),
        ) as write:
            result = await update_private_task("VTB0001234", {"comments": "hi"})

        write.assert_called_once()
        assert SYS_ID in write.call_args.args[1]
        assert result == {"number": "VTB0001234"}

    @pytest.mark.asyncio
    async def test_validation_still_runs_before_the_lookup(self):
        """A rejected field must not cost a round trip."""
        with patch("Table_Tools.vtb_task_tools._get_task_sys_id") as lookup:
            result = await update_private_task("VTB0001234", {"sys_id": "nope"})
        lookup.assert_not_called()
        assert "Rejected non-updatable field(s)" in result["error"]["message"]


class TestEndToEndThroughTheRealDispatcher:
    """A failed lookup reaches `update_private_task` through the real dispatcher.

    These exercise the real `make_nws_request` rather than the module seam. That
    was originally the only way to catch a typo in the `_TYPED_CALLERS` opt-in
    list; with the shim gone the list is gone too, and what these now prove is
    the property that outlived it — a real classified failure, produced by the
    real dispatcher, is handled by this module rather than escaping it.

    Still not replaceable by the source scan in `test_http_layer_errors.py`: that
    checks a handler EXISTS, these check it does the right thing.

    Concretely: if a failure arrives as `None` again, `_get_task_sys_id` answers
    None and the update reports the task as missing while silently declining to
    write it.
    """

    @pytest.fixture
    def transport(self, monkeypatch):
        import http_layer.request_dispatcher as dispatcher

        writes = []

        class FakeClient:
            async def make_authenticated_request(self, method, url, raise_for_status=True, json=None):
                writes.append((method, url))
                return {"result": {"number": "VTB0001234"}}

        def install(get_handler):
            async def fake_get(url):
                return get_handler(url)
            monkeypatch.setattr(dispatcher, "make_oauth_request", fake_get)
            monkeypatch.setattr(dispatcher, "get_oauth_client", lambda: FakeClient())
            return writes

        return install

    @pytest.mark.asyncio
    async def test_lookup_timeout_does_not_report_the_task_missing(self, transport):
        def boom(url):
            raise TimeoutError()

        writes = transport(boom)
        result = await update_private_task("VTB0001234", {"comments": "hi"})

        assert writes == [], "no write should be attempted on an unreadable lookup"
        _assert_plain_failure(result, ErrorCode.TIMEOUT)
        assert result != PRIVATE_TASK_NOT_FOUND_UPDATE

    @pytest.mark.asyncio
    async def test_genuinely_absent_task_still_says_not_found(self, transport):
        writes = transport(lambda url: {"result": []})
        result = await update_private_task("VTB9999999", {"comments": "hi"})

        assert writes == []
        assert result == {"error": {"code": "NOT_FOUND", "message": PRIVATE_TASK_NOT_FOUND_UPDATE}}

    @pytest.mark.asyncio
    async def test_successful_lookup_writes_once(self, transport):
        writes = transport(lambda url: {"result": [{"sys_id": SYS_ID}]})
        result = await update_private_task("VTB0001234", {"comments": "hi"})

        assert len(writes) == 1
        assert writes[0][0] == "PATCH"
        assert SYS_ID in writes[0][1]
        assert result["record"] == {"number": "VTB0001234"}


class TestReadFailureStillRaisesAtTheHelperBoundary:
    @pytest.mark.asyncio
    async def test_helper_propagates(self):
        with patch(
            "Table_Tools.vtb_task_tools.make_nws_request", side_effect=TIMEOUT
        ):
            with pytest.raises(ServiceNowRequestError):
                await _get_task_sys_id("VTB0001234")

    @pytest.mark.asyncio
    async def test_helper_returns_none_for_a_genuinely_empty_result(self):
        with patch("Table_Tools.vtb_task_tools.make_nws_request") as request:
            request.return_value = {"result": []}
            assert await _get_task_sys_id("VTB9999999") is None
