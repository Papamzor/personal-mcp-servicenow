from mcp.server.fastmcp import FastMCP
from Table_Tools.consolidated_tools import (
    # Incident tools
    similarincidentsfortext, getshortdescforincident, similarincidentsforincident, 
    getincidentdetails, getIncidentsByFilter,
    # Change tools  
    similarchangesfortext, getshortdescforchange, similarchangesforchange, getchangedetails,
    # UR tools
    similarURfortext, getshortdescforUR, similarURsforUR, getURdetails,
    # Knowledge tools
    similar_knowledge_for_text, get_knowledge_details, get_knowledge_by_category, get_active_knowledge_articles,
    # VTB Task tools
    similarvtbtasksfortext, getshortdescforvtbtask, similarvtbtasksforvtbtask, getvtbtaskdetails,
    createvtbtask, updatevtbtask, getvtbtasksbyfilter,
    # Table tools
    nowtestauth, nowtestauthInput
)
from utility_tools import nowtest, nowtestoauth, nowauthinfo

mcp = FastMCP("personalmcpservicenow")

# Register optimized tools
tools = [
    nowtest, nowtestoauth, nowauthinfo, nowtestauth, nowtestauthInput,
    similarURfortext, getshortdescforUR, similarURsforUR, getURdetails,
    similarincidentsfortext, getshortdescforincident, similarincidentsforincident, 
    getincidentdetails, getIncidentsByFilter,
    similarchangesfortext, getshortdescforchange, similarchangesforchange, getchangedetails,
    similar_knowledge_for_text, get_knowledge_by_category, get_active_knowledge_articles, get_knowledge_details,
    similarvtbtasksfortext, getshortdescforvtbtask, similarvtbtasksforvtbtask, getvtbtaskdetails,
    createvtbtask, updatevtbtask, getvtbtasksbyfilter
]

for tool in tools:
    mcp.tool()(tool)