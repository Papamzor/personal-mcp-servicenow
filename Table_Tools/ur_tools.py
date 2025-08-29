from service_now_api_oauth import make_nws_request, NWS_API_BASE
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

async def similar_ur_for_text(input_text: str):
    """Get universal requests based on input text."""
    keywords = extract_keywords(input_text)
    for keyword in keywords:
        url = f"{NWS_API_BASE}/api/now/table/universal_request?sysparm_fields={','.join(COMMON_UR_FIELDS)}&sysparm_query=short_descriptionCONTAINS{keyword}"
        data = await make_nws_request(url)
        if data:
            return data
    return "Unable to fetch alerts or no alerts found."

async def get_short_desc_for_ur(input_ur: str):
    """Get short_description for a given universal request based on input universal request number."""
    url = f"{NWS_API_BASE}/api/now/table/universal_request?sysparm_fields=short_description&sysparm_query=number={input_ur}"
    data = await make_nws_request(url)
    return data if data else "UR not found."

async def similar_urs_for_ur(input_ur: str):
    """Get similar universal requests based on given universal request."""
    input_text = await get_short_desc_for_ur(input_ur)
    return await similar_ur_for_text(input_text)

async def get_ur_details(input_ur: str) -> dict[str, Any] | str:
    """Get detailed information for a given universal request based on input universal request number.
    
    Args:
        input_ur: The universal request number (e.g., 'UR0000001').
    
    Returns:
        A dictionary containing universal request details or an error message if the request fails.
    """
    fields = COMMON_UR_FIELDS + [
        "description",
        "comments",
        "sys_updated_on"
    ]
    url = f"{NWS_API_BASE}/api/now/table/universal_request?sysparm_fields={','.join(fields)}&sysparm_query=number={input_ur}"
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