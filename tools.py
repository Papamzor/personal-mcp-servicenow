
from mcp.server.fastmcp import FastMCP
from Table_Tools.incident_tools import similarincidentsfortext, getshortdescforincident, similarincidentsforincident, getincidentdetails
from Table_Tools.change_tools import similarchangesfortext, getshortdescforchange, similarchangesforchange, getchangedetails
from Table_Tools.ur_tools import similarURfortext, getshortdescforUR, similarURsforUR, getURdetails
from Table_Tools.kb_tools import similar_knowledge_for_text, get_knowledge_details
from Table_Tools.table_tools import nowtestauth, nowtestauthInput
from utility_tools import nowtest

mcp = FastMCP("personalmcpservicenow", version="1.0.0", description="MCP ServiceNow Service")

# Register all tools with the MCP server
mcp.tool()(nowtest)
mcp.tool()(nowtestauth)
mcp.tool()(nowtestauthInput)
# Universal Request tools
mcp.tool()(similarURfortext)
mcp.tool()(getshortdescforUR)
mcp.tool()(similarURsforUR)
mcp.tool()(getURdetails)
# Incident tools
mcp.tool()(similarincidentsfortext)
mcp.tool()(getshortdescforincident)
mcp.tool()(similarincidentsforincident)
mcp.tool()(getincidentdetails)
# Change tools
mcp.tool()(similarchangesfortext)
mcp.tool()(getshortdescforchange)
mcp.tool()(similarchangesforchange)
mcp.tool()(getchangedetails)
# Knowledge Base tools
mcp.tool()(similar_knowledge_for_text)
mcp.tool()(get_knowledge_details)