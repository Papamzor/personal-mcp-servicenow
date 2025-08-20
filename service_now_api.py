import httpx
from typing import Any
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
SERVICENOW_USERNAME = os.getenv("SERVICENOW_USERNAME")
SERVICENOW_PASSWORD = os.getenv("SERVICENOW_PASSWORD") 
SERVICENOW_INSTANCE = os.getenv("SERVICENOW_INSTANCE")

NWS_API_BASE = SERVICENOW_INSTANCE

def _extract_display_values(data: dict[str, Any]) -> dict[str, Any]:
    """Extract display values from ServiceNow API response."""
    if not isinstance(data, dict):
        return data
    
    # Process the result array if it exists
    if 'result' in data and isinstance(data['result'], list):
        processed_results = []
        for item in data['result']:
            if isinstance(item, dict):
                processed_item = {}
                for key, value in item.items():
                    if isinstance(value, dict) and 'display_value' in value:
                        # Extract just the display value for reference fields
                        processed_item[key] = value['display_value']
                    else:
                        processed_item[key] = value
                processed_results.append(processed_item)
            else:
                processed_results.append(item)
        data['result'] = processed_results
    
    return data

async def make_nws_request(url: str, display_value: bool = True) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    # Use the loaded environment variables for authentication
    auth = (SERVICENOW_USERNAME, SERVICENOW_PASSWORD)
    
    # Add display value parameter if requested
    if display_value and "sysparm_display_value" not in url:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}sysparm_display_value=true"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, auth=auth, headers=headers, timeout=30.0)
            response.raise_for_status()
            result = response.json()
            return _extract_display_values(result) if result and display_value else result
        except Exception:
            return None
