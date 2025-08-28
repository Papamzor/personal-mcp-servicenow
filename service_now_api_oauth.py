from typing import Any
from dotenv import load_dotenv
import os
from oauth_client import get_oauth_client, make_oauth_request

# Load environment variables from .env file
load_dotenv()
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
    """Make a request to the ServiceNow API using OAuth 2.0 authentication."""
    
    # Add display value parameter if requested
    if display_value and "sysparm_display_value" not in url:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}sysparm_display_value=true"
    
    try:
        result = await make_oauth_request(url)
        return _extract_display_values(result) if result and display_value else result
    except Exception as e:
        print(f"OAuth request failed: {str(e)}")
        return None

async def test_oauth_connection() -> dict[str, Any]:
    """Test OAuth connection and return status."""
    try:
        client = get_oauth_client()
        return await client.test_connection()
    except Exception as e:
        return {
            "status": "error",
            "message": f"OAuth configuration error: {str(e)}",
            "oauth_available": False
        }

def get_auth_info() -> dict[str, Any]:
    """Get information about current authentication method."""
    return {
        "oauth_enabled": True,
        "instance_url": SERVICENOW_INSTANCE,
        "auth_method": "oauth"
    }