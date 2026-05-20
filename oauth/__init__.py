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

The module-level singleton ``get_oauth_client`` and
``make_oauth_request`` continue to live in ``oauth_client.py`` (now a
shim) so existing test patches like
``patch("oauth_client._oauth_client")`` keep working.
"""
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
]
