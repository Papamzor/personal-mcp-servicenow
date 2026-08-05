"""Typed read failures in the CMDB tools (v4.4 Tier 0.3, PR B).

`Table_Tools.cmdb_tools` joins `_TYPED_CALLERS`, so a failed GET raises instead
of returning None. Two things are locked here:

1. Every public function returns `{"error": {"code", "message"}}` on a failure
   instead of one of its not-found strings (NO_CIS_FOUND_FOR_TYPE, CI_NOT_FOUND,
   ...) or its ERROR_* string, which dropped the code. Empty result sets keep
   their existing strings — empty is success. The module's return type is
   `dict | str` for the duration; Tier 3.1 removes the strings.

2. `_probe_ci_table` no longer reports a failed probe as "this table has no such
   CI". That conflation was worse than a wrong message: under the concurrent
   gather in `get_ci_details`, a timeout on cmdb_ci_server made a server CI
   appear to live in the base cmdb_ci table.

`TestEndToEndThroughTheRealDispatcher` matters more here than in PR A: the probes
run under `asyncio.gather`, and `_calling_module()` resolves the caller by
walking the stack. A Task boundary severs the frame chain, so the wiring is
verified against the real dispatcher rather than argued about.
"""
import pytest
from unittest.mock import AsyncMock, patch

from constants import (
    CI_NOT_FOUND,
    ERROR_FINDING_SIMILAR_CIS,
    ERROR_QUICK_CI_SEARCH,
    ERROR_SEARCHING_CIS_BY_TYPE,
    NO_CIS_FOUND_FOR_TYPE,
    NO_CIS_FOUND_MATCHING_CRITERIA,
    NO_SIMILAR_CIS_FOUND,
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


def _by_table(mapping, default=None):
    """Fake make_nws_request that answers per table name in the URL.

    Values are either a payload dict or an exception to raise, so a test can say
    "cmdb_ci_server times out, cmdb_ci has the row" without ordering assumptions
    about how the concurrent probes interleave.
    """
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
        assert result != NO_CIS_FOUND_FOR_TYPE.format(ci_type="cmdb_ci_server")

    @pytest.mark.asyncio
    async def test_find_by_type_empty_keeps_its_not_found_string(self):
        with patch("Table_Tools.cmdb_tools.make_nws_request") as mock_request:
            mock_request.return_value = {"result": []}
            result = await find_cis_by_type("cmdb_ci_server")
        assert result == NO_CIS_FOUND_FOR_TYPE.format(ci_type="cmdb_ci_server")

    @pytest.mark.asyncio
    async def test_find_by_type_unexpected_error_still_returns_its_string(self):
        """Narrowing the except must not remove the catch-all for real bugs."""
        with patch(
            "Table_Tools.cmdb_tools.make_nws_request", side_effect=RuntimeError("boom")
        ):
            result = await find_cis_by_type("cmdb_ci_server")
        assert result == ERROR_SEARCHING_CIS_BY_TYPE

    @pytest.mark.asyncio
    async def test_search_by_attributes_failure_is_not_no_cis_matching(self):
        with patch("Table_Tools.cmdb_tools.make_nws_request", side_effect=FORBIDDEN):
            result = await search_cis_by_attributes(name="srv-app")
        _assert_plain_failure(result, ErrorCode.FORBIDDEN)

    @pytest.mark.asyncio
    async def test_search_by_attributes_empty_keeps_its_not_found_string(self):
        with patch("Table_Tools.cmdb_tools.make_nws_request") as mock_request:
            mock_request.return_value = {"result": []}
            result = await search_cis_by_attributes(name="srv-app")
        assert result == NO_CIS_FOUND_MATCHING_CRITERIA

    @pytest.mark.asyncio
    async def test_quick_search_failure_is_not_no_cis_found(self):
        with patch("Table_Tools.cmdb_tools.make_nws_request", side_effect=TIMEOUT):
            result = await quick_ci_search("srv-app-01")
        _assert_plain_failure(result, ErrorCode.TIMEOUT)

    @pytest.mark.asyncio
    async def test_quick_search_unexpected_error_still_returns_its_string(self):
        with patch(
            "Table_Tools.cmdb_tools.make_nws_request", side_effect=RuntimeError("boom")
        ):
            result = await quick_ci_search("srv-app-01")
        assert result == ERROR_QUICK_CI_SEARCH

    @pytest.mark.asyncio
    async def test_get_all_ci_types_failure_is_not_no_types_found(self):
        with patch("Table_Tools.cmdb_tools.make_nws_request", side_effect=TIMEOUT):
            result = await get_all_ci_types()
        _assert_plain_failure(result, ErrorCode.TIMEOUT)


class TestProbeFailuresAreNotAbsence:
    """The headline bug: one timed-out probe attributing a CI to the wrong table."""

    @pytest.mark.asyncio
    async def test_failed_probe_does_not_attribute_the_ci_to_a_broader_table(self):
        """cmdb_ci_server times out; the base cmdb_ci row must NOT be the answer.

        cmdb_ci holds every CI, so the base table almost always has a row. If a
        failed probe counted as absence, `get_ci_details` would confidently
        report ci_table="cmdb_ci" for a machine that is a server.
        """
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
        assert result["result"] == CI_ROW

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
    async def test_all_probes_empty_still_says_ci_not_found(self):
        with patch("Table_Tools.cmdb_tools.make_nws_request", new=_by_table({})):
            result = await get_ci_details("CI0009999")
        assert result == CI_NOT_FOUND.format(ci_number="CI0009999")

    @pytest.mark.asyncio
    async def test_explicit_ci_type_failure_returns_the_error(self):
        with patch("Table_Tools.cmdb_tools.make_nws_request", side_effect=TIMEOUT):
            result = await get_ci_details("CI0001000", ci_type="cmdb_ci_server")
        _assert_plain_failure(result, ErrorCode.TIMEOUT)

    @pytest.mark.asyncio
    async def test_unexpected_probe_exception_still_propagates(self):
        """A real bug must not be laundered into a not-found string."""
        fake = _by_table({"cmdb_ci_server": RuntimeError("boom")})
        with patch("Table_Tools.cmdb_tools.make_nws_request", new=fake):
            with pytest.raises(RuntimeError):
                await get_ci_details("CI0001000")


class TestSimilarCis:
    @pytest.mark.asyncio
    async def test_lookup_failure_is_passed_through_not_indexed_into(self):
        """get_ci_details can answer with a failure dict, which has no 'result'."""
        with patch(
            "Table_Tools.cmdb_tools.get_ci_details",
            new=AsyncMock(return_value=TIMEOUT.to_error_dict()),
        ):
            result = await similar_cis_for_ci("CI0001000")
        _assert_plain_failure(result, ErrorCode.TIMEOUT)

    @pytest.mark.asyncio
    async def test_search_failure_is_not_no_similar_cis(self):
        details = {"ci_table": "cmdb_ci_server", "ci_number": "CI0001000", "result": {
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
        assert result != NO_SIMILAR_CIS_FOUND.format(ci_number="CI0001000")

    @pytest.mark.asyncio
    async def test_genuine_no_similar_cis_keeps_its_string(self):
        details = {"ci_table": "cmdb_ci_server", "ci_number": "CI0001000", "result": {
            "sys_class_name": "Server", "location": "Brussels", "operational_status": "1",
        }}
        with patch(
            "Table_Tools.cmdb_tools.get_ci_details", new=AsyncMock(return_value=details)
        ), patch(
            "Table_Tools.cmdb_tools.search_cis_by_attributes",
            new=AsyncMock(return_value=NO_CIS_FOUND_MATCHING_CRITERIA),
        ):
            result = await similar_cis_for_ci("CI0001000")
        assert result == NO_SIMILAR_CIS_FOUND.format(ci_number="CI0001000")

    @pytest.mark.asyncio
    async def test_unexpected_error_in_the_lookup_half_returns_its_string(self):
        """get_ci_details re-raises real bugs; this function still answers with
        its own ERROR_* string, the same as for a bug in the search half."""
        with patch(
            "Table_Tools.cmdb_tools.get_ci_details",
            new=AsyncMock(side_effect=RuntimeError("boom")),
        ):
            result = await similar_cis_for_ci("CI0001000")
        assert result == ERROR_FINDING_SIMILAR_CIS

    @pytest.mark.asyncio
    async def test_unexpected_error_still_returns_its_string(self):
        details = {"ci_table": "cmdb_ci_server", "ci_number": "CI0001000", "result": {
            "sys_class_name": "Server",
        }}
        with patch(
            "Table_Tools.cmdb_tools.get_ci_details", new=AsyncMock(return_value=details)
        ), patch(
            "Table_Tools.cmdb_tools.search_cis_by_attributes",
            new=AsyncMock(side_effect=RuntimeError("boom")),
        ):
            result = await similar_cis_for_ci("CI0001000")
        assert result == ERROR_FINDING_SIMILAR_CIS


class TestEndToEndThroughTheRealDispatcher:
    """Proves the _TYPED_CALLERS entry resolves — including across asyncio.gather.

    `_calling_module()` walks frames outward from the dispatcher. The probes in
    `get_ci_details` each run in their own Task, so this is the case where a
    frame-walk could plausibly fail to find `Table_Tools.cmdb_tools`.
    """

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
    async def test_empty_probes_through_the_real_dispatcher_say_not_found(self, monkeypatch):
        import http_layer.request_dispatcher as dispatcher

        async def empty(url):
            return {"result": []}

        monkeypatch.setattr(dispatcher, "make_oauth_request", empty)
        result = await get_ci_details("CI0009999")
        assert result == CI_NOT_FOUND.format(ci_number="CI0009999")
