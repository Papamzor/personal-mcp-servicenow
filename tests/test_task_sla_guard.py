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


def _sysparm_conditions(url):
    """The caller's conditions from a captured URL, sort clause removed.

    Splitting the raw URL on "^OR" also splits "^ORDERBYDESC", so the sort is
    stripped before the conditions are separated.
    """
    from urllib.parse import parse_qs, unquote, urlsplit

    raw = parse_qs(urlsplit(url).query).get("sysparm_query", [""])[0]
    query = unquote(raw).split("^ORDERBY")[0]
    return [part for part in query.replace("^OR", "^").split("^") if part]


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
        """A bare short_description condition is the silently-dropped filter.

        Splitting on the literal "^OR" would also split "^ORDERBYDESC" (the
        pagination sort) and depends on no param name containing "LIKE", so the
        conditions are isolated properly first: take the sysparm_query value,
        drop the sort clause, then split.
        """
        capture = _Capture()
        with patch("http_layer.request_dispatcher.make_oauth_request", new=capture):
            await similar_slas_for_text("network outage")

        conditions = _sysparm_conditions(capture.urls[0])
        like_conditions = [c for c in conditions if "LIKE" in c]
        assert like_conditions, f"no LIKE condition found in {conditions!r}"
        for condition in like_conditions:
            assert condition.startswith("task.short_description"), condition


class TestIntelligentSearchPath:
    """The same bug reached task_sla through the NL query tools.

    `query_table_intelligently` falls back to a keyword search, and the NL
    parser's own fallback built `{"short_description": "LIKE..."}` for any
    table. On task_sla that condition is silently dropped, so
    intelligent_search(query=..., table="task_sla") returned an arbitrary page
    of SLAs with confidence 0.5 and an explanation claiming a keyword match.
    """

    def test_nl_keyword_fallback_uses_the_table_search_field(self):
        from filter.intelligence import QueryIntelligence

        incident = QueryIntelligence._build_keyword_fallback("server down", "incident")
        sla = QueryIntelligence._build_keyword_fallback("server down", "task_sla")

        assert "short_description" in incident["filters"]
        assert "task.short_description" in sla["filters"]
        assert "short_description" not in sla["filters"]

    def test_parse_natural_language_threads_the_table_through(self):
        from filter.intelligence import QueryIntelligence

        parsed = QueryIntelligence.parse_natural_language("server down", "task_sla")

        bare = [f for f in parsed["filters"] if f == "short_description"]
        assert not bare, f"bare short_description filter on task_sla: {parsed['filters']}"

    @pytest.mark.asyncio
    async def test_query_table_by_text_resolves_the_field_from_the_table(self):
        """A caller that forgets search_field must still get a valid query."""
        from Table_Tools.generic_table_tools import query_table_by_text

        capture = _Capture()
        with patch("http_layer.request_dispatcher.make_oauth_request", new=capture):
            await query_table_by_text("task_sla", "network outage")

        conditions = _sysparm_conditions(capture.urls[0])
        for condition in (c for c in conditions if "LIKE" in c):
            assert condition.startswith("task.short_description"), condition

    @pytest.mark.asyncio
    async def test_other_tables_keep_the_default_field(self):
        from Table_Tools.generic_table_tools import query_table_by_text

        capture = _Capture()
        with patch("http_layer.request_dispatcher.make_oauth_request", new=capture):
            await query_table_by_text("incident", "network outage")

        conditions = _sysparm_conditions(capture.urls[0])
        for condition in (c for c in conditions if "LIKE" in c):
            assert condition.startswith("short_description"), condition
