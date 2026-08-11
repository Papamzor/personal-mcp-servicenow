"""Typed read failures in the diagnostic tool (v4.4 Tier 0.3 / v5.0 Tier 2).

`health_check` (v5.0 "Boron") is the single diagnostic tool. It absorbed the
five v4 diagnostics — including `nowtestauth` (live auth probe) and
`nowtest_auth_input` (table schema peek) — and it calls `make_nws_request`, so
`utility_tools` is now the read-path consumer that `Table_Tools.table_tools`
used to be. It must report the *classified* failure, not blame auth for a
timeout: exactly the mislabelling those tools committed before Tier 0.3.

This is the fifth `test_typed_read_*.py`, replacing the table_tools one when
that module was deleted.
"""
import pytest
from unittest.mock import patch

from constants import TABLE_CONFIGS
from http_layer.errors import ErrorCode, ServiceNowRequestError
from utility_tools import health_check

TIMEOUT = ServiceNowRequestError(
    ErrorCode.TIMEOUT, "ServiceNow request timed out", retryable=True
)
AUTH = ServiceNowRequestError(
    ErrorCode.AUTH, "ServiceNow authentication failed", status_code=401
)

_FAKE_AUTH = {"instance": "https://example.service-now.com", "auth_type": "oauth"}


class TestConnectivityProbe:
    @pytest.mark.asyncio
    async def test_timeout_is_not_reported_as_an_auth_failure(self):
        """The point of a diagnostic is to name the right failure."""
        with patch("utility_tools.get_auth_info", return_value=_FAKE_AUTH), \
             patch("utility_tools.make_nws_request", side_effect=TIMEOUT):
            result = await health_check()
        assert result["connection"] == "failed"
        assert result["error"]["code"] == ErrorCode.TIMEOUT
        assert "Authentication test failed" not in str(result)

    @pytest.mark.asyncio
    async def test_a_real_auth_failure_says_auth(self):
        with patch("utility_tools.get_auth_info", return_value=_FAKE_AUTH), \
             patch("utility_tools.make_nws_request", side_effect=AUTH):
            result = await health_check()
        assert result["connection"] == "failed"
        assert result["error"]["code"] == ErrorCode.AUTH

    @pytest.mark.asyncio
    async def test_success_reports_ok_and_the_config(self):
        with patch("utility_tools.get_auth_info", return_value=_FAKE_AUTH), \
             patch("utility_tools.make_nws_request") as request:
            request.return_value = {"result": [{"sys_id": "a" * 32, "name": "Someone"}]}
            result = await health_check()
        assert result["server"] == "running"
        assert result["connection"] == "ok"
        assert result["auth"] == _FAKE_AUTH


class TestSchemaProbe:
    @pytest.mark.asyncio
    async def test_timeout_is_not_reported_as_a_missing_table(self):
        with patch("utility_tools.get_auth_info", return_value=_FAKE_AUTH), \
             patch("utility_tools.make_nws_request", side_effect=TIMEOUT):
            result = await health_check(probe_table="incident")
        assert result["connection"] == "failed"
        assert result["error"]["code"] == ErrorCode.TIMEOUT
        assert "may not exist" not in str(result)

    @pytest.mark.asyncio
    async def test_table_outside_the_allowlist_costs_no_request(self):
        with patch("utility_tools.get_auth_info", return_value=_FAKE_AUTH), \
             patch("utility_tools.make_nws_request") as request:
            result = await health_check(probe_table="sys_user")
        request.assert_not_called()
        assert result["connection"] == "skipped"
        assert result["error"]["code"] == ErrorCode.VALIDATION
        assert "not in the supported allowlist" in result["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_empty_table_is_a_success_with_no_sample_fields(self):
        with patch("utility_tools.get_auth_info", return_value=_FAKE_AUTH), \
             patch("utility_tools.make_nws_request") as request:
            request.return_value = {"result": []}
            result = await health_check(probe_table="incident")
        assert result["connection"] == "ok"
        assert result["has_records"] is False
        assert result["sample_fields"] == []

    @pytest.mark.asyncio
    async def test_success_reports_the_sample_fields(self):
        with patch("utility_tools.get_auth_info", return_value=_FAKE_AUTH), \
             patch("utility_tools.make_nws_request") as request:
            request.return_value = {"result": [{"number": "INC1", "state": "1"}]}
            result = await health_check(probe_table="incident")
        assert result["connection"] == "ok"
        assert result["table"] == "incident"
        assert result["total_fields"] == 2
        assert set(result["sample_fields"]) == {"number", "state"}

    def test_the_allowlist_used_by_the_test_is_the_real_one(self):
        """Guards the premise of test_table_outside_the_allowlist_costs_no_request."""
        assert "incident" in TABLE_CONFIGS
        assert "sys_user" not in TABLE_CONFIGS


class TestEndToEndThroughTheRealDispatcher:
    """health_check reports the classified failure through the real dispatcher.

    If a failed read ever arrives here as `None` again, the probe would fall
    back to reporting success. Module-seam mocks cannot see that.
    """

    @pytest.fixture
    def failing_transport(self, monkeypatch):
        import http_layer.request_dispatcher as dispatcher

        async def boom(url):
            raise TimeoutError()

        monkeypatch.setattr(dispatcher, "make_oauth_request", boom)

    @pytest.mark.asyncio
    async def test_connectivity_probe_reports_the_timeout(self, failing_transport):
        with patch("utility_tools.get_auth_info", return_value=_FAKE_AUTH):
            result = await health_check()
        assert result["connection"] == "failed"
        assert result["error"]["code"] == ErrorCode.TIMEOUT

    @pytest.mark.asyncio
    async def test_schema_probe_reports_the_timeout(self, failing_transport):
        with patch("utility_tools.get_auth_info", return_value=_FAKE_AUTH):
            result = await health_check(probe_table="incident")
        assert result["connection"] == "failed"
        assert result["error"]["code"] == ErrorCode.TIMEOUT
