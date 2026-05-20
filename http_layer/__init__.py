"""HTTP layer for the ServiceNow REST API — v4.0 Sprint 3 split.

The v3 ``service_now_api_oauth.py`` mixed URL construction, response
transformation, and read/write dispatch in one ~120-line module. v4.0
splits the concerns into three:

    url_builder.py        URL encoding + read-only performance params
    response_parser.py    display-value flattening
    request_dispatcher.py make_nws_request (orchestrator)

Public API:
    make_nws_request, NWS_API_BASE     re-exported from request_dispatcher
    test_oauth_connection, get_auth_info  re-exported from request_dispatcher

The module-level singleton (``get_oauth_client`` / ``make_oauth_request``)
continues to live in ``oauth_client.py`` (an oauth-layer shim).
"""
from http_layer.request_dispatcher import (
    NWS_API_BASE,
    get_auth_info,
    make_nws_request,
    test_oauth_connection,
)

__all__ = [
    "make_nws_request",
    "test_oauth_connection",
    "get_auth_info",
    "NWS_API_BASE",
]
