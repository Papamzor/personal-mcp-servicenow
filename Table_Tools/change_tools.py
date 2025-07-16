from service_now_api import make_nws_request, NWS_API_BASE
from typing import Any
from utils import extract_keywords

async def similarchangesfortext(inputText: str):
    """Get changes based on input text."""
    keywords = extract_keywords(inputText)
    for keyword in keywords:
        url = f"{NWS_API_BASE}/api/now/table/change_request?sysparm_fields=number,short_description&sysparm_query=short_descriptionCONTAINS{keyword}"
        data = await make_nws_request(url)
        if data:
            return data
    return "Unable to fetch alerts or no alerts found."

async def getshortdescforchange(inputchange: str):
    """Get short_description for a given change based on input change number."""
    keywords = extract_keywords(inputchange)
    for keyword in keywords:
        url = f"{NWS_API_BASE}/api/now/table/change_request?sysparm_fields=short_description&sysparm_query=number={inputchange}"
        data = await make_nws_request(url)
        if data:
            return data
    return "Unable to fetch alerts or no alerts found."

async def similarchangesforchange(inputchange: str):
    """Get similar changes based on given change."""
    inputText = await getshortdescforchange(inputchange)
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
        "state",
        "comments",
        "priority",
        "assigned_to",
        "assignment_group",
        "start_date",
        "end_date",
        "reason",
        "risk",
        "type",
        "work_notes",
        "close_code",
        "close_notes",
        "sys_updated_on"
    ]
    url = f"{NWS_API_BASE}/api/now/table/change_request?sysparm_fields={','.join(fields)}&sysparm_query=number={inputchange}"
    data = await make_nws_request(url)
    if data and data.get('result'):
        results = data['result']
        # If results is a non-empty list, return the first item (robust for MCP validation)
        if isinstance(results, list) and results:
            return results[0]
        # If results is a dict, return it directly (handles edge cases from API)
        elif isinstance(results, dict):
            return results
    # Return error string if no valid result found
    return "Unable to fetch change details or no change found."