from service_now_api_oauth import make_nws_request, NWS_API_BASE
from utils import extract_keywords
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
from .generic_table_tools import query_table_with_filters, TableFilterParams


class IncidentFilterParams(BaseModel):
    filters: Optional[Dict[str, str]] = Field(None, description="Field-value pairs for filtering")
    fields: Optional[List[str]] = Field(None, description="Fields to return")

# Define a common set of fields for all incident functions
COMMON_INCIDENT_FIELDS = [
    "number",
    "short_description",
    "priority",
    "sys_created_on",
    "state",
    "assigned_to",
    "assignment_group"
]

async def similarincidentsfortext(input_text: str):
    """Get incidents based on input text."""
    keywords = extract_keywords(input_text)
    for keyword in keywords:
        url = f"{NWS_API_BASE}/api/now/table/incident?sysparm_fields={','.join(COMMON_INCIDENT_FIELDS)}&sysparm_query=short_descriptionCONTAINS{keyword}"
        data = await make_nws_request(url)
        if data:
            return data
    return "Unable to fetch alerts or no alerts found."

async def getshortdescforincident(inputincident: str):
    """Get short_description for a given incident based on input incident number."""
    url = f"{NWS_API_BASE}/api/now/table/incident?sysparm_fields=short_description&sysparm_query=number={inputincident}"
    data = await make_nws_request(url)
    return data if data else "Incident not found."

async def similarincidentsforincident(inputincident: str):
    """Get similar incidents based on given incident."""
    input_text = await getshortdescforincident(inputincident)
    return await similarincidentsfortext(input_text)

async def get_incident_details(input_incident: str) -> dict[str, Any] | str:
    """Get detailed information for a given incident based on input incident number.
    
    Args:
        input_incident: The incident number (e.g., 'INC0127661').
    
    Returns:
        A dictionary containing incident details or an error message if the request fails.
    """
    fields = COMMON_INCIDENT_FIELDS + [
        "description",
        "comments",
        "work_notes",
        "close_code",
        "close_notes",
        "sys_updated_on"
    ]
    url = f"{NWS_API_BASE}/api/now/table/incident?sysparm_fields={','.join(fields)}&sysparm_query=number={input_incident}"
    data = await make_nws_request(url)
    if data and data.get('result'):
        results = data['result']
        if isinstance(results, list) and results:
            return results[0]
        elif isinstance(results, dict):
            return results
    return "Unable to fetch incident details or no incident found."

async def get_incidents_by_filter(params: IncidentFilterParams) -> dict[str, Any] | str:
    """Get incidents based on filters with proper date handling.
    
    Supports multiple date formats:
    - Standard dates: "2024-01-01" or "2024-01-01 12:00:00"
    - ServiceNow JavaScript: "javascript:gs.daysAgoStart(14)"
    - Relative operators: sys_created_on_gte, sys_created_on_lte, etc.
    
    Examples:
    - sys_created_on_gte: "2024-01-01"
    - sys_created_on: ">=javascript:gs.daysAgoStart(14)"
    """
    # Use default incident fields if not specified
    fields = params.fields or COMMON_INCIDENT_FIELDS
    
    # Convert IncidentFilterParams to TableFilterParams and delegate to generic function
    table_params = TableFilterParams(filters=params.filters, fields=fields)
    return await query_table_with_filters("incident", table_params)