import httpx
from typing import Any
from dotenv import load_dotenv
import os
from constants import JSON_HEADERS

# Load environment variables from .env file
load_dotenv()
SERVICENOW_USERNAME = os.getenv("SERVICENOW_USERNAME")
SERVICENOW_PASSWORD = os.getenv("SERVICENOW_PASSWORD") 
SERVICENOW_INSTANCE = os.getenv("SERVICENOW_INSTANCE")

NWS_API_BASE = SERVICENOW_INSTANCE

def _extract_field_value(value: Any) -> Any:
    """Extract the appropriate value (display_value if available, otherwise raw value)."""
    if isinstance(value, dict) and 'display_value' in value:
        return value['display_value']
    return value

def _process_item_dict(item: dict) -> dict:
    """Process a single dictionary item to extract display values."""
    return {key: _extract_field_value(value) for key, value in item.items()}

def _extract_display_values(data: dict[str, Any]) -> dict[str, Any]:
    """Extract display values from ServiceNow API response."""
    if not isinstance(data, dict):
        return data
    
    if 'result' not in data or not isinstance(data['result'], list):
        return data
    
    data['result'] = [_process_item_dict(item) if isinstance(item, dict) else item 
                      for item in data['result']]
    return data

async def make_nws_request(url: str, display_value: bool = True) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = JSON_HEADERS
    # Use the loaded environment variables for authentication
    auth = (SERVICENOW_USERNAME, SERVICENOW_PASSWORD)
    
    # Add display value parameter if requested
    if display_value and "sysparm_display_value" not in url:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}sysparm_display_value=true"
    
    async with httpx.AsyncClient(verify=True) as client:
        try:
            response = await client.get(url, auth=auth, headers=headers, timeout=30.0)
            response.raise_for_status()
            result = response.json()
            return _extract_display_values(result) if result and display_value else result
        except Exception:
            return None
