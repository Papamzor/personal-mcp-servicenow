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
async def similarincidentsfortext(inputText: str) -> dict[str, Any] | str:
    """Find incidents based on input text."""
    return await query_table_by_text("incident", inputText)

async def getshortdescforincident(inputincident: str) -> dict[str, Any] | str:
    """Get short_description for incident."""
    return await get_record_description("incident", inputincident)

async def similarincidentsforincident(inputincident: str) -> dict[str, Any] | str:
    """Find similar incidents based on given incident."""
    # Try the optimized approach first
    try:
        result = await find_similar_records("incident", inputincident)
        if isinstance(result, dict):
            return result
    except Exception:
        pass
    
    # Fallback to original approach - get description then search
    try:
        desc_data = await getshortdescforincident(inputincident)
        if isinstance(desc_data, dict) and desc_data.get('result'):
            # Extract the actual description text
            if len(desc_data['result']) > 0:
                desc_text = desc_data['result'][0].get('short_description', '')
                if desc_text:
                    return await similarincidentsfortext(desc_text)
        return "No description found."
    except Exception as e:
        return f"Connection error: {str(e)}"

async def getincidentdetails(inputincident: str) -> dict[str, Any] | str:
    """Get detailed incident information."""
    return await get_record_details("incident", inputincident)

async def getIncidentsByFilter(filters: Dict[str, str], fields: Optional[List[str]] = None) -> dict[str, Any] | str:
    """Get incidents with custom filters."""
    params = TableFilterParams(filters=filters, fields=fields)
    return await query_table_with_filters("incident", params)

# CHANGE TOOLS - Consolidated
async def similarchangesfortext(inputText: str) -> dict[str, Any] | str:
    """Find changes based on input text."""
    return await query_table_by_text("change_request", inputText)

async def getshortdescforchange(inputchange: str) -> dict[str, Any] | str:
    """Get short_description for change."""
    return await get_record_description("change_request", inputchange)

async def similarchangesforchange(inputchange: str) -> dict[str, Any] | str:
    """Find similar changes based on given change."""
    try:
        result = await find_similar_records("change_request", inputchange)
        if isinstance(result, dict):
            return result
    except Exception:
        pass
    
    # Fallback approach
    try:
        desc_data = await getshortdescforchange(inputchange)
        if isinstance(desc_data, dict) and desc_data.get('result'):
            if len(desc_data['result']) > 0:
                desc_text = desc_data['result'][0].get('short_description', '')
                if desc_text:
                    return await similarchangesfortext(desc_text)
        return "No description found."
    except Exception as e:
        return f"Connection error: {str(e)}"

async def getchangedetails(inputchange: str) -> dict[str, Any] | str:
    """Get detailed change information."""
    return await get_record_details("change_request", inputchange)

# UR TOOLS - Consolidated  
async def similarURfortext(inputText: str) -> dict[str, Any] | str:
    """Find URs based on input text."""
    return await query_table_by_text("universal_request", inputText)

async def getshortdescforUR(inputUR: str) -> dict[str, Any] | str:
    """Get short_description for UR."""
    return await get_record_description("universal_request", inputUR)

async def similarURsforUR(inputUR: str) -> dict[str, Any] | str:
    """Find similar URs based on given UR."""
    try:
        result = await find_similar_records("universal_request", inputUR)
        if isinstance(result, dict):
            return result
    except Exception:
        pass
    
    # Fallback approach
    try:
        desc_data = await getshortdescforUR(inputUR)
        if isinstance(desc_data, dict) and desc_data.get('result'):
            if len(desc_data['result']) > 0:
                desc_text = desc_data['result'][0].get('short_description', '')
                if desc_text:
                    return await similarURfortext(desc_text)
        return "No description found."
    except Exception as e:
        return f"Connection error: {str(e)}"

async def getURdetails(inputUR: str) -> dict[str, Any] | str:
    """Get detailed UR information."""
    return await get_record_details("universal_request", inputUR)

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