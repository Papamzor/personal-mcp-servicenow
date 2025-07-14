from mcp.server.fastmcp import FastMCP
from service_now_api import make_nws_request, NWS_API_BASE
from utils import getKeywords

mcp = FastMCP("mcpnowsimilarity", version="1.0.0", description="MCP Now Similarity Service")

@mcp.tool()
async def nowtest():
    """Test function to verify mcp is running."""
    return "Server is running and ready to handle requests!"

@mcp.tool()
async def nowtestauth():
    """Test function to verify nowauth is running with authentication."""
    url = f"{NWS_API_BASE}/api/x_146833_awesomevi/test"
    data = await make_nws_request(url)
    if not data:
        return "Unable to fetch alerts or no alerts found."
    return data

@mcp.tool()
async def nowtestauthInput(tableName: str):
    """Get ServiceNow table description for a given table."""
    url = f"{NWS_API_BASE}/api/x_146833_awesomevi/test/{tableName}"
    data = await make_nws_request(url)
    if not data:
        return "Unable to fetch alerts or no alerts found."
    return data

@mcp.tool()
async def similarincidentsfortext(inputText: str):
    """Get incidents based on input text."""
    keywords = getKeywords(inputText)
    for keyword in keywords:
        url = f"{NWS_API_BASE}/api/now/table/incident?sysparm_fields=number,short_description&sysparm_query=short_descriptionCONTAINS{keyword}"
        data = await make_nws_request(url)
        if data:
            return data
    return "Unable to fetch alerts or no alerts found."

@mcp.tool()
async def getshortdescforincident(inputincident: str):
    """Get short_description for a given incident based on input incident number."""
    keywords = getKeywords(inputincident)
    for keyword in keywords:
        url = f"{NWS_API_BASE}/api/now/table/incident?sysparm_fields=short_description&sysparm_query=number={inputincident}"
        data = await make_nws_request(url)
        if data:
            return data
    return "Unable to fetch alerts or no alerts found."

@mcp.tool()
async def similarincidentsforincident(inputincident: str):
    """Get similar incidents based on given incident."""
    inputText = await getshortdescforincident(inputincident)
    return await similarincidentsfortext(inputText)
