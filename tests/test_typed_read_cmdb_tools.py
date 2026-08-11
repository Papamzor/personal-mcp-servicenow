"""Typed read failures + response contract in the CMDB tools.

v4.4 Tier 0.3 gave the read path typed failures; v5.0 "Boron" Tier 3.1 removed
the 16 bare strings this module used to return. Locked here:

1. A failure returns `{"error": {"code", "message"}}` — a classified read
   failure carries its transport code; a genuine bug (bare `except Exception`)
   carries INTERNAL with the module's ERROR_* base text. Never a not-found
   string, never a bare error string.
2. An empty result set is SUCCESS: an empty `list_response` for the list tools,
   `record_response(None)` for the single-record get_ci_details. Deciding empty
   means "not found" is the caller's call.
3. `_probe_ci_table` still never reports a failed probe as "this table has no
   such CI" — a timeout on cmdb_ci_server must not attribute a server CI to the
   base cmdb_ci table.

`TestEndToEndThroughTheRealDispatcher` drives failures through the real
dispatcher rather than the module seam.
"""
import pytest
from unittest.mock import AsyncMock, patch

from constants import (
    ERROR_FINDING_SIMILAR_CIS,
    ERROR_GETTING_CI_TYPES,
    ERROR_QUICK_CI_SEARCH,
    ERROR_SEARCHING_CIS,
    ERROR_SEARCHING_CIS_BY_TYPE,
)
from http_layer.errors import ErrorCode, ServiceNowRequestError
from Table_Tools.cmdb_tools import (
    DEFAULT_CI_PROBE_TABLES,
    find_cis_by_type,
    get_all_ci_types,
    get_ci_details,
    quick_ci_search,
    search_cis_by_attributes,
    similar_cis_for_ci,
)

TIMEOUT = ServiceNowRequestError(
    ErrorCode.TIMEOUT, "ServiceNow request timed out", retryable=True
)
FORBIDDEN = ServiceNowRequestError(
    ErrorCode.FORBIDDEN, "ServiceNow returned HTTP 403", status_code=403
)

CI_ROW = {"number": "CI0001000", "name": "srv-app-01", "sys_class_name": "Server"}


def _assert_plain_failure(response, code):
    assert isinstance(response, dict), response
    assert set(response) == {"error"}, response
    assert set(response["error"]) == {"code", "message"}
    assert response["error"]["code"] == code


def _assert_internal(response, message):
    """A bare-except catch-all: INTERNAL carrying the module's base text."""
    assert response["error"]["code"] == ErrorCode.INTERNAL
    assert response["error"]["message"] == message


def _assert_empty_list(response):
    assert response["result"] == []
    assert response["returned_count"] == 0
    assert "error" not in response


def _by_table(mapping, default=None):
    """Fake make_nws_request that answers per table name in the URL."""
    async def fake(url, *args, **kwargs):
        table = url.split("/api/now/table/")[1].split("?")[0]
        outcome = mapping.get(table, default)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome if outcome is not None else {"result": []}

    return fake


class TestSingleRequestReads:
    @pytest.mark.asyncio
    async def test_find_by_type_failure_is_not_no_cis_found(self):
        with patch("Table_Tools.cmdb_tools.make_nws_request", side_effect=TIMEOUT):
            result = await find_cis_by_type("cmdb_ci_server")
        _assert_plain_failure(result, ErrorCode.TIMEOUT)

    @pytest.mark.asyncio
    async def test_find_by_type_empty_is_an_empty_list(self):
        with patch("Table_Tools.cmdb_tools.make_nws_request") as mock_request:
            mock_request.return_value = {"result": []}
            result = await find_cis_by_type("cmdb_ci_server")
        _assert_empty_list(result)
        assert result["ci_type"] == "cmdb_ci_server"

    @pytest.mark.asyncio
    async def test_find_by_type_unexpected_error_is_internal(self):
        """Narrowing the except must not remove the catch-all for real bugs."""
        with patch(
            "Table_Tools.cmdb_tools.make_nws_request", side_effect=RuntimeError("boom")
        ):
            result = await find_cis_by_type("cmdb_ci_server")
        _assert_internal(result, ERROR_SEARCHING_CIS_BY_TYPE)

    @pytest.mark.asyncio
    async def test_search_by_attributes_failure_is_not_no_cis_matching(self):
        with patch("Table_Tools.cmdb_tools.make_nws_request", side_effect=FORBIDDEN):
            result = await search_cis_by_attributes(name="srv-app")
        _assert_plain_failure(result, ErrorCode.FORBIDDEN)

    @pytest.mark.asyncio
    async def test_search_by_attributes_empty_is_an_empty_list(self):
        with patch("Table_Tools.cmdb_tools.make_nws_request") as mock_request:
            mock_request.return_value = {"result": []}
            result = await search_cis_by_attributes(name="srv-app")
        _assert_empty_list(result)

    @pytest.mark.asyncio
    async def test_search_by_attributes_unexpected_error_is_internal(self):
        with patch(
            "Table_Tools.cmdb_tools.make_nws_request", side_effect=RuntimeError("boom")
        ):
            result = await search_cis_by_attributes(name="srv-app")
        _assert_internal(result, ERROR_SEARCHING_CIS)

    @pytest.mark.asyncio
    async def test_quick_search_failure_is_not_no_cis_found(self):
        with patch("Table_Tools.cmdb_tools.make_nws_request", side_effect=TIMEOUT):
            result = await quick_ci_search("srv-app-01")
        _assert_plain_failure(result, ErrorCode.TIMEOUT)

    @pytest.mark.asyncio
    async def test_quick_search_unexpected_error_is_internal(self):
        with patch(
            "Table_Tools.cmdb_tools.make_nws_request", side_effect=RuntimeError("boom")
        ):
            result = await quick_ci_search("srv-app-01")
        _assert_internal(result, ERROR_QUICK_CI_SEARCH)

    @pytest.mark.asyncio
    async def test_get_all_ci_types_failure_is_not_no_types_found(self):
        with patch("Table_Tools.cmdb_tools.make_nws_request", side_effect=TIMEOUT):
            result = await get_all_ci_types()
        _assert_plain_failure(result, ErrorCode.TIMEOUT)

    @pytest.mark.asyncio
    async def test_get_all_ci_types_empty_is_an_empty_list(self):
        with patch("Table_Tools.cmdb_tools.make_nws_request") as mock_request:
            mock_request.return_value = {"result": []}
            result = await get_all_ci_types()
        _assert_empty_list(result)

    @pytest.mark.asyncio
    async def test_get_all_ci_types_unexpected_error_is_internal(self):
        with patch(
            "Table_Tools.cmdb_tools.make_nws_request", side_effect=RuntimeError("boom")
        ):
            result = await get_all_ci_types()
        _assert_internal(result, ERROR_GETTING_CI_TYPES)


class TestProbeFailuresAreNotAbsence:
    """The headline bug: one timed-out probe attributing a CI to the wrong table."""

    @pytest.mark.asyncio
    async def test_failed_probe_does_not_attribute_the_ci_to_a_broader_table(self):
        """cmdb_ci_server times out; the base cmdb_ci row must NOT be the answer."""
        fake = _by_table({
            "cmdb_ci_server": TIMEOUT,
            "cmdb_ci": {"result": [CI_ROW]},
        })
        with patch("Table_Tools.cmdb_tools.make_nws_request", new=fake):
            result = await get_ci_details("CI0001000")
        _assert_plain_failure(result, ErrorCode.TIMEOUT)

    @pytest.mark.asyncio
    async def test_failure_after_a_hit_does_not_spoil_the_answer(self):
        """A higher-priority table already decided; later failures are irrelevant."""
        assert DEFAULT_CI_PROBE_TABLES[0] == "cmdb_ci_server"
        fake = _by_table({
            "cmdb_ci_server": {"result": [CI_ROW]},
            "cmdb_ci_database": TIMEOUT,
            "cmdb_ci": TIMEOUT,
        })
        with patch("Table_Tools.cmdb_tools.make_nws_request", new=fake):
            result = await get_ci_details("CI0001000")
        assert result["ci_table"] == "cmdb_ci_server"
        assert result["record"] == CI_ROW

    @pytest.mark.asyncio
    async def test_priority_order_is_still_most_specific_first(self):
        fake = _by_table({
            "cmdb_ci_computer": {"result": [CI_ROW]},
            "cmdb_ci": {"result": [CI_ROW]},
        })
        with patch("Table_Tools.cmdb_tools.make_nws_request", new=fake):
            result = await get_ci_details("CI0001000")
        assert result["ci_table"] == "cmdb_ci_computer"

    @pytest.mark.asyncio
    async def test_all_probes_empty_is_a_null_record(self):
        with patch("Table_Tools.cmdb_tools.make_nws_request", new=_by_table({})):
            result = await get_ci_details("CI0009999")
        assert result["record"] is None
        assert result["ci_number"] == "CI0009999"

    @pytest.mark.asyncio
    async def test_explicit_ci_type_failure_returns_the_error(self):
        with patch("Table_Tools.cmdb_tools.make_nws_request", side_effect=TIMEOUT):
            result = await get_ci_details("CI0001000", ci_type="cmdb_ci_server")
        _assert_plain_failure(result, ErrorCode.TIMEOUT)

    @pytest.mark.asyncio
    async def test_unexpected_probe_exception_still_propagates(self):
        """A real bug must not be laundered into a not-found record."""
        fake = _by_table({"cmdb_ci_server": RuntimeError("boom")})
        with patch("Table_Tools.cmdb_tools.make_nws_request", new=fake):
            with pytest.raises(RuntimeError):
                await get_ci_details("CI0001000")


class TestSimilarCis:
    @pytest.mark.asyncio
    async def test_lookup_failure_is_passed_through_not_indexed_into(self):
        """get_ci_details can answer with a failure dict, which has no 'record'."""
        with patch(
            "Table_Tools.cmdb_tools.get_ci_details",
            new=AsyncMock(return_value=TIMEOUT.to_error_dict()),
        ):
            result = await similar_cis_for_ci("CI0001000")
        _assert_plain_failure(result, ErrorCode.TIMEOUT)

    @pytest.mark.asyncio
    async def test_seed_ci_not_found_is_an_empty_list(self):
        """A record=None seed has no attributes to match — empty, not an error."""
        with patch(
            "Table_Tools.cmdb_tools.get_ci_details",
            new=AsyncMock(return_value={"record": None, "ci_number": "CI0001000"}),
        ):
            result = await similar_cis_for_ci("CI0001000")
        _assert_empty_list(result)
        assert result["original_ci"] == "CI0001000"

    @pytest.mark.asyncio
    async def test_seed_with_only_a_class_is_empty_not_validation(self):
        """Regression: a seed with sys_class_name but no location/status.

        _extract_ci_search_attributes then yields only ci_type, which
        search_cis_by_attributes rejects as VALIDATION. Pre-contract that bare
        string fell through to a soft "no similar CIs"; the typed error would
        make it a hard failure. The sparse-attrs guard must short-circuit to an
        empty list BEFORE any request — so the real search is never reached.
        """
        details = {
            "ci_table": "cmdb_ci_server",
            "ci_number": "CI0001000",
            "record": {"sys_class_name": "Server", "operational_status": ""},
        }
        capture_urls = []

        async def capture(url, *a, **k):
            capture_urls.append(url)
            return {"result": []}

        with patch(
            "Table_Tools.cmdb_tools.get_ci_details", new=AsyncMock(return_value=details)
        ), patch("Table_Tools.cmdb_tools.make_nws_request", new=capture):
            result = await similar_cis_for_ci("CI0001000")

        _assert_empty_list(result)
        assert result["original_ci"] == "CI0001000"
        assert capture_urls == [], "sparse attrs must not reach search_cis_by_attributes"

    @pytest.mark.asyncio
    async def test_search_failure_is_not_no_similar_cis(self):
        details = {"ci_table": "cmdb_ci_server", "ci_number": "CI0001000", "record": {
            "sys_class_name": "Server", "location": "Brussels", "operational_status": "1",
        }}
        with patch(
            "Table_Tools.cmdb_tools.get_ci_details", new=AsyncMock(return_value=details)
        ), patch(
            "Table_Tools.cmdb_tools.search_cis_by_attributes",
            new=AsyncMock(return_value=FORBIDDEN.to_error_dict()),
        ):
            result = await similar_cis_for_ci("CI0001000")
        _assert_plain_failure(result, ErrorCode.FORBIDDEN)

    @pytest.mark.asyncio
    async def test_genuine_no_similar_cis_is_an_empty_list(self):
        details = {"ci_table": "cmdb_ci_server", "ci_number": "CI0001000", "record": {
            "sys_class_name": "Server", "location": "Brussels", "operational_status": "1",
        }}
        with patch(
            "Table_Tools.cmdb_tools.get_ci_details", new=AsyncMock(return_value=details)
        ), patch(
            "Table_Tools.cmdb_tools.search_cis_by_attributes",
            new=AsyncMock(return_value={"result": [], "returned_count": 0, "truncated": False}),
        ):
            result = await similar_cis_for_ci("CI0001000")
        _assert_empty_list(result)

    @pytest.mark.asyncio
    async def test_unexpected_error_in_the_lookup_half_is_internal(self):
        """get_ci_details re-raises real bugs; this function answers INTERNAL."""
        with patch(
            "Table_Tools.cmdb_tools.get_ci_details",
            new=AsyncMock(side_effect=RuntimeError("boom")),
        ):
            result = await similar_cis_for_ci("CI0001000")
        _assert_internal(result, ERROR_FINDING_SIMILAR_CIS)

    @pytest.mark.asyncio
    async def test_unexpected_error_in_the_search_half_is_internal(self):
        # location present so the sparse-attrs guard passes and search is reached.
        details = {"ci_table": "cmdb_ci_server", "ci_number": "CI0001000", "record": {
            "sys_class_name": "Server", "location": "Brussels",
        }}
        with patch(
            "Table_Tools.cmdb_tools.get_ci_details", new=AsyncMock(return_value=details)
        ), patch(
            "Table_Tools.cmdb_tools.search_cis_by_attributes",
            new=AsyncMock(side_effect=RuntimeError("boom")),
        ):
            result = await similar_cis_for_ci("CI0001000")
        _assert_internal(result, ERROR_FINDING_SIMILAR_CIS)


class TestEndToEndThroughTheRealDispatcher:
    """Failures reach this module through the real dispatcher, gather included."""

    @pytest.mark.asyncio
    async def test_timeout_reaches_find_cis_by_type(self, monkeypatch):
        import http_layer.request_dispatcher as dispatcher

        async def slow(url):
            raise TimeoutError()

        monkeypatch.setattr(dispatcher, "make_oauth_request", slow)
        result = await find_cis_by_type("cmdb_ci_server")
        _assert_plain_failure(result, ErrorCode.TIMEOUT)

    @pytest.mark.asyncio
    async def test_timeout_inside_a_gathered_probe_reaches_get_ci_details(self, monkeypatch):
        import http_layer.request_dispatcher as dispatcher

        async def slow(url):
            raise TimeoutError()

        monkeypatch.setattr(dispatcher, "make_oauth_request", slow)
        result = await get_ci_details("CI0001000")
        _assert_plain_failure(result, ErrorCode.TIMEOUT)

    @pytest.mark.asyncio
    async def test_empty_probes_through_the_real_dispatcher_are_a_null_record(self, monkeypatch):
        import http_layer.request_dispatcher as dispatcher

        async def empty(url):
            return {"result": []}

        monkeypatch.setattr(dispatcher, "make_oauth_request", empty)
        result = await get_ci_details("CI0009999")
        assert result["record"] is None
        assert result["ci_number"] == "CI0009999"
