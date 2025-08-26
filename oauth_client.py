import httpx
import base64
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import json
import asyncio
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class ServiceNowOAuthClient:
    """OAuth 2.0 Client Credentials implementation for ServiceNow."""
    
    def __init__(self):
        self.instance_url = os.getenv("SERVICENOW_INSTANCE")
        self.client_id = os.getenv("SERVICENOW_CLIENT_ID")
        self.client_secret = os.getenv("SERVICENOW_CLIENT_SECRET")
        
        # Token management
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._token_lock = asyncio.Lock()
        
        # Validate configuration
        if not all([self.instance_url, self.client_id, self.client_secret]):
            raise ValueError(
                "Missing OAuth configuration. Ensure SERVICENOW_INSTANCE, "
                "SERVICENOW_CLIENT_ID, and SERVICENOW_CLIENT_SECRET are set."
            )
        
        self.token_endpoint = f"{self.instance_url}/oauth_token.do"
    
    def _get_basic_auth_header(self) -> str:
        """Generate Basic Auth header for client credentials."""
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded_credentials}"
    
    async def _request_access_token(self) -> Dict[str, Any]:
        """Request a new access token from ServiceNow."""
        headers = {
            "Authorization": self._get_basic_auth_header(),
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = "grant_type=client_credentials"
        
        async with httpx.AsyncClient(verify=True) as client:
            try:
                response = await client.post(
                    self.token_endpoint,
                    headers=headers,
                    data=data,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise Exception("OAuth token request failed: Invalid client credentials")
                elif e.response.status_code == 403:
                    raise Exception("OAuth token request failed: Access denied")
                else:
                    raise Exception("OAuth token request failed: Server error")
            except Exception as e:
                raise Exception("OAuth token request error: Connection failed")
    
    async def _get_valid_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        async with self._token_lock:
            # Check if current token is still valid (with 5-minute buffer)
            now = datetime.now()
            if (self._access_token and 
                self._token_expires_at and 
                now < (self._token_expires_at - timedelta(minutes=5))):
                return self._access_token
            
            # Request new token
            token_data = await self._request_access_token()
            
            self._access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 1800)  # Default 30 minutes
            self._token_expires_at = now + timedelta(seconds=expires_in)
            
            return self._access_token
    
    async def get_auth_headers(self) -> Dict[str, str]:
        """Get headers with valid Bearer token for API requests."""
        token = await self._get_valid_token()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    async def make_authenticated_request(
        self, 
        method: str, 
        url: str, 
        **kwargs
    ) -> Dict[str, Any] | None:
        """Make an authenticated request to ServiceNow API."""
        headers = await self.get_auth_headers()
        
        # Merge with any additional headers
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
        kwargs["headers"] = headers
        
        async with httpx.AsyncClient(verify=True) as client:
            try:
                response = await client.request(method, url, timeout=30.0, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                # Handle potential token expiration
                if e.response.status_code == 401:
                    # Clear cached token and retry once
                    async with self._token_lock:
                        self._access_token = None
                        self._token_expires_at = None
                    
                    # Retry with fresh token
                    headers = await self.get_auth_headers()
                    kwargs["headers"] = headers
                    
                    try:
                        response = await client.request(method, url, timeout=30.0, **kwargs)
                        response.raise_for_status()
                        return response.json()
                    except Exception:
                        return None
                return None
            except Exception:
                return None
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test the OAuth connection by making a simple API call."""
        test_url = f"{self.instance_url}/api/now/table/sys_user?sysparm_limit=1"
        result = await self.make_authenticated_request("GET", test_url)
        
        if result:
            return {
                "status": "success",
                "message": "OAuth authentication successful",
                "token_valid": True,
                "expires_at": self._token_expires_at.isoformat() if self._token_expires_at else None
            }
        else:
            return {
                "status": "error", 
                "message": "OAuth authentication failed",
                "token_valid": False
            }

# Global OAuth client instance
_oauth_client = None

def get_oauth_client() -> ServiceNowOAuthClient:
    """Get or create the global OAuth client instance."""
    global _oauth_client
    if _oauth_client is None:
        _oauth_client = ServiceNowOAuthClient()
    return _oauth_client

async def make_oauth_request(url: str) -> dict[str, Any] | None:
    """Convenience function for making OAuth-authenticated requests."""
    client = get_oauth_client()
    return await client.make_authenticated_request("GET", url)