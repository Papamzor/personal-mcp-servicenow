
from mcp.server.fastmcp import FastMCP
from incident_tools import similarincidentsfortext, getshortdescforincident, similarincidentsforincident, getincidentdetails
from change_tools import changesfortext, getshortdescforchange, similarchangefortext, getchangedetails
from table_tools import nowtestauth, nowtestauthInput
from utility_tools import nowtest

mcp = FastMCP("mcpnowsimilarity", version="1.0.0", description="MCP Now Similarity Service")

# Register all tools with the MCP server
mcp.tool()(nowtest)
mcp.tool()(nowtestauth)
mcp.tool()(nowtestauthInput)
mcp.tool()(similarincidentsfortext)
mcp.tool()(getshortdescforincident)
mcp.tool()(similarincidentsforincident)
mcp.tool()(changesfortext)
mcp.tool()(getshortdescforchange)
mcp.tool()(similarchangefortext)
mcp.tool()(getincidentdetails)
mcp.tool()(getchangedetails)