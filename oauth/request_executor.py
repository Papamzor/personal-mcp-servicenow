"""Authenticated HTTP request execution with 401 retry.

Owns the actual ``httpx.AsyncClient`` lifecycle for ServiceNow API calls
and the retry-with-fresh-token policy for 401 responses. Read paths
swallow errors (return None); write paths re-raise so callers can map
HTTP status codes to domain-specific error messages.

The auth-header source is injected as a callable so the façade can
supply its own ``get_auth_headers`` bound method — letting tests patch
``client.get_auth_headers`` and have the patch take effect inside the
executor's request loop.
"""
from __future__ import annotations

import json
from typing import Any, Awaitable, Callable, Dict, Optional

import httpx

from oauth.token_store import TokenStore


AuthHeaderSource = Callable[[], Awaitable[Dict[str, str]]]


class RequestExecutor:
    """Make authenticated HTTP requests with token-refresh on 401."""

    def __init__(
        self,
        get_auth_headers: AuthHeaderSource,
        token_store: TokenStore,
    ) -> None:
        self._get_auth_headers = get_auth_headers
        self._token_store = token_store

    async def make_authenticated_request(
        self,
        method: str,
        url: str,
        raise_for_status: bool = False,
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        """Make an authenticated request to ServiceNow API.

        When ``raise_for_status=True``, propagates ``httpx.HTTPStatusError`` so
        the caller can map status codes to domain-specific error messages
        (used by write operations like vtb_task CRUD). Read operations keep
        the default permissive behaviour and return ``None`` on failure.
        """
        headers = await self._get_auth_headers()

        if "headers" in kwargs:
            merged = dict(headers)
            merged.update(kwargs["headers"])
            headers = merged
        kwargs["headers"] = headers

        async with httpx.AsyncClient(verify=True) as client:
            try:
                response = await client.request(method, url, timeout=30.0, **kwargs)
                response.raise_for_status()
                return self._process_response(response)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    return await self._retry_with_fresh_token(
                        client, method, url,
                        raise_for_status=raise_for_status,
                        **kwargs,
                    )
                if raise_for_status:
                    raise
                return None
            except (httpx.RequestError, httpx.TimeoutException, json.JSONDecodeError):
                return None

    def _process_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Decode a successful response payload."""
        return response.json()

    async def _retry_with_fresh_token(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        raise_for_status: bool = False,
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        """Drop the cached token, re-authenticate, retry once."""
        await self._token_store.clear()

        headers = await self._get_auth_headers()
        kwargs["headers"] = headers

        try:
            response = await client.request(method, url, timeout=30.0, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError:
            if raise_for_status:
                raise
            return None
        except (httpx.RequestError, httpx.TimeoutException, json.JSONDecodeError):
            return None
