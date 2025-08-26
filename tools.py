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
    # Private Task tools (vtb_task table)
    similarprivatetasksfortext, getshortdescforprivatetask, similarprivatetasksforprivatetask, getprivatetaskdetails,
    createprivatetask, updateprivatetask, getprivatetasksbyfilter,
    # Table tools
    nowtestauth, nowtestauthInput,
    # CMDB tools
    findCIsByType, searchCIsByAttributes, getCIDetails, similarCIsForCI, getAllCITypes, quickCISearch
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
    similarprivatetasksfortext, getshortdescforprivatetask, similarprivatetasksforprivatetask, getprivatetaskdetails,
    createprivatetask, updateprivatetask, getprivatetasksbyfilter,
    # CMDB tools
    findCIsByType, searchCIsByAttributes, getCIDetails, similarCIsForCI, getAllCITypes, quickCISearch
]

for tool in tools:
    mcp.tool()(tool)