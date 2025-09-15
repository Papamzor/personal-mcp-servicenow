# Output MCP Server Start confirmation in stderr for Claude Desktop or CLI
import sys
print("Personal ServiceNow MCP Server started.", file=sys.stderr)

from mcp.server.fastmcp import FastMCP
from Table_Tools.consolidated_tools import (
    # Incident tools
    similar_incidents_for_text, get_short_desc_for_incident, similar_incidents_for_incident, 
    get_incident_details, get_incidents_by_filter, get_priority_incidents,
    # Change tools  
    similar_changes_for_text, get_short_desc_for_change, similar_changes_for_change, get_change_details,
    # Request Item tools
    similar_request_items_for_text, get_short_desc_for_request_item, similar_request_items_for_request_item, get_request_item_details,
    # Knowledge tools
    similar_knowledge_for_text, get_knowledge_details, get_knowledge_by_category, get_active_knowledge_articles,
    # Private Task tools (basic operations)
    similar_private_tasks_for_text, get_short_desc_for_private_task, similar_private_tasks_for_private_task, get_private_task_details,
    get_private_tasks_by_filter
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

# Register optimized tools - consolidated from 25+ individual table tools to generic approach
tools = [
    # Server & Authentication tools
    nowtest, now_test_oauth, now_auth_info, nowtestauth, nowtest_auth_input,
    
    # Incident tools (using generic functions)
    similar_incidents_for_text, get_short_desc_for_incident, similar_incidents_for_incident, 
    get_incident_details, get_incidents_by_filter, get_priority_incidents,
    
    # Change tools (using generic functions)
    similar_changes_for_text, get_short_desc_for_change, similar_changes_for_change, get_change_details,
    
    # Request Item tools (using generic functions)
    similar_request_items_for_text, get_short_desc_for_request_item, similar_request_items_for_request_item, get_request_item_details,
    
    # Knowledge Base tools (using generic functions)
    similar_knowledge_for_text, get_knowledge_details, get_knowledge_by_category, get_active_knowledge_articles,
    
    # Private Task tools (using generic functions + CRUD operations)
    similar_private_tasks_for_text, get_short_desc_for_private_task, similar_private_tasks_for_private_task, 
    get_private_task_details, get_private_tasks_by_filter, create_private_task, update_private_task,
    
    # CMDB tools (specialized, kept separate due to unique requirements)
    find_cis_by_type, search_cis_by_attributes, get_ci_details, similar_cis_for_ci, get_all_ci_types, quick_ci_search,
    
    # Intelligent query tools
    intelligent_search, explain_servicenow_filters, build_smart_servicenow_filter,
    get_servicenow_filter_templates, get_query_examples
]

for tool in tools:
    mcp.tool()(tool)

if __name__ == "__main__":
    mcp.run()
