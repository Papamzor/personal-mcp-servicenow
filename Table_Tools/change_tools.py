from service_now_api import make_nws_request, NWS_API_BASE
from typing import Any
from utils import getKeywords

async def similarchangesfortext(inputText: str):
    """Get changes based on input text."""
    keywords = getKeywords(inputText)
    for keyword in keywords:
        url = f"{NWS_API_BASE}/api/now/table/change_request?sysparm_fields=number,short_description&sysparm_query=short_descriptionCONTAINS{keyword}"
        data = await make_nws_request(url)
        if data:
            return data
    return "Unable to fetch alerts or no alerts found."

async def getshortdescforchange(inputincident: str):
    """Get short_description for a given change based on input change number."""
    keywords = getKeywords(inputincident)
    for keyword in keywords:
        url = f"{NWS_API_BASE}/api/now/table/change_request?sysparm_fields=short_description&sysparm_query=number={inputincident}"
        data = await make_nws_request(url)
        if data:
            return data
    return "Unable to fetch alerts or no alerts found."

async def similarchangesforchange(inputincident: str):
    """Get similar changes based on given change."""
    inputText = await getshortdescforchange(inputincident)
    return await similarchangesfortext(inputText)

async def getchangedetails(inputchange: str) -> dict[str, Any] | str:
    """Get detailed information for a given change based on input change number.
    
    Args:
        inputchange: The change number (e.g., 'CHG0000001').
    
    Returns:
        A dictionary containing change request details or an error message if the request fails.
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
        "sys_updated_on"
    ]
    url = f"{NWS_API_BASE}/api/now/table/change_request?sysparm_fields={','.join(fields)}&sysparm_query=number={inputchange}"
    data = await make_nws_request(url)
    if data and data.get('result'):
        return data['result']
    return "Unable to fetch change details or no change found."