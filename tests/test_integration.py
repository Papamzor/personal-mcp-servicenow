"""End-to-end integration tests that exercise real product code paths.

These tests mock only the outermost network boundary (httpx via
oauth_client / make_oauth_request) and let every wrapper, validator,
filter applicator, query builder, and response shaper run as it would
in production. They are the safety net for cross-module wiring that
unit tests miss because each unit mocks its dependencies.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import httpx


pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Module / tool registry smoke tests
# ---------------------------------------------------------------------------

class TestModuleImports:
    """Catch import-time errors and circular imports across the codebase."""

    def test_tools_module_imports(self):
        import tools
        assert tools.mcp is not None

    def test_all_table_tools_modules_import(self):
        from Table_Tools import (
            generic_table_tools,
            generic_tool_wrappers,
            consolidated_tools,
            cmdb_tools,
            vtb_task_tools,
            intelligent_query_tools,
            date_utils,
        )
        assert generic_table_tools is not None
        assert generic_tool_wrappers is not None
        assert consolidated_tools is not None
        assert cmdb_tools is not None
        assert vtb_task_tools is not None
        assert intelligent_query_tools is not None
        assert date_utils is not None

    def test_core_modules_import(self):
        import http_layer
        import oauth
        import filter
        import config_loader
        import constants
        assert http_layer.make_nws_request is not None
        assert oauth.ServiceNowOAuthClient is not None


class TestToolRegistry:
    """Tools.py is the MCP entrypoint — registration must stay coherent."""

    def test_expected_tool_count(self):
        import tools
        # v5.0 "Boron" (Tier 2 cull): 39 -> 25.
        # (1 health_check + 4 generic + 1 priority + 1 KB state read +
        #  2 vtb CRUD + 5 KB write + 4 SLA + 6 CMDB + 1 query-syntax help).
        assert len(tools.tools) == 25, (
            f"Expected 25 registered tools, got {len(tools.tools)}. "
            "If tool count changed intentionally, update this test and CLAUDE.md."
        )

    def test_critical_tools_registered(self):
        import tools
        names = {fn.__name__ for fn in tools.tools}
        # A representative subset covering each tool category
        expected = {
            "search_records", "get_record", "find_similar", "filter_records",
            "create_private_task", "update_private_task",
            "get_priority_incidents",
            "get_kb_articles_by_state",
            "find_cis_by_type", "get_ci_details",
            "health_check",
            "get_query_syntax_help",
            # v4.0 SLA consolidation (v5.0 dropped similar_slas_for_text)
            "get_sla_details",
            "query_slas_by_task", "query_slas_by_status", "query_slas_custom",
        }
        missing = expected - names
        assert not missing, f"Missing tools in registry: {missing}"


# ---------------------------------------------------------------------------
# Read pipeline end-to-end
# ---------------------------------------------------------------------------

class TestReadPipelineEndToEnd:
    """search_records → query_table_by_text → make_nws_request → make_oauth_request."""

    @pytest.mark.asyncio
    async def test_search_records_builds_encoded_query_and_perf_params(self):
        from Table_Tools.generic_tool_wrappers import search_records

        captured = {}

        async def fake_oauth_request(url):
            captured["url"] = url
            return {"result": [{"number": "INC0001", "short_description": "server down"}]}

        with patch("http_layer.request_dispatcher.make_oauth_request", new=fake_oauth_request):
            result = await search_records("incident", "server down")

        assert result["result"][0]["number"] == "INC0001"

        url = captured["url"]
        # Performance params injected by make_nws_request
        assert "sysparm_no_count=true" in url
        assert "sysparm_exclude_reference_link=true" in url
        # Deterministic sort order injected by paginated request
        assert "ORDERBYDESCsys_created_on" in url
        # Spaces in keywords URL-encoded
        assert "server" in url

    @pytest.mark.asyncio
    async def test_search_records_rejects_unknown_table(self):
        from Table_Tools.generic_tool_wrappers import search_records

        result = await search_records("not_a_real_table", "anything")

        assert "error" in result
        assert "Invalid table" in result["error"]

    @staticmethod
    def _sysparm_query(url: str) -> str:
        """The decoded sysparm_query value from a captured request URL."""
        from urllib.parse import parse_qs, unquote, urlsplit

        raw = parse_qs(urlsplit(url).query).get("sysparm_query", [""])[0]
        return unquote(raw)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("table,filters,expected_query", [
        ("sc_req_item", {"state": "1"}, "state=1"),
        ("incident", {"priority": "1"}, "priority=1"),
    ])
    async def test_query_is_exactly_the_caller_conditions(self, table, filters, expected_query):
        """The outbound query equals the caller's conditions — nothing appended.

        Domain filtering was deleted in v4.4. Asserting *equality* rather than
        the absence of specific substrings is deliberate: a substring check only
        catches a re-introduction that reuses the old field names, while this
        fails on any appended condition whatsoever, under any field or operator.
        The trailing ORDERBYDESC is the pagination sort, not a filter.
        """
        from Table_Tools.generic_tool_wrappers import filter_records

        captured = {}

        async def fake_oauth_request(url):
            captured["url"] = url
            return {"result": []}

        with patch("http_layer.request_dispatcher.make_oauth_request", new=fake_oauth_request):
            await filter_records(table, filters)

        query = self._sysparm_query(captured["url"])
        conditions = query.split("^ORDERBY")[0]
        assert conditions == expected_query

    @pytest.mark.asyncio
    async def test_every_returned_row_reaches_the_caller(self):
        """Nothing is dropped after the response comes back.

        The URL assertions above cannot see a post-response exclusion — a
        re-introduction that filtered `all_results` in Python would leave the
        request untouched and pass every query-shape check. Rows whose category
        and catalog match the old exclusion lists are returned here, so any
        such filter shows up as a missing row.
        """
        from Table_Tools.generic_tool_wrappers import filter_records

        rows = [
            {"number": "RITM0001", "category": "Payroll",
             "cat_item.sc_catalogs.title": "People_Pay"},
            {"number": "RITM0002", "category": "People Support",
             "assignment_group": "Payroll Managers"},
            {"number": "RITM0003", "category": "Workplace"},
            {"number": "RITM0004", "category": "Network"},
        ]

        async def fake_oauth_request(url):
            return {"result": rows}

        with patch("http_layer.request_dispatcher.make_oauth_request", new=fake_oauth_request):
            result = await filter_records("sc_req_item", {"state": "1"})

        returned = [row["number"] for row in result["result"]]
        assert returned == ["RITM0001", "RITM0002", "RITM0003", "RITM0004"]
        assert result["returned_count"] == 4


# ---------------------------------------------------------------------------
# Write pipeline end-to-end
# ---------------------------------------------------------------------------

class TestWritePipelineEndToEnd:
    """create_private_task → make_nws_request(method=POST) → oauth_client (raise_for_status=True)."""

    @pytest.mark.asyncio
    async def test_create_private_task_routes_through_unified_pipeline(self):
        from Table_Tools.vtb_task_tools import create_private_task

        with patch("http_layer.request_dispatcher.get_oauth_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.make_authenticated_request = AsyncMock(
                return_value={"result": {"number": "VTB0001234"}}
            )
            mock_get_client.return_value = mock_client

            result = await create_private_task({"short_description": "Integration test"})

        assert result == {"number": "VTB0001234"}
        # Confirm the write was delegated to oauth_client with raise_for_status=True
        call = mock_client.make_authenticated_request.call_args
        assert call.args[0] == "POST"
        assert call.kwargs["raise_for_status"] is True
        assert call.kwargs["json"]["short_description"] == "Integration test"

    @pytest.mark.asyncio
    async def test_update_private_task_resolves_sys_id_then_patches(self):
        from Table_Tools.vtb_task_tools import update_private_task

        # Sequence: GET (sys_id lookup) -> PATCH (update)
        async def fake_oauth_get(url):
            assert "sysparm_query=number=VTB0001234" in url
            return {"result": [{"sys_id": "abc123"}]}

        with patch("http_layer.request_dispatcher.make_oauth_request", new=fake_oauth_get), \
             patch("http_layer.request_dispatcher.get_oauth_client") as mock_get_client:

            mock_client = MagicMock()
            mock_client.make_authenticated_request = AsyncMock(
                return_value={"result": {"number": "VTB0001234", "state": "3"}}
            )
            mock_get_client.return_value = mock_client

            result = await update_private_task("VTB0001234", {"state": "3"})

        assert result == {"number": "VTB0001234", "state": "3"}
        call = mock_client.make_authenticated_request.call_args
        assert call.args[0] == "PATCH"
        assert "abc123" in call.args[1]  # sys_id reached the PATCH URL


# ---------------------------------------------------------------------------
# Error propagation end-to-end
# ---------------------------------------------------------------------------

class TestErrorPropagationEndToEnd:
    """HTTPStatusError raised at the OAuth boundary surfaces as a domain error string."""

    @pytest.mark.parametrize("status_code,fragment", [
        (401, "Authentication failed"),
        (403, "Access denied"),
        (400, "Invalid request"),
        (404, "not found"),
        (500, "server error"),
    ])
    @pytest.mark.asyncio
    async def test_create_private_task_maps_http_status_to_error_message(
        self, status_code, fragment
    ):
        from Table_Tools.vtb_task_tools import create_private_task

        response = MagicMock()
        response.status_code = status_code
        error = httpx.HTTPStatusError(str(status_code), request=MagicMock(), response=response)

        with patch("http_layer.request_dispatcher.get_oauth_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.make_authenticated_request = AsyncMock(side_effect=error)
            mock_get_client.return_value = mock_client

            result = await create_private_task({"short_description": "boom"})

        assert isinstance(result, str)
        assert fragment.lower() in result.lower()
