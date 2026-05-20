"""URL construction for ServiceNow read requests.

Owns the two read-path mutations every GET to the table API must apply:

1. URL-encoding the ``sysparm_query`` value while preserving the
   ServiceNow operator characters ``= < > & ^ ( ) : @ !``.
2. Injecting the read-only performance parameters
   ``sysparm_display_value``, ``sysparm_exclude_reference_link``, and
   ``sysparm_no_count`` — the trio responsible for the v3 token-saving
   gains (per CLAUDE.md and the token-optimization invariant memory).

Write paths (POST/PATCH/DELETE) MUST NOT call these helpers — read-only
params on a write payload would mangle the request.
"""
from __future__ import annotations

from urllib.parse import quote, unquote


def ensure_query_encoded(url: str) -> str:
    """Ensure ``sysparm_query`` value in URL is percent-encoded for ServiceNow.

    Idempotent: already-encoded URLs are unquoted first to prevent
    double-encoding. Preserves ServiceNow operators: ``= < > & ^ ( ) : @ !``.
    """
    if "sysparm_query=" not in url:
        return url
    prefix, rest = url.split("sysparm_query=", 1)
    if "&" in rest:
        query_value, suffix = rest.split("&", 1)
        suffix = "&" + suffix
    else:
        query_value = rest
        suffix = ""
    decoded_value = unquote(query_value)
    encoded_value = quote(decoded_value, safe="=<>&^():@!")
    return f"{prefix}sysparm_query={encoded_value}{suffix}"


def add_default_params(url: str, display_value: bool = True) -> str:
    """Add default performance and display parameters to a ServiceNow API URL.

    Token-optimization invariant: these three params materially reduce
    per-call token usage and must be present on every read request.
    """
    params = []
    if display_value and "sysparm_display_value" not in url:
        params.append("sysparm_display_value=true")
    if "sysparm_exclude_reference_link" not in url:
        params.append("sysparm_exclude_reference_link=true")
    if "sysparm_no_count" not in url:
        params.append("sysparm_no_count=true")
    if not params:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}{'&'.join(params)}"
