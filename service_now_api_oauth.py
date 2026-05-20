"""Backwards-compat shim — v4.0 split the HTTP layer into ``http_layer/``.

The ``make_nws_request`` orchestrator, ``test_oauth_connection``, and
``get_auth_info`` were moved to ``http_layer/request_dispatcher.py``;
the URL builder and response parser live in their own modules. This
shim re-exports every public AND private name v3 exposed so existing
imports keep working — including the private helpers tests import
directly (``_extract_field_value``, ``_ensure_query_encoded``, etc.).

It also keeps ``make_oauth_request`` and ``get_oauth_client`` as
module-level names so patch targets like
``patch("service_now_api_oauth.make_oauth_request", ...)`` and
``patch("service_now_api_oauth.get_oauth_client")`` continue to resolve.

Delete in v4.1 once consumers have migrated to ``from http_layer import ...``.
"""
from http_layer.request_dispatcher import (
    NWS_API_BASE,
    get_auth_info,
    make_nws_request,
    test_oauth_connection,
)
from http_layer.response_parser import (
    extract_display_values as _extract_display_values,
    extract_field_value as _extract_field_value,
    process_item_dict as _process_item_dict,
)
from http_layer.url_builder import (
    add_default_params as _add_default_params,
    ensure_query_encoded as _ensure_query_encoded,
)

# Re-export the oauth-layer module-level singletons so the v3 patch
# targets ``service_now_api_oauth.make_oauth_request`` and
# ``service_now_api_oauth.get_oauth_client`` still resolve. The
# request_dispatcher imports through these names too, so a patch on
# this module's name actually changes what the dispatcher sees.
from oauth_client import get_oauth_client, make_oauth_request

__all__ = [
    "make_nws_request",
    "test_oauth_connection",
    "get_auth_info",
    "NWS_API_BASE",
    "_extract_field_value",
    "_process_item_dict",
    "_extract_display_values",
    "_ensure_query_encoded",
    "_add_default_params",
    "make_oauth_request",
    "get_oauth_client",
]
