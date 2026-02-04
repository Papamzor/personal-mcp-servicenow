import orjson
from typing import Any
from dotenv import load_dotenv
import os
from oauth_client import get_oauth_client, make_oauth_request

# Load environment variables from .env file
load_dotenv()
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

def _add_default_params(url: str, display_value: bool = True) -> str:
    """Add default performance and display parameters to a ServiceNow API URL."""
    params = []
    if display_value and "sysparm_display_value" not in url:
        params.append("sysparm_display_value=true")
    if "sysparm_exclude_reference_link" not in url:
        params.append("sysparm_exclude_reference_link=true")
    if "sysparm_no_count" not in url:
        params.append("sysparm_no_count=true")
    if not params:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}{'&'.join(params)}"

async def make_nws_request(url: str, display_value: bool = True) -> dict[str, Any] | None:
    """Make a request to the ServiceNow API using OAuth 2.0 authentication."""
    url = _add_default_params(url, display_value)

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