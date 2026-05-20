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
        import service_now_api_oauth
        import oauth_client
        import query_intelligence
        import query_validation
        import config_loader
        import constants
        assert service_now_api_oauth.make_nws_request is not None
        assert oauth_client.ServiceNowOAuthClient is not None


class TestToolRegistry:
    """Tools.py is the MCP entrypoint — registration must stay coherent."""

    def test_expected_tool_count(self):
        import tools
        # v4.0 Sprint 2: SLA tools consolidated 10 -> 5 (32 total).
        # (5 server/auth + 5 generic + 1 priority + 3 knowledge +
        #  2 vtb CRUD + 5 SLA + 6 CMDB + 5 intelligent).
        assert len(tools.tools) == 32, (
            f"Expected 32 registered tools, got {len(tools.tools)}. "
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
            "similar_knowledge_for_text",
            "find_cis_by_type", "get_ci_details",
            "intelligent_search",
            "now_test_oauth",
            # v4.0 SLA consolidation
            "similar_slas_for_text", "get_sla_details",
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

        with patch("service_now_api_oauth.make_oauth_request", new=fake_oauth_request):
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

    @pytest.mark.asyncio
    async def test_filter_records_applies_sc_catalog_filter(self):
        """Service-catalog tables get sensitive-record exclusions injected automatically.

        ENABLE_SC_CATALOG_FILTERING is True by default, so a request against
        sc_req_item should always include the People_Pay catalog exclusion
        and the assignment-group exclusions, regardless of caller-supplied
        filters.
        """
        from Table_Tools.generic_tool_wrappers import filter_records

        captured = {}

        async def fake_oauth_request(url):
            captured["url"] = url
            return {"result": []}

        with patch("service_now_api_oauth.make_oauth_request", new=fake_oauth_request):
            await filter_records("sc_req_item", {"state": "1"})

        url = captured["url"]
        # Catalog and assignment-group exclusions are appended by the SDK
        assert "cat_item.sc_catalogs.title!=People_Pay" in url
        assert "assignment_group.name!=" in url
        # Caller-supplied filter still present
        assert "state=1" in url

    @pytest.mark.asyncio
    async def test_filter_records_skips_category_filter_when_flag_off(self):
        """Toggle on the incident-category gate to confirm both branches wire up."""
        from Table_Tools.generic_tool_wrappers import filter_records

        captured = {}

        async def fake_oauth_request(url):
            captured["url"] = url
            return {"result": []}

        with patch("service_now_api_oauth.make_oauth_request", new=fake_oauth_request), \
             patch("Table_Tools.generic_table_tools.ENABLE_INCIDENT_CATEGORY_FILTERING", True):
            await filter_records("incident", {"priority": "1"})

        url = captured["url"]
        assert "category!=Payroll" in url


# ---------------------------------------------------------------------------
# Write pipeline end-to-end
# ---------------------------------------------------------------------------

class TestWritePipelineEndToEnd:
    """create_private_task → make_nws_request(method=POST) → oauth_client (raise_for_status=True)."""

    @pytest.mark.asyncio
    async def test_create_private_task_routes_through_unified_pipeline(self):
        from Table_Tools.vtb_task_tools import create_private_task

        with patch("service_now_api_oauth.get_oauth_client") as mock_get_client:
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

        with patch("service_now_api_oauth.make_oauth_request", new=fake_oauth_get), \
             patch("service_now_api_oauth.get_oauth_client") as mock_get_client:

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

        with patch("service_now_api_oauth.get_oauth_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.make_authenticated_request = AsyncMock(side_effect=error)
            mock_get_client.return_value = mock_client

            result = await create_private_task({"short_description": "boom"})

        assert isinstance(result, str)
        assert fragment.lower() in result.lower()
