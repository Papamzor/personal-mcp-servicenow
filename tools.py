from mcp.server.fastmcp import FastMCP
from Table_Tools.consolidated_tools import (
    # Incident tools
    similar_incidents_for_text, get_short_desc_for_incident, similar_incidents_for_incident, 
    get_incident_details, get_incidents_by_filter,
    # Change tools  
    similar_changes_for_text, get_short_desc_for_change, similar_changes_for_change, get_change_details,
    # UR tools
    similar_ur_for_text, get_short_desc_for_ur, similar_urs_for_ur, get_ur_details,
    # Knowledge tools
    similar_knowledge_for_text, get_knowledge_details, get_knowledge_by_category, get_active_knowledge_articles,
    # Private Task tools (vtb_task table)
    similar_private_tasks_for_text, get_short_desc_for_private_task, similar_private_tasks_for_private_task, get_private_task_details,
    create_private_task, update_private_task, get_private_tasks_by_filter,
    # Table tools
    nowtestauth, nowtest_auth_input,
    # CMDB tools
    find_cis_by_type, search_cis_by_attributes, get_ci_details, similar_cis_for_ci, get_all_ci_types, quick_ci_search
)
from utility_tools import nowtest, nowtestoauth, nowauthinfo

mcp = FastMCP("personalmcpservicenow")

# Register optimized tools
tools = [
    nowtest, nowtestoauth, nowauthinfo, nowtestauth, nowtest_auth_input,
    similar_ur_for_text, get_short_desc_for_ur, similar_urs_for_ur, get_ur_details,
    similar_incidents_for_text, get_short_desc_for_incident, similar_incidents_for_incident, 
    get_incident_details, get_incidents_by_filter,
    similar_changes_for_text, get_short_desc_for_change, similar_changes_for_change, get_change_details,
    similar_knowledge_for_text, get_knowledge_by_category, get_active_knowledge_articles, get_knowledge_details,
    similar_private_tasks_for_text, get_short_desc_for_private_task, similar_private_tasks_for_private_task, get_private_task_details,
    create_private_task, update_private_task, get_private_tasks_by_filter,
    # CMDB tools
    find_cis_by_type, search_cis_by_attributes, get_ci_details, similar_cis_for_ci, get_all_ci_types, quick_ci_search
]

for tool in tools:
    mcp.tool()(tool)