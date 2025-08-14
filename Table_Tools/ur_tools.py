from service_now_api import make_nws_request, NWS_API_BASE
from typing import Any
from utils import extract_keywords

# Define a common set of fields for all UR functions
COMMON_UR_FIELDS = [
    "number",
    "short_description",
    "sys_created_on",
    "state",
    "assigned_to",
    "assignment_group"
]

async def similarURfortext(inputText: str):
    """Get universal requests based on input text."""
    keywords = extract_keywords(inputText)
    for keyword in keywords:
        url = f"{NWS_API_BASE}/api/now/table/universal_request?sysparm_fields={','.join(COMMON_UR_FIELDS)}&sysparm_query=short_descriptionCONTAINS{keyword}"
        data = await make_nws_request(url)
        if data:
            return data
    return "Unable to fetch alerts or no alerts found."

async def getshortdescforUR(inputUR: str):
    """Get short_description for a given universal request based on input universal request number."""
    keywords = extract_keywords(inputUR)
    for keyword in keywords:
        url = f"{NWS_API_BASE}/api/now/table/universal_request?sysparm_fields=short_description&sysparm_query=number={inputUR}"
        data = await make_nws_request(url)
        if data:
            return data
    return "Unable to fetch alerts or no alerts found."

async def similarURsforUR(inputUR: str):
    """Get similar universal requests based on given universal request."""
    inputText = await getshortdescforUR(inputUR)
    return await similarURfortext(inputText)

async def getURdetails(inputUR: str) -> dict[str, Any] | str:
    """Get detailed information for a given universal request based on input universal request number.
    
    Args:
        inputur: The universal request number (e.g., 'UR0000001').
    
    Returns:
        A dictionary containing universal request details or an error message if the request fails.
    """
    fields = COMMON_UR_FIELDS + [
        "description",
        "comments",
        "sys_updated_on"
    ]
    url = f"{NWS_API_BASE}/api/now/table/universal_request?sysparm_fields={','.join(fields)}&sysparm_query=number={inputUR}"
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