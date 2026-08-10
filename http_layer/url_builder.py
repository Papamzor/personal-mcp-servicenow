"""URL construction for ServiceNow read requests.

Owns the two read-path mutations every GET to the table API must apply:

1. URL-encoding the ``sysparm_query`` value while preserving the
   ServiceNow operator characters ``= < > ^ ( ) : @ !``.
2. Injecting the read-only performance parameters
   ``sysparm_display_value``, ``sysparm_exclude_reference_link``, and
   ``sysparm_no_count`` — the trio responsible for the v3 token-saving
   gains (per CLAUDE.md and the token-optimization invariant memory).

Write paths (POST/PATCH/DELETE) MUST NOT call these helpers — read-only
params on a write payload would mangle the request.

Why ``&`` left the safe-set in v4.4.1
------------------------------------
This encoder normalises the whole assembled query, so it cannot tell a value's
``&`` from an operator — and ``&`` is not an operator at all: encoded-query
syntax separates conditions with ``^``. Keeping it safe meant a value's ``&``,
however carefully escaped upstream, was decoded here and then passed through
raw, ending ``sysparm_query`` and turning the rest of the condition into a
sibling URL parameter. ``nameLIKESales & Marketing`` searched for "Sales " and
sent a stray ``Marketing`` parameter — a query BROADER than the one asked for.
Escaping it is correct in every case, since it is never structural.

The invariant that makes this compose with the producers
-------------------------------------------------------
``unquote`` before ``quote`` keeps this function idempotent, which matters
because ``query_table_with_filters`` encodes its assembled query and then
``make_nws_request`` encodes it again. Idempotency by decoding is only safe
while decoding cannot resurrect a structural character, and that holds by
construction: ``filter.value_encoding`` escapes caller values with the safe-set
here MINUS ``^``, so a producer never emits a ``%XY`` for a character this
function would leave raw, and it refuses ``^`` outright rather than escaping it.
Pinned by ``tests/test_query_value_encoding.py::
test_the_two_safe_sets_differ_only_by_the_caret``.

Flipping one side alone reopens the defect: producers that do not escape hand
this function raw structural characters, and putting ``&`` back here undoes the
escaping done by the ones that do.
"""
from __future__ import annotations

from urllib.parse import quote, unquote

#: Characters left unescaped in an assembled query: ServiceNow's operators.
#: ``&`` is deliberately NOT among them — see the module docstring. Values are
#: escaped by ``filter.value_encoding.encode_query_value`` using this set minus
#: ``^``, and the two must stay in that relationship.
QUERY_OPERATOR_SAFE = "=<>^():@!"


def encode_query_string(query: str) -> str:
    """Percent-encode an assembled encoded-query string for a URL.

    Idempotent: an already-encoded query is decoded first, so encoding twice is
    the same as encoding once. ``Table_Tools.generic_table_tools`` used to keep a
    near-copy of this with its own safe-set, so a value could pass through two
    encoders that disagreed and be round-trip-stable by luck; this is the single
    implementation both paths now share.
    """
    return quote(unquote(query), safe=QUERY_OPERATOR_SAFE)


def ensure_query_encoded(url: str) -> str:
    """Ensure ``sysparm_query`` value in URL is percent-encoded for ServiceNow.

    Idempotent: already-encoded URLs are unquoted first to prevent
    double-encoding. Preserves ServiceNow operators: ``= < > ^ ( ) : @ !``.

    The split on the first ``&`` is why a raw ``&`` inside a value cannot be
    rescued at this layer: by the time it arrives it is indistinguishable from
    the separator before ``sysparm_limit``, and everything after it has already
    become ``suffix``. Values are escaped at the producer instead, and dropping
    ``&`` from the safe-set is what stops this function undoing that.
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
    return f"{prefix}sysparm_query={encode_query_string(query_value)}{suffix}"


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
