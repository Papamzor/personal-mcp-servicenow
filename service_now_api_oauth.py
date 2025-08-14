import httpx
from typing import Any
from dotenv import load_dotenv
import os
from oauth_client import get_oauth_client, make_oauth_request

# Load environment variables from .env file
load_dotenv()
SERVICENOW_INSTANCE = os.getenv("SERVICENOW_INSTANCE")

# Legacy basic auth credentials (fallback)
SERVICENOW_USERNAME = os.getenv("SERVICENOW_USERNAME")
SERVICENOW_PASSWORD = os.getenv("SERVICENOW_PASSWORD") 

NWS_API_BASE = SERVICENOW_INSTANCE

def _get_oauth_credentials():
    """Get OAuth credentials from environment variables."""
    return os.getenv("SERVICENOW_CLIENT_ID"), os.getenv("SERVICENOW_CLIENT_SECRET")

def _should_use_oauth():
    """Determine if OAuth should be used."""
    client_id, client_secret = _get_oauth_credentials()
    return bool(client_id and client_secret)

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the ServiceNow API with OAuth or Basic Auth fallback."""
    
    if _should_use_oauth():
        # Use OAuth 2.0 Client Credentials
        try:
            return await make_oauth_request(url)
        except Exception as e:
            print(f"OAuth request failed, falling back to basic auth: {str(e)}")
            # Fall back to basic auth if OAuth fails
    
    # Basic Auth fallback
    if not (SERVICENOW_USERNAME and SERVICENOW_PASSWORD):
        print("No valid authentication method available")
        return None
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    auth = (SERVICENOW_USERNAME, SERVICENOW_PASSWORD)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, auth=auth, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

async def test_oauth_connection() -> dict[str, Any]:
    """Test OAuth connection and return status."""
    if not _should_use_oauth():
        return {
            "status": "disabled",
            "message": "OAuth not configured. Using basic auth.",
            "oauth_available": False
        }
    
    try:
        client = get_oauth_client()
        return await client.test_connection()
    except Exception as e:
        return {
            "status": "error",
            "message": f"OAuth configuration error: {str(e)}",
            "oauth_available": False
        }

async def get_auth_info() -> dict[str, Any]:
    """Get information about current authentication method."""
    oauth_enabled = _should_use_oauth()
    return {
        "oauth_enabled": oauth_enabled,
        "basic_auth_available": bool(SERVICENOW_USERNAME and SERVICENOW_PASSWORD),
        "instance_url": SERVICENOW_INSTANCE,
        "auth_method": "oauth" if oauth_enabled else "basic"
    }