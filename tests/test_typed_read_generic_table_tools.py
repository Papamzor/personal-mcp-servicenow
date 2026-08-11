"""Typed read failures through the generic read path (v4.4 Tier 0.3, PR A).

`Table_Tools.generic_table_tools` was the first module migrated, so a failed
GET arrives as a raised `ServiceNowRequestError` instead of `None`. What is
locked here:

* a failure returns `{"error": {"code", "message"}}` and nothing else — never a
  not-found message, never a bare error string;
* an empty result set still returns the not-found message (empty is success);
* a page failing mid-pagination keeps the rows already collected and marks the
  response `partial`, while a first-page failure is a plain error;
* the modules that re-wrap these responses (`consolidated_tools`) do not
  relabel a failure as "0 records found".

The end-to-end tests at the bottom go through the real dispatcher; everything
above patches `make_nws_request` inside the consumer module and so cannot see
whether the wiring below it actually works.
"""
import pytest
from unittest.mock import AsyncMock, patch

from http_layer.errors import ErrorCode, ServiceNowRequestError
from Table_Tools.generic_table_tools import (
    PartialPageReadError,
    _make_paginated_request,
    find_similar_records,
    get_record_description,
    get_record_details,
    get_records_by_priority,
    query_table_by_text,
    query_table_with_filters,
    TableFilterParams,
)

TIMEOUT = ServiceNowRequestError(
    ErrorCode.TIMEOUT, "ServiceNow request timed out", retryable=True
)
FORBIDDEN = ServiceNowRequestError(
    ErrorCode.FORBIDDEN, "ServiceNow returned HTTP 403", status_code=403
)


def _rows(count, prefix="INC"):
    return [{"number": f"{prefix}{i:07d}", "short_description": "db down"} for i in range(count)]


def _assert_plain_failure(response, code):
    """The §3.1 failure shape: exactly {"error": {"code", "message"}}."""
    assert set(response) == {"error"}, response
    assert set(response["error"]) == {"code", "message"}
    assert response["error"]["code"] == code
    assert "result" not in response


class TestSingleRecordReads:
    """The two inverted labels: a transport failure reported as a missing record."""

    @pytest.mark.asyncio
    async def test_description_timeout_is_not_record_not_found(self):
        with patch("Table_Tools.generic_table_tools.make_nws_request", side_effect=TIMEOUT):
            result = await get_record_description("incident", "INC0012345")
        _assert_plain_failure(result, ErrorCode.TIMEOUT)

    @pytest.mark.asyncio
    async def test_details_timeout_is_not_record_not_found(self):
        with patch("Table_Tools.generic_table_tools.make_nws_request", side_effect=TIMEOUT):
            result = await get_record_details("incident", "INC0012345")
        _assert_plain_failure(result, ErrorCode.TIMEOUT)

    @pytest.mark.asyncio
    async def test_forbidden_keeps_its_own_code(self):
        """Codes are not collapsed: a 403 must not read as a timeout or a 404."""
        with patch("Table_Tools.generic_table_tools.make_nws_request", side_effect=FORBIDDEN):
            result = await get_record_details("incident", "INC0012345")
        _assert_plain_failure(result, ErrorCode.FORBIDDEN)

    @pytest.mark.asyncio
    async def test_empty_result_is_a_record_miss_not_a_failure(self):
        with patch("Table_Tools.generic_table_tools.make_nws_request") as mock_request:
            mock_request.return_value = {"result": []}
            result = await get_record_details("incident", "INC0099999")
        assert result == {"record": None}
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_row_returns_under_record_key(self):
        row = {"number": "INC0012345", "short_description": "db down"}
        with patch("Table_Tools.generic_table_tools.make_nws_request") as mock_request:
            mock_request.return_value = {"result": [row]}
            result = await get_record_details("incident", "INC0012345")
        assert result == {"record": row}


class TestPaginationPartialReads:
    """Collected rows survive a later page failing."""

    @pytest.mark.asyncio
    async def test_first_page_failure_propagates_plain(self):
        with patch("Table_Tools.generic_table_tools.make_nws_request", side_effect=TIMEOUT):
            with pytest.raises(ServiceNowRequestError) as excinfo:
                await _make_paginated_request("https://x/api/now/table/incident?a=b", max_results=500)
        assert excinfo.value.code == ErrorCode.TIMEOUT
        assert not isinstance(excinfo.value, PartialPageReadError)

    @pytest.mark.asyncio
    async def test_second_page_failure_keeps_first_page_rows(self):
        page_one = {"result": _rows(250)}
        with patch(
            "Table_Tools.generic_table_tools.make_nws_request",
            side_effect=[page_one, TIMEOUT],
        ):
            with pytest.raises(PartialPageReadError) as excinfo:
                await _make_paginated_request("https://x/api/now/table/incident?a=b", max_results=500)
        assert len(excinfo.value.rows) == 250
        assert excinfo.value.error.code == ErrorCode.TIMEOUT

    def test_partial_error_is_not_a_request_error_subclass(self):
        """Otherwise every `except ServiceNowRequestError` arm would eat the rows."""
        assert not issubclass(PartialPageReadError, ServiceNowRequestError)

    @pytest.mark.asyncio
    async def test_every_page_collected_before_the_failure_is_kept(self):
        """Two good pages then a failure keeps 500 rows, not just the last page."""
        page = {"result": _rows(250)}
        with patch(
            "Table_Tools.generic_table_tools.make_nws_request",
            side_effect=[page, page, TIMEOUT],
        ):
            with pytest.raises(PartialPageReadError) as excinfo:
                await _make_paginated_request("https://x/api/now/table/incident?a=b", max_results=600)
        assert len(excinfo.value.rows) == 500


class TestFilteredQueryEnvelopes:
    @pytest.mark.asyncio
    async def test_failure_returns_error_not_no_records_found(self):
        with patch(
            "Table_Tools.generic_table_tools._make_paginated_request", side_effect=TIMEOUT
        ):
            result = await query_table_with_filters("incident", TableFilterParams(filters={"priority": "1"}))
        _assert_plain_failure(result, ErrorCode.TIMEOUT)

    @pytest.mark.asyncio
    async def test_partial_keeps_rows_and_flags_incompleteness(self):
        partial = PartialPageReadError(_rows(250), TIMEOUT)
        with patch(
            "Table_Tools.generic_table_tools._make_paginated_request", side_effect=partial
        ):
            result = await query_table_with_filters(
                "incident", TableFilterParams(filters={"priority": "1"}, max_results=500)
            )
        assert len(result["result"]) == 250
        assert result["returned_count"] == 250
        assert result["partial"] is True
        assert result["error"]["code"] == ErrorCode.TIMEOUT

    @pytest.mark.asyncio
    async def test_successful_query_has_no_partial_key(self):
        with patch("Table_Tools.generic_table_tools._make_paginated_request") as mock_request:
            mock_request.return_value = _rows(3)
            result = await query_table_with_filters("incident", TableFilterParams(filters={"priority": "1"}))
        assert "partial" not in result
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_text_search_failure_returns_error(self):
        with patch(
            "Table_Tools.generic_table_tools._make_paginated_request", side_effect=TIMEOUT
        ):
            result = await query_table_by_text("incident", "database down")
        _assert_plain_failure(result, ErrorCode.TIMEOUT)

    @pytest.mark.asyncio
    async def test_text_search_partial_keeps_rows(self):
        partial = PartialPageReadError(_rows(20), TIMEOUT)
        with patch(
            "Table_Tools.generic_table_tools._make_paginated_request", side_effect=partial
        ):
            result = await query_table_by_text("incident", "database down")
        assert len(result["result"]) == 20
        assert result["partial"] is True
        assert result["error"]["code"] == ErrorCode.TIMEOUT

    @pytest.mark.asyncio
    async def test_priority_query_failure_is_not_the_request_failed_string(self):
        with patch(
            "Table_Tools.generic_table_tools._make_paginated_request", side_effect=TIMEOUT
        ):
            result = await get_records_by_priority("incident", ["1", "2"])
        _assert_plain_failure(result, ErrorCode.TIMEOUT)

    @pytest.mark.asyncio
    async def test_priority_query_partial_keeps_rows(self):
        partial = PartialPageReadError(_rows(30), TIMEOUT)
        with patch(
            "Table_Tools.generic_table_tools._make_paginated_request", side_effect=partial
        ):
            result = await get_records_by_priority("incident", ["1", "2"])
        assert len(result["result"]) == 30
        assert result["partial"] is True

    @pytest.mark.asyncio
    async def test_unexpected_exception_still_maps_to_request_failed(self):
        """Narrowing the except must not remove the catch-all for real bugs."""
        with patch(
            "Table_Tools.generic_table_tools._make_paginated_request",
            side_effect=RuntimeError("boom"),
        ):
            result = await get_records_by_priority("incident", ["1", "2"])
        assert result["error"]["code"] == "INTERNAL"
        assert isinstance(result["error"]["message"], str)


class TestFindSimilarRecords:
    """`except Exception: return CONNECTION_ERROR` must not become a 4th dialect."""

    @pytest.mark.asyncio
    async def test_description_failure_is_not_no_description_found(self):
        with patch("Table_Tools.generic_table_tools.make_nws_request", side_effect=TIMEOUT):
            result = await find_similar_records("incident", "INC0012345")
        _assert_plain_failure(result, ErrorCode.TIMEOUT)

    @pytest.mark.asyncio
    async def test_search_failure_is_not_connection_error_string(self):
        with patch(
            "Table_Tools.generic_table_tools.get_record_description",
            new=AsyncMock(return_value={"result": [{"short_description": "db down"}]}),
        ), patch(
            "Table_Tools.generic_table_tools.query_table_by_text",
            new=AsyncMock(return_value=FORBIDDEN.to_error_dict()),
        ):
            result = await find_similar_records("incident", "INC0012345")
        _assert_plain_failure(result, ErrorCode.FORBIDDEN)

    @pytest.mark.asyncio
    async def test_partial_search_survives_the_original_record_filter(self):
        similar = {
            "result": [{"number": "INC0012345"}, {"number": "INC0099999"}],
            "partial": True,
            **TIMEOUT.to_error_dict(),
        }
        with patch(
            "Table_Tools.generic_table_tools.get_record_description",
            new=AsyncMock(return_value={"result": [{"short_description": "db down"}]}),
        ), patch(
            "Table_Tools.generic_table_tools.query_table_by_text",
            new=AsyncMock(return_value=similar),
        ):
            result = await find_similar_records("incident", "INC0012345")
        assert [r["number"] for r in result["result"]] == ["INC0099999"]
        assert result["partial"] is True
        assert result["error"]["code"] == ErrorCode.TIMEOUT

    @pytest.mark.asyncio
    async def test_genuinely_empty_description_still_says_no_description(self):
        with patch("Table_Tools.generic_table_tools.make_nws_request") as mock_request:
            mock_request.return_value = {"result": []}
            result = await find_similar_records("incident", "INC0099999")
        assert result["result"] == []
        assert "error" not in result



class TestConsumersThatReWrap:
    """A re-wrapper must not relabel a failure as an empty result set."""

    @pytest.mark.asyncio
    async def test_priority_incidents_with_metadata_does_not_report_zero_found(self):
        from Table_Tools.consolidated_tools import get_priority_incidents

        with patch(
            "Table_Tools.consolidated_tools.get_records_by_priority",
            new=AsyncMock(return_value=TIMEOUT.to_error_dict()),
        ):
            result = await get_priority_incidents(["1"], include_metadata=True)
        _assert_plain_failure(result, ErrorCode.TIMEOUT)
        assert "metadata" not in result

    @pytest.mark.asyncio
    async def test_priority_incidents_partial_is_flagged_in_metadata_response(self):
        from Table_Tools.consolidated_tools import get_priority_incidents

        payload = {"result": _rows(4), "partial": True, **TIMEOUT.to_error_dict()}
        with patch(
            "Table_Tools.consolidated_tools.get_records_by_priority",
            new=AsyncMock(return_value=payload),
        ):
            result = await get_priority_incidents(["1"], include_metadata=True)
        assert result["metadata"]["count"] == 4
        assert result["partial"] is True
        assert result["error"]["code"] == ErrorCode.TIMEOUT

    @pytest.mark.asyncio
    async def test_kb_by_state_does_not_report_no_matching_articles(self):
        from Table_Tools.consolidated_tools import get_kb_articles_by_state

        with patch(
            "Table_Tools.consolidated_tools.query_table_with_filters",
            new=AsyncMock(return_value=TIMEOUT.to_error_dict()),
        ):
            result = await get_kb_articles_by_state()
        _assert_plain_failure(result, ErrorCode.TIMEOUT)

    @pytest.mark.asyncio
    async def test_kb_by_state_reports_failure_when_the_filter_empties_a_partial(self):
        """A partial set filtered down to nothing must not answer "no matches".

        Two pages requested, page 1 returns 250 draft articles, page 2 times out.
        Asking for `published` filters all 250 away — but the articles that would
        have matched could be in the page that never arrived, so "No matching KB
        articles." would be a confident answer built from an unfinished read.
        """
        from Table_Tools.consolidated_tools import get_kb_articles_by_state

        page_one = {"result": [
            {"number": f"KB{i:07d}", "sys_id": f"{i:032x}", "workflow_state": "draft"}
            for i in range(250)
        ]}
        with patch(
            "Table_Tools.generic_table_tools.make_nws_request",
            side_effect=[page_one, TIMEOUT],
        ):
            result = await get_kb_articles_by_state(workflow_state="published", max_results=500)
        _assert_plain_failure(result, ErrorCode.TIMEOUT)
        assert "message" not in result

    @pytest.mark.asyncio
    async def test_kb_by_state_genuine_empty_still_says_no_matching_articles(self):
        """The complete-read case is untouched: empty stays not-found."""
        from Table_Tools.consolidated_tools import get_kb_articles_by_state

        with patch("Table_Tools.generic_table_tools.make_nws_request") as mock_request:
            mock_request.return_value = {"result": []}
            result = await get_kb_articles_by_state(workflow_state="published")
        assert result["result"] == []
        assert result["returned_count"] == 0
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_find_similar_reports_failure_when_the_only_match_was_the_original(self):
        """Same invariant on the similar-records filter."""
        similar = {
            "result": [{"number": "INC0012345"}],
            "partial": True,
            **TIMEOUT.to_error_dict(),
        }
        with patch(
            "Table_Tools.generic_table_tools.get_record_description",
            new=AsyncMock(return_value={"result": [{"short_description": "db down"}]}),
        ), patch(
            "Table_Tools.generic_table_tools.query_table_by_text",
            new=AsyncMock(return_value=similar),
        ):
            result = await find_similar_records("incident", "INC0012345")
        _assert_plain_failure(result, ErrorCode.TIMEOUT)

    # v5.0 "Boron" (Tier 2): the intelligent_search re-wrap tests were removed
    # with the tool; its query_table_intelligently engine is deleted in the
    # Tier 2.5 sweep.


class TestEndToEndThroughTheRealDispatcher:
    """Failures reach the wrappers through the real dispatcher.

    These exercise the real `make_nws_request` rather than the module seam. That
    was originally the only way to catch a typo in the `_TYPED_CALLERS` opt-in
    list; with the shim gone the list is gone too, and what these now prove is
    the property that outlived it — a real classified failure, produced by the
    real dispatcher, is handled by this module rather than escaping it.

    Still not replaceable by the source scan in `test_http_layer_errors.py`: that
    checks a handler EXISTS, these check it does the right thing.
    """

    @pytest.mark.asyncio
    async def test_timeout_reaches_search_records_as_a_timeout(self, monkeypatch):
        import http_layer.request_dispatcher as dispatcher
        from Table_Tools.generic_tool_wrappers import search_records

        async def slow(url):
            raise TimeoutError()

        monkeypatch.setattr(dispatcher, "make_oauth_request", slow)
        result = await search_records("incident", "database down")
        _assert_plain_failure(result, ErrorCode.TIMEOUT)

    @pytest.mark.asyncio
    async def test_timeout_reaches_get_record_as_a_timeout(self, monkeypatch):
        import http_layer.request_dispatcher as dispatcher
        from Table_Tools.generic_tool_wrappers import get_record

        async def slow(url):
            raise TimeoutError()

        monkeypatch.setattr(dispatcher, "make_oauth_request", slow)
        result = await get_record("incident", "INC0012345")
        _assert_plain_failure(result, ErrorCode.TIMEOUT)

    @pytest.mark.asyncio
    async def test_empty_result_through_the_real_dispatcher_is_not_found(self, monkeypatch):
        import http_layer.request_dispatcher as dispatcher
        from Table_Tools.generic_tool_wrappers import get_record

        async def empty(url):
            return {"result": []}

        monkeypatch.setattr(dispatcher, "make_oauth_request", empty)
        result = await get_record("incident", "INC0099999")
        assert result == {"record": None}
        assert "error" not in result
