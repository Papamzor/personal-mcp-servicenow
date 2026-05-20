# Output MCP Server Start confirmation in stderr for Claude Desktop or CLI
import sys
print("Personal ServiceNow MCP Server started.", file=sys.stderr)

from mcp.server.fastmcp import FastMCP
from Table_Tools.generic_tool_wrappers import (
    search_records, get_record_summary, get_record, find_similar, filter_records
)
from Table_Tools.consolidated_tools import (
    # Priority incidents (unique date logic)
    get_priority_incidents,
    # Knowledge-specific tools
    similar_knowledge_for_text, get_knowledge_by_category, get_active_knowledge_articles,
    # SLA tools (v4.0: 10 -> 5 consolidated)
    similar_slas_for_text, get_sla_details,
    query_slas_by_task, query_slas_by_status, query_slas_custom,
)
from Table_Tools.table_tools import nowtestauth, nowtest_auth_input
from Table_Tools.vtb_task_tools import create_private_task, update_private_task
from Table_Tools.cmdb_tools import (
    find_cis_by_type, search_cis_by_attributes, get_ci_details, similar_cis_for_ci, get_all_ci_types, quick_ci_search
)
from utility_tools import nowtest, now_test_oauth, now_auth_info
from Table_Tools.intelligent_query_tools import (
    intelligent_search, explain_servicenow_filters, build_smart_servicenow_filter,
    get_servicenow_filter_templates, get_query_examples
)

mcp = FastMCP("personalmcpservicenow")

# Register tools — consolidated from 55 -> 37 (v3.0) -> 32 (v4.0)
tools = [
    # Server & Authentication tools
    nowtest, now_test_oauth, now_auth_info, nowtestauth, nowtest_auth_input,

    # Generic table tools (replace 24 table-specific wrappers)
    search_records, get_record_summary, get_record, find_similar, filter_records,

    # Priority incidents (unique date logic)
    get_priority_incidents,

    # Knowledge-specific tools (unique params)
    similar_knowledge_for_text, get_knowledge_by_category, get_active_knowledge_articles,

    # Private Task CRUD
    create_private_task, update_private_task,

    # SLA tools (v4.0: 10 -> 5 consolidated; presets exposed via query_slas_by_status)
    similar_slas_for_text, get_sla_details,
    query_slas_by_task, query_slas_by_status, query_slas_custom,

    # CMDB tools
    find_cis_by_type, search_cis_by_attributes, get_ci_details, similar_cis_for_ci, get_all_ci_types, quick_ci_search,

    # Intelligent query tools
    intelligent_search, explain_servicenow_filters, build_smart_servicenow_filter,
    get_servicenow_filter_templates, get_query_examples
]

for tool in tools:
    mcp.tool()(tool)

if __name__ == "__main__":
    mcp.run()
