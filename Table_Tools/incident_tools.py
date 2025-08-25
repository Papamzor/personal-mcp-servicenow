from service_now_api_oauth import make_nws_request, NWS_API_BASE
from utils import extract_keywords
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field


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

async def similarincidentsfortext(inputText: str):
    """Get incidents based on input text."""
    keywords = extract_keywords(inputText)
    for keyword in keywords:
        url = f"{NWS_API_BASE}/api/now/table/incident?sysparm_fields={','.join(COMMON_INCIDENT_FIELDS)}&sysparm_query=short_descriptionCONTAINS{keyword}"
        data = await make_nws_request(url)
        if data:
            return data
    return "Unable to fetch alerts or no alerts found."

async def getshortdescforincident(inputincident: str):
    """Get short_description for a given incident based on input incident number."""
    keywords = extract_keywords(inputincident)
    for keyword in keywords:
        url = f"{NWS_API_BASE}/api/now/table/incident?sysparm_fields=short_description&sysparm_query=number={inputincident}"
        data = await make_nws_request(url)
        if data:
            return data
    return "Unable to fetch alerts or no alerts found."

async def similarincidentsforincident(inputincident: str):
    """Get similar incidents based on given incident."""
    inputText = await getshortdescforincident(inputincident)
    return await similarincidentsfortext(inputText)

async def getincidentdetails(inputincident: str) -> dict[str, Any] | str:
    """Get detailed information for a given incident based on input incident number.
    
    Args:
        inputincident: The incident number (e.g., 'INC0127661').
    
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
    url = f"{NWS_API_BASE}/api/now/table/incident?sysparm_fields={','.join(fields)}&sysparm_query=number={inputincident}"
    data = await make_nws_request(url)
    if data and data.get('result'):
        results = data['result']
        if isinstance(results, list) and results:
            return results[0]
        elif isinstance(results, dict):
            return results
    return "Unable to fetch incident details or no incident found."

async def getIncidentsByFilter(params: IncidentFilterParams) -> dict[str, Any] | str:
    fields = params.fields or COMMON_INCIDENT_FIELDS
    query_parts = []
    if params.filters:
        for field, value in params.filters.items():
            if field.endswith('_gte'):
                base_field = field[:-4]
                query_parts.append(f"{base_field}>={value}")
            elif field.endswith('_lte'):
                base_field = field[:-4]
                query_parts.append(f"{base_field}<={value}")
            else:
                query_parts.append(f"{field}={value}")
    sysparm_query = "^".join(query_parts) if query_parts else ""
    url = f"{NWS_API_BASE}/api/now/table/incident?sysparm_fields={','.join(fields)}&sysparm_query={sysparm_query}"
    data = await make_nws_request(url)
    if data and data.get('result'):
        return data
    return "Unable to fetch incidents or no incidents found."