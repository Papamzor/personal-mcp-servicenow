"""OAuth token cache + lifecycle.

Owns the access token, its expiry, the asyncio lock that serialises
refresh, and the HTTP call that obtains a new token from ServiceNow's
``/oauth_token.do`` endpoint. Other subsystems consume tokens via
``get_valid_token`` without seeing the cache details.

The token-fetch step is parametrised on a ``fetch_token_fn`` callable
so the ``ServiceNowOAuthClient`` façade can route through its own
``_request_access_token`` method — that lets tests patch
``client._request_access_token`` and have the patch take effect inside
the cache-refresh loop.
"""
from __future__ import annotations

import asyncio
import base64
import json
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Dict, Optional

import httpx

from constants import APPLICATION_JSON
from oauth.exceptions import (
    ServiceNowAuthenticationError,
    ServiceNowAuthorizationError,
    ServiceNowConnectionError,
    ServiceNowOAuthError,
)


TokenFetcher = Callable[[], Awaitable[Dict[str, Any]]]


class TokenStore:
    """Caches a single OAuth access token and refreshes it on demand."""

    def __init__(
        self,
        instance_url: str,
        client_id: str,
        client_secret: str,
        fetch_token_fn: Optional[TokenFetcher] = None,
    ) -> None:
        self.instance_url = instance_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_endpoint = f"{instance_url}/oauth_token.do"

        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._token_lock = asyncio.Lock()
        self._fetch_token_fn: TokenFetcher = fetch_token_fn or self._do_request_access_token

    # ---- public API -----------------------------------------------------

    async def get_valid_token(self) -> str:
        """Return a cached token or refresh if expired (with 5-minute buffer)."""
        async with self._token_lock:
            now = datetime.now()
            if (
                self._access_token
                and self._token_expires_at
                and now < (self._token_expires_at - timedelta(minutes=5))
            ):
                return self._access_token

            token_data = await self._fetch_token_fn()
            self._access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 1800)  # default 30 min
            self._token_expires_at = now + timedelta(seconds=expires_in)
            return self._access_token

    async def clear(self) -> None:
        """Discard the cached token. Used by the 401-retry path."""
        async with self._token_lock:
            self._access_token = None
            self._token_expires_at = None

    @property
    def expires_at(self) -> Optional[datetime]:
        """Read-only view of the current token's expiry."""
        return self._token_expires_at

    # ---- internals ------------------------------------------------------

    def _get_basic_auth_header(self) -> str:
        """Build the Basic Auth header used to authenticate the token request."""
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    # Kept as ``_request_access_token`` for v3 attribute parity (anything that
    # reached into TokenStore for this name directly continues to work). The
    # real call lives in ``_do_request_access_token``; this attribute is the
    # one ``get_valid_token`` invokes via the injectable hook.
    async def _request_access_token(self) -> Dict[str, Any]:
        return await self._do_request_access_token()

    async def _do_request_access_token(self) -> Dict[str, Any]:
        """POST the client-credentials grant to ServiceNow and return its JSON."""
        headers = {
            "Authorization": self._get_basic_auth_header(),
            "Accept": APPLICATION_JSON,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = "grant_type=client_credentials"

        async with httpx.AsyncClient(verify=True) as client:
            try:
                response = await client.post(
                    self.token_endpoint,
                    headers=headers,
                    data=data,
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                if status == 401:
                    raise ServiceNowAuthenticationError(
                        "OAuth token request failed: Invalid client credentials"
                    )
                if status == 403:
                    raise ServiceNowAuthorizationError(
                        "OAuth token request failed: Access denied"
                    )
                raise ServiceNowOAuthError(
                    f"OAuth token request failed: Server error (status {status})"
                )
            except (httpx.RequestError, httpx.TimeoutException) as e:
                raise ServiceNowConnectionError(
                    f"OAuth token request error: Connection failed - {e}"
                )
            except json.JSONDecodeError as e:
                raise ServiceNowOAuthError(
                    f"OAuth token response parsing failed: {e}"
                )
