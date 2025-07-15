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

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    # Use the loaded environment variables for authentication
    auth = (SERVICENOW_USERNAME, SERVICENOW_PASSWORD)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, auth=auth, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None
