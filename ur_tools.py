from service_now_api import make_nws_request, NWS_API_BASE
from typing import Any
from utils import getKeywords

async def similarURfortext(inputText: str):
    """Get universal requests based on input text."""
    keywords = getKeywords(inputText)
    for keyword in keywords:
        url = f"{NWS_API_BASE}/api/now/table/universal_request?sysparm_fields=number,short_description&sysparm_query=short_descriptionCONTAINS{keyword}"
        data = await make_nws_request(url)
        if data:
            return data
    return "Unable to fetch alerts or no alerts found."

async def getshortdescforUR(inputincident: str):
    """Get short_description for a given universal request based on input universal request number."""
    keywords = getKeywords(inputincident)
    for keyword in keywords:
        url = f"{NWS_API_BASE}/api/now/table/universal_request?sysparm_fields=short_description&sysparm_query=number={inputincident}"
        data = await make_nws_request(url)
        if data:
            return data
    return "Unable to fetch alerts or no alerts found."

async def similarURsforUR(inputincident: str):
    """Get similar universal requests based on given universal request."""
    inputText = await getshortdescforUR(inputincident)
    return await similarURfortext(inputText)

async def getURdetails(inputUR: str) -> dict[str, Any] | str:
    """Get detailed information for a given universal request based on input universal request number.
    
    Args:
        inputur: The universal request number (e.g., 'UR0000001').
    
    Returns:
        A dictionary containing universal request details or an error message if the request fails.
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
    url = f"{NWS_API_BASE}/api/now/table/universal_request?sysparm_fields={','.join(fields)}&sysparm_query=number={inputUR}"
    data = await make_nws_request(url)
    if data and data.get('result'):
        return data['result']
    return "Unable to fetch change details or no change found."