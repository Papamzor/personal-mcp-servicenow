"""Read/write request dispatcher for the ServiceNow REST API.

This is the v4.0 replacement for ``service_now_api_oauth.make_nws_request``.
Reads and writes share an entry point but their pipelines diverge:

    GET:
        url_builder.ensure_query_encoded
     -> url_builder.add_default_params       (read-only perf params)
     -> oauth_client.make_oauth_request
     -> response_parser.extract_display_values

    POST / PATCH / DELETE:
        oauth_client.get_oauth_client().make_authenticated_request(
            method, url, raise_for_status=True, json=json_data
        )

The write path explicitly skips the read-only param injection and the
display-value flattening — applying either to a write payload would
break the request shape or the response shape (per the token-optimization
invariant memory).
"""
from __future__ import annotations

import hashlib
import os
import sys
from typing import Any, Optional
from urllib.parse import urlsplit

import anyio

from http_layer.response_parser import extract_display_values
from http_layer.url_builder import add_default_params, ensure_query_encoded
from oauth.singleton import get_oauth_client, make_oauth_request

# .env is loaded once by oauth/client.py — imported above via oauth.singleton —
# before this line reads the environment, so no duplicate load_dotenv() here.
SERVICENOW_INSTANCE = os.getenv("SERVICENOW_INSTANCE")
NWS_API_BASE = SERVICENOW_INSTANCE


def _redact_url(url: str) -> str:
    """Path + stable query hash for stderr logs — never the raw sysparm_query."""
    parts = urlsplit(url)
    h = hashlib.sha256(url.encode()).hexdigest()[:8]
    return f"{parts.path} q_hash={h}"


async def make_nws_request(
    url: str,
    display_value: bool = True,
    method: str = "GET",
    json_data: Optional[dict[str, Any]] = None,
) -> dict[str, Any] | None:
    """Make a request to the ServiceNow API using OAuth 2.0 authentication.

    For GET requests, applies query encoding, default performance params
    (sysparm_no_count, sysparm_exclude_reference_link, sysparm_display_value),
    and display-value extraction.

    For non-GET requests (POST, PATCH, DELETE), bypasses read-only param
    injection and propagates ``httpx.HTTPStatusError`` +
    ``httpx.TimeoutException`` so callers can map them to domain-specific
    error messages.

    Wrap calls in ``anyio.fail_after()`` at the call site to enforce
    per-operation deadlines (e.g. ``anyio.fail_after(180.0)`` for KB publish).
    """
    if method == "GET":
        url = ensure_query_encoded(url)
        url = add_default_params(url, display_value)
        try:
            with anyio.fail_after(30.0):  # anyio cancel scope: sync ctx, async-compatible
                result = await make_oauth_request(url)
            return extract_display_values(result) if result and display_value else result
        except TimeoutError:
            print(f"[http_layer] GET request timed out for {_redact_url(url)}", file=sys.stderr)
            return None
        except Exception as e:  # noqa: BLE001
            # stderr only — stdout is reserved for the MCP JSON-RPC frame stream.
            print(f"[http_layer] GET request failed for {_redact_url(url)} ({type(e).__name__}): {e}", file=sys.stderr)
            return None

    # Write path: bypass read-only params + display flattening, raise
    # for status so callers can map HTTP errors to domain errors.
    # Callers wrap in anyio.fail_after() to enforce custom deadlines.
    client = get_oauth_client()
    return await client.make_authenticated_request(
        method, url, raise_for_status=True, json=json_data
    )


async def test_oauth_connection() -> dict[str, Any]:
    """Test OAuth connection and return status."""
    try:
        client = get_oauth_client()
        return await client.test_connection()
    except Exception as e:  # noqa: BLE001
        return {
            "status": "error",
            "message": f"OAuth configuration error: {e}",
            "oauth_available": False,
        }


def get_auth_info() -> dict[str, Any]:
    """Get information about current authentication method."""
    return {
        "oauth_enabled": True,
        "instance_url": SERVICENOW_INSTANCE,
        "auth_method": "oauth",
    }
