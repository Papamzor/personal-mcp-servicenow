import httpx
from typing import Any

NWS_API_BASE = "https://matecodev.service-now.com"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    auth = ("redacted", "redacted")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, auth=auth, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None
