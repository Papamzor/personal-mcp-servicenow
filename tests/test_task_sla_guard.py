"""task_sla guards on the generic tools (v4.4 Tier 0.5).

`task_sla` has no `number` column (its number_prefix is None) and no
`short_description` of its own. The four number/text-addressed generic tools
advertised it anyway, and ServiceNow **silently drops** a condition on a field
a table does not have — so those calls returned HTTP 200 with an arbitrary page
of SLA rows rather than failing. That is the exact shape of the historic
1.2M-token `get_sla_details` bug.

These tests pin three things:
  1. the four tools refuse task_sla before issuing any request,
  2. `filter_records` still accepts it (the caller names the fields there),
  3. `similar_slas_for_text` searches the dot-walked `task.short_description`.
"""
from unittest.mock import patch

import pytest

from Table_Tools.consolidated_tools import similar_slas_for_text
from Table_Tools.generic_tool_wrappers import (
    filter_records,
    find_similar,
    get_record,
    get_record_summary,
    search_records,
)


class _Capture:
    def __init__(self, payload=None):
        self.urls = []
        self.payload = payload if payload is not None else {"result": []}

    async def __call__(self, url, *args, **kwargs):
        self.urls.append(url)
        return self.payload


class TestIdentityToolsRejectTaskSla:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("call", [
        lambda: search_records("task_sla", "network outage"),
        lambda: get_record_summary("task_sla", "SLA0001"),
        lambda: get_record("task_sla", "SLA0001"),
        lambda: find_similar("task_sla", "SLA0001"),
    ])
    async def test_refused_without_issuing_a_request(self, call):
        capture = _Capture()
        with patch("http_layer.request_dispatcher.make_oauth_request", new=capture):
            result = await call()

        assert "error" in result
        assert "task_sla" in result["error"]
        assert capture.urls == [], "must refuse before touching ServiceNow"

    @pytest.mark.asyncio
    async def test_error_names_the_working_alternatives(self):
        """A refusal that does not say what to use instead just moves the dead end."""
        result = await get_record("task_sla", "SLA0001")

        message = result["error"]
        assert "get_sla_details" in message
        assert "query_slas_by_task" in message
        assert "filter_records" in message

    @pytest.mark.asyncio
    async def test_other_tables_are_unaffected(self):
        capture = _Capture(payload={"result": [{"number": "INC0001"}]})
        with patch("http_layer.request_dispatcher.make_oauth_request", new=capture):
            result = await get_record("incident", "INC0001")

        assert "error" not in result
        assert len(capture.urls) == 1

    @pytest.mark.asyncio
    async def test_unknown_table_still_reports_invalid_table(self):
        """The identity guard must not mask the plain unsupported-table error."""
        result = await get_record("not_a_real_table", "X0001")

        assert "Invalid table" in result["error"]


class TestFilterRecordsStillAcceptsTaskSla:
    @pytest.mark.asyncio
    async def test_caller_named_fields_are_allowed(self):
        """filter_records assumes no field names, so task_sla stays supported."""
        capture = _Capture()
        with patch("http_layer.request_dispatcher.make_oauth_request", new=capture):
            result = await filter_records("task_sla", {"active": "true"})

        assert "error" not in result
        assert len(capture.urls) == 1
        assert "active=true" in capture.urls[0]


class TestSimilarSlasForTextSearchField:
    @pytest.mark.asyncio
    async def test_query_uses_dot_walked_task_description(self):
        capture = _Capture()
        with patch("http_layer.request_dispatcher.make_oauth_request", new=capture):
            await similar_slas_for_text("network outage")

        url = capture.urls[0]
        assert "task.short_descriptionLIKE" in url

    @pytest.mark.asyncio
    async def test_bare_short_description_never_appears(self):
        """A bare short_description condition is the silently-dropped filter."""
        capture = _Capture()
        with patch("http_layer.request_dispatcher.make_oauth_request", new=capture):
            await similar_slas_for_text("network outage")

        query = capture.urls[0].split("sysparm_query=")[1]
        # Every LIKE condition must be dot-walked; none may target the
        # non-existent task_sla.short_description column directly.
        for condition in query.split("^OR"):
            if "LIKE" in condition:
                assert condition.startswith("task.short_description"), condition
