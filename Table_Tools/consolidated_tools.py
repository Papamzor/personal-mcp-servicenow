from .generic_table_tools import (
    query_table_by_text, 
    get_record_description, 
    get_record_details, 
    find_similar_records,
    query_table_with_filters,
    TableFilterParams
)
from typing import Any, Dict, Optional, List

# INCIDENT TOOLS - Consolidated
async def similarincidentsfortext(input_text: str) -> dict[str, Any] | str:
    """Find incidents based on input text."""
    return await query_table_by_text("incident", input_text)

async def getshortdescforincident(input_incident: str) -> dict[str, Any] | str:
    """Get short_description for incident."""
    return await get_record_description("incident", input_incident)

async def similarincidentsforincident(input_incident: str) -> dict[str, Any] | str:
    """Find similar incidents based on given incident."""
    # Try the optimized approach first
    try:
        result = await find_similar_records("incident", input_incident)
        if isinstance(result, dict):
            return result
    except Exception:
        pass
    
    # Fallback to original approach - get description then search
    try:
        desc_data = await getshortdescforincident(input_incident)
        if isinstance(desc_data, dict) and desc_data.get('result'):
            # Extract the actual description text
            if len(desc_data['result']) > 0:
                desc_text = desc_data['result'][0].get('short_description', '')
                if desc_text:
                    return await similarincidentsfortext(desc_text)
        return "No description found."
    except Exception:
        return "Connection error: Request failed"

async def getincidentdetails(input_incident: str) -> dict[str, Any] | str:
    """Get detailed incident information."""
    return await get_record_details("incident", input_incident)

async def getIncidentsByFilter(filters: Dict[str, str], fields: Optional[List[str]] = None) -> dict[str, Any] | str:
    """Get incidents with custom filters."""
    params = TableFilterParams(filters=filters, fields=fields)
    return await query_table_with_filters("incident", params)

# CHANGE TOOLS - Consolidated
async def similarchangesfortext(input_text: str) -> dict[str, Any] | str:
    """Find changes based on input text."""
    return await query_table_by_text("change_request", input_text)

async def getshortdescforchange(input_change: str) -> dict[str, Any] | str:
    """Get short_description for change."""
    return await get_record_description("change_request", input_change)

async def similarchangesforchange(input_change: str) -> dict[str, Any] | str:
    """Find similar changes based on given change."""
    try:
        result = await find_similar_records("change_request", input_change)
        if isinstance(result, dict):
            return result
    except Exception:
        pass
    
    # Fallback approach
    try:
        desc_data = await getshortdescforchange(input_change)
        if isinstance(desc_data, dict) and desc_data.get('result'):
            if len(desc_data['result']) > 0:
                desc_text = desc_data['result'][0].get('short_description', '')
                if desc_text:
                    return await similarchangesfortext(desc_text)
        return "No description found."
    except Exception:
        return "Connection error: Request failed"

async def getchangedetails(input_change: str) -> dict[str, Any] | str:
    """Get detailed change information."""
    return await get_record_details("change_request", input_change)

# UR TOOLS - Consolidated  
async def similarURfortext(input_text: str) -> dict[str, Any] | str:
    """Find URs based on input text."""
    return await query_table_by_text("universal_request", input_text)

async def getshortdescforUR(input_ur: str) -> dict[str, Any] | str:
    """Get short_description for UR."""
    return await get_record_description("universal_request", input_ur)

async def similarURsforUR(input_ur: str) -> dict[str, Any] | str:
    """Find similar URs based on given UR."""
    try:
        result = await find_similar_records("universal_request", input_ur)
        if isinstance(result, dict):
            return result
    except Exception:
        pass
    
    # Fallback approach
    try:
        desc_data = await getshortdescforUR(input_ur)
        if isinstance(desc_data, dict) and desc_data.get('result'):
            if len(desc_data['result']) > 0:
                desc_text = desc_data['result'][0].get('short_description', '')
                if desc_text:
                    return await similarURfortext(desc_text)
        return "No description found."
    except Exception:
        return "Connection error: Request failed"

async def getURdetails(input_ur: str) -> dict[str, Any] | str:
    """Get detailed UR information."""
    return await get_record_details("universal_request", input_ur)

# KNOWLEDGE TOOLS - Specialized (keeping existing functionality)
from .kb_tools import (
    similar_knowledge_for_text,
    get_knowledge_details, 
    get_knowledge_by_category,
    get_active_knowledge_articles
)

# PRIVATE TASK TOOLS (vtb_task table) - New
from .vtb_task_tools import (
    similarprivatetasksfortext,
    getshortdescforprivatetask,
    similarprivatetasksforprivatetask,
    getprivatetaskdetails,
    createprivatetask,
    updateprivatetask,
    getprivatetasksbyfilter
)

# TABLE TOOLS - Keep existing
from .table_tools import nowtestauth, nowtestauthInput

# CMDB TOOLS - CI Discovery & Search
from .cmdb_tools import (
    findCIsByType,
    searchCIsByAttributes,
    getCIDetails,
    similarCIsForCI,
    getAllCITypes,
    quickCISearch
)