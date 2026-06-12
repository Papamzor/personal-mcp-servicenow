"""OAuth 2.0 client for ServiceNow — v4.0 Sprint 3 split.

The single 165-line ``ServiceNowOAuthClient`` from v3 mixed eight
concerns (config, basic auth header, token request, token cache,
bearer header, request execution, retry policy, connection test).
v4.0 splits these into three subsystems that compose via the public
class façade.

Public API:
    ServiceNowOAuthClient   façade — composes TokenStore +
                            AuthHeaderProvider + RequestExecutor
    ServiceNowOAuthError    base exception
    ServiceNowAuthenticationError
    ServiceNowConnectionError
    ServiceNowAuthorizationError

The module-level singleton ``get_oauth_client`` / ``make_oauth_request``
lives in ``oauth/singleton.py`` (v4.1 — was the ``oauth_client.py`` shim,
now deleted).
"""
from oauth.client import ServiceNowOAuthClient
from oauth.exceptions import (
    ServiceNowAuthenticationError,
    ServiceNowAuthorizationError,
    ServiceNowConnectionError,
    ServiceNowOAuthError,
)
from oauth.singleton import get_oauth_client, make_oauth_request

__all__ = [
    "ServiceNowOAuthClient",
    "ServiceNowOAuthError",
    "ServiceNowAuthenticationError",
    "ServiceNowConnectionError",
    "ServiceNowAuthorizationError",
    "get_oauth_client",
    "make_oauth_request",
]
