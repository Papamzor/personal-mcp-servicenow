from service_now_api_oauth import make_nws_request, NWS_API_BASE
from typing import Any
from utils import extract_keywords

# Define a common set of fields for all change functions
COMMON_CHANGE_FIELDS = [
    "number",
    "short_description",
    "priority",
    "sys_created_on",
    "state",
    "assigned_to",
    "assignment_group"
]

async def similarchangesfortext(input_text: str):
    """Get changes based on input text."""
    keywords = extract_keywords(input_text)
    for keyword in keywords:
        url = f"{NWS_API_BASE}/api/now/table/change_request?sysparm_fields={','.join(COMMON_CHANGE_FIELDS)}&sysparm_query=short_descriptionCONTAINS{keyword}"
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

async def get_change_details(input_change: str) -> dict[str, Any] | str:
    """Get detailed information for a given change based on input change number.
    
    Args:
        input_change: The change number (e.g., 'CHG0000001').
    
    Returns:
        A dictionary containing change request details or an error message if the request fails.
    """
    fields = COMMON_CHANGE_FIELDS + [
        "description",
        "comments",
        "work_notes",
        "close_code",
        "close_notes",
        "sys_updated_on"
    ]
    url = f"{NWS_API_BASE}/api/now/table/change_request?sysparm_fields={','.join(fields)}&sysparm_query=number={input_change}"
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