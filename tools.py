
from mcp.server.fastmcp import FastMCP
from incident_tools import similarincidentsfortext, getshortdescforincident, similarincidentsforincident, getincidentdetails
from change_tools import similarchangesfortext, getshortdescforchange, similarchangeforchange, getchangedetails
from ur_tools import similarURfortext, getshortdescforUR, similarURforUR, getURdetails
from table_tools import nowtestauth, nowtestauthInput
from utility_tools import nowtest

mcp = FastMCP("personalmcpservicenow", version="1.0.0", description="MCP ServiceNow Service")

# Register all tools with the MCP server
mcp.tool()(nowtest)
mcp.tool()(nowtestauth)
mcp.tool()(nowtestauthInput)
# Universal Request tools
mcp.tool()(similarURfortext)
mcp.tool()(getshortdescforUR)
mcp.tool()(similarURforUR)
mcp.tool()(getURdetails)
# Incident tools
mcp.tool()(similarincidentsfortext)
mcp.tool()(getshortdescforincident)
mcp.tool()(similarincidentsforincident)
mcp.tool()(getincidentdetails)
# Change tools
mcp.tool()(similarchangesfortext)
mcp.tool()(getshortdescforchange)
mcp.tool()(similarchangeforchange)
mcp.tool()(getchangedetails)