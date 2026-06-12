"""Module-level OAuth client singleton + convenience request helpers.

Canonical home (v4.1) of the process-wide ``ServiceNowOAuthClient``
instance and the ``get_oauth_client`` / ``make_oauth_request`` helpers.
Before v4.1 these lived in the ``oauth_client.py`` shim; that shim is
now deleted and this is the single source of truth.

``httpx`` is re-exported so tests can patch
``oauth.singleton.httpx.AsyncClient`` (patching the attribute on the
shared httpx module also affects the executor/token-store call sites).
"""
from __future__ import annotations

from typing import Any, Optional

import httpx  # re-exported for tests that patch ``oauth.singleton.httpx.AsyncClient``

from oauth.client import ServiceNowOAuthClient

__all__ = ["get_oauth_client", "make_oauth_request", "httpx"]

# Process-wide singleton. Tests reset it via ``oauth.singleton._oauth_client = None``.
_oauth_client: Optional[ServiceNowOAuthClient] = None


def get_oauth_client() -> ServiceNowOAuthClient:
    """Get or create the global OAuth client instance."""
    global _oauth_client
    if _oauth_client is None:
        _oauth_client = ServiceNowOAuthClient()
    return _oauth_client


async def make_oauth_request(url: str) -> Optional[dict[str, Any]]:
    """Convenience function for making OAuth-authenticated GET requests."""
    client = get_oauth_client()
    return await client.make_authenticated_request("GET", url)
