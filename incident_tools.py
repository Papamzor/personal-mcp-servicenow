from service_now_api import make_nws_request, NWS_API_BASE
from utils import getKeywords
from typing import Any

async def similarincidentsfortext(inputText: str):
    """Get incidents based on input text."""
    keywords = getKeywords(inputText)
    for keyword in keywords:
        url = f"{NWS_API_BASE}/api/now/table/incident?sysparm_fields=number,short_description&sysparm_query=short_descriptionCONTAINS{keyword}"
        data = await make_nws_request(url)
        if data:
            return data
    return "Unable to fetch alerts or no alerts found."

async def getshortdescforincident(inputincident: str):
    """Get short_description for a given incident based on input incident number."""
    keywords = getKeywords(inputincident)
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
        inputincident: The incident number (e.g., 'INC0010001').
    
    Returns:
        A dictionary containing incident details or an error message if the request fails.
    """
    fields = [
        "number",
        "short_description",
        "description",
        "comments",
        "assigned_to",
        "assignment_group",
        "priority",
        "state",
        "work_notes",
        "close_code",
        "close_notes",
        "sys_updated_on"
    ]
    url = f"{NWS_API_BASE}/api/now/table/incident?sysparm_fields={','.join(fields)}&sysparm_query=number={inputincident}"
    data = await make_nws_request(url)
    if data and data.get('result'):
        return data['result']
    return "Unable to fetch incident details or no incident found."