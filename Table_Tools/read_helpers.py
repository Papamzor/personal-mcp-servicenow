"""Shared read-response helpers for the typed-read consumers (v4.4 Tier 0.3).

`http_layer` raises `ServiceNowRequestError` on a failed GET, and each consumer
maps it to `error.to_error_dict()`. Two shapes then travel back up through the
modules that re-wrap each other's responses:

    failure   {"error": {"code": ..., "message": ...}}
              No rows. The read did not happen — this is NOT "no records match".

    partial   {"result": [...], "partial": true, "error": {...}}
              Rows plus the reason the set is incomplete (a page after the first
              failed). The rows are real and must not be thrown away.

Every module that re-wraps another module's response has to keep both shapes
intact. Re-wrapping a failure as an empty result — "Found 0 records", "No
matching KB articles." — is exactly the mislabelling this tier removes, and it
is easy to reintroduce because the mistake reads as ordinary code.
"""
from typing import Any, Dict


def is_read_failure(response: Any) -> bool:
    """True when *response* is a read failure carrying no usable rows.

    A partial read (rows AND error) is deliberately not a failure: its rows are
    usable and the caller should keep them, marked incomplete.
    """
    return (
        isinstance(response, dict)
        and bool(response.get("error"))
        and not response.get("result")
    )


def carry_partial(response: Dict[str, Any], source: Any) -> Dict[str, Any]:
    """Propagate *source*'s partial-read marker onto *response*.

    Used wherever one response is re-wrapped into another, so an incomplete set
    is never presented as a complete one. No-op when *source* carries no error.
    """
    if isinstance(source, dict) and source.get("error"):
        response["partial"] = True
        response["error"] = source["error"]
    return response
