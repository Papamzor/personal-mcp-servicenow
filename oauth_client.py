"""Backwards-compat shim — v4.0 split OAuth client into the ``oauth/`` package.

The ``ServiceNowOAuthClient`` class and exception hierarchy now live in
``oauth/``. This module remains as the canonical home of the module-level
singleton (``_oauth_client``, ``get_oauth_client``, ``make_oauth_request``)
and of the ``httpx`` re-export so test patches like
``patch("oauth_client.httpx.AsyncClient")`` and
``oauth_client._oauth_client = None`` keep working without rewriting
every fixture.

Delete the re-exports in v4.1; tests should be migrated to
``patch("oauth.client.httpx.AsyncClient")`` or the equivalent on the
relocated subsystem at that point.
"""
from __future__ import annotations

from typing import Any, Optional

import httpx  # re-exported for tests that patch ``oauth_client.httpx.AsyncClient``

from oauth.client import ServiceNowOAuthClient
from oauth.exceptions import (
    ServiceNowAuthenticationError,
    ServiceNowAuthorizationError,
    ServiceNowConnectionError,
    ServiceNowOAuthError,
)

__all__ = [
    "ServiceNowOAuthClient",
    "ServiceNowOAuthError",
    "ServiceNowAuthenticationError",
    "ServiceNowConnectionError",
    "ServiceNowAuthorizationError",
    "get_oauth_client",
    "make_oauth_request",
    "httpx",
]

# Module-level singleton kept here (not in oauth/) so existing tests that
# do ``oauth_client._oauth_client = None`` to reset state continue to
# work. Moving the binding would silently break those resets.
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
