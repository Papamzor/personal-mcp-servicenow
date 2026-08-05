"""Typed read failures in the legacy auth-test tools (v4.4 Tier 0.3, PR D).

`Table_Tools.table_tools` was missing from the migration inventory. Its two
functions are registered MCP tools (`nowtestauth`, `nowtest_auth_input`) that
called `make_nws_request` with a bare `if not data:` and no exception handling,
so the shim was the only thing keeping them working — and deleting the shim
would have turned any transient read failure into an uncaught exception from a
live tool.

These are diagnostics, which makes the mislabelling worse than usual rather than
milder: `nowtestauth` reported "Authentication test failed" for a timeout, and
`nowtest_auth_input` guessed "table may not exist or no permissions" for a read
that never completed. Both are the tools someone reaches for when they are
already trying to find out what is broken, and both were prepared to blame the
wrong thing.

Module was at 11.43% line coverage before this file.
"""
import pytest
from unittest.mock import patch

from constants import TABLE_CONFIGS
from http_layer.errors import ErrorCode, ServiceNowRequestError
from Table_Tools.table_tools import nowtest_auth_input, nowtestauth

TIMEOUT = ServiceNowRequestError(
    ErrorCode.TIMEOUT, "ServiceNow request timed out", retryable=True
)
AUTH = ServiceNowRequestError(
    ErrorCode.AUTH, "ServiceNow authentication failed", status_code=401
)


def _assert_plain_failure(response, code):
    assert isinstance(response, dict), response
    assert set(response) == {"error"}, response
    assert response["error"]["code"] == code


class TestNowTestAuth:
    @pytest.mark.asyncio
    async def test_timeout_is_not_reported_as_an_auth_failure(self):
        """The point of a diagnostic is to name the right failure."""
        with patch("Table_Tools.table_tools.make_nws_request", side_effect=TIMEOUT):
            result = await nowtestauth()
        _assert_plain_failure(result, ErrorCode.TIMEOUT)
        assert "Authentication test failed" not in str(result)

    @pytest.mark.asyncio
    async def test_a_real_auth_failure_says_auth(self):
        with patch("Table_Tools.table_tools.make_nws_request", side_effect=AUTH):
            result = await nowtestauth()
        _assert_plain_failure(result, ErrorCode.AUTH)

    @pytest.mark.asyncio
    async def test_success_is_unchanged(self):
        with patch("Table_Tools.table_tools.make_nws_request") as request:
            request.return_value = {"result": [{"sys_id": "a" * 32, "name": "Someone"}]}
            result = await nowtestauth()
        assert result["status"] == "success"
        assert result["records_found"] == 1

    @pytest.mark.asyncio
    async def test_a_falsy_body_keeps_the_legacy_string(self):
        """Distinct from a failure now: a 2xx that carried no body at all.

        Kept rather than deleted as unreachable — the dispatcher returns whatever
        ServiceNow sent, and this arm is the only thing standing between an empty
        body and a TypeError on `data.get`.
        """
        with patch("Table_Tools.table_tools.make_nws_request") as request:
            request.return_value = None
            result = await nowtestauth()
        assert result == "Authentication test failed - unable to access ServiceNow API."


class TestNowTestAuthInput:
    @pytest.mark.asyncio
    async def test_timeout_is_not_reported_as_a_missing_table(self):
        with patch("Table_Tools.table_tools.make_nws_request", side_effect=TIMEOUT):
            result = await nowtest_auth_input("incident")
        _assert_plain_failure(result, ErrorCode.TIMEOUT)
        assert "may not exist" not in str(result)

    @pytest.mark.asyncio
    async def test_table_outside_the_allowlist_costs_no_request(self):
        with patch("Table_Tools.table_tools.make_nws_request") as request:
            result = await nowtest_auth_input("sys_user")
        request.assert_not_called()
        assert "not in the supported allowlist" in result.lower()

    @pytest.mark.asyncio
    async def test_empty_table_keeps_its_own_message(self):
        """Decision (b): a table that is readable but empty is a success."""
        with patch("Table_Tools.table_tools.make_nws_request") as request:
            request.return_value = {"result": []}
            result = await nowtest_auth_input("incident")
        assert "contains no records" in result

    @pytest.mark.asyncio
    async def test_success_reports_the_sample_fields(self):
        with patch("Table_Tools.table_tools.make_nws_request") as request:
            request.return_value = {"result": [{"number": "INC1", "state": "1"}]}
            result = await nowtest_auth_input("incident")
        assert result["status"] == "accessible"
        assert result["total_fields"] == 2
        assert set(result["sample_fields"]) == {"number", "state"}

    @pytest.mark.asyncio
    async def test_a_falsy_body_keeps_the_legacy_string(self):
        with patch("Table_Tools.table_tools.make_nws_request") as request:
            request.return_value = None
            result = await nowtest_auth_input("incident")
        assert "may not exist or no permissions" in result

    def test_the_allowlist_used_by_the_test_is_the_real_one(self):
        """Guards the premise of test_table_outside_the_allowlist_costs_no_request."""
        assert "incident" in TABLE_CONFIGS
        assert "sys_user" not in TABLE_CONFIGS


class TestEndToEndThroughTheRealDispatcher:
    """Both tools report the classified failure through the real dispatcher.

    If a failed read ever arrives here as `None` again, both fall back to their
    misleading strings — "Authentication test failed" for a timeout, "table may
    not exist" for a read that never completed. Module-seam mocks cannot see it.
    """

    @pytest.fixture
    def failing_transport(self, monkeypatch):
        import http_layer.request_dispatcher as dispatcher

        async def boom(url):
            raise TimeoutError()

        monkeypatch.setattr(dispatcher, "make_oauth_request", boom)

    @pytest.mark.asyncio
    async def test_nowtestauth_reports_the_timeout(self, failing_transport):
        result = await nowtestauth()
        _assert_plain_failure(result, ErrorCode.TIMEOUT)

    @pytest.mark.asyncio
    async def test_nowtest_auth_input_reports_the_timeout(self, failing_transport):
        result = await nowtest_auth_input("incident")
        _assert_plain_failure(result, ErrorCode.TIMEOUT)
