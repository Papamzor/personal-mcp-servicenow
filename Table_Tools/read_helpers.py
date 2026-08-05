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

    Used wherever one response is re-shaped into another without dropping rows,
    so an incomplete set is never presented as a complete one. No-op when
    *source* carries no error.

    If the re-wrap FILTERS rows out, use `carry_partial_after_filter` instead —
    an emptied-out partial must not keep its not-found message.
    """
    if isinstance(source, dict) and source.get("error"):
        response["partial"] = True
        response["error"] = source["error"]
    return response


def carry_partial_after_filter(response: Dict[str, Any], source: Any) -> Dict[str, Any]:
    """`carry_partial` for a response whose rows were filtered down.

    When the filter removes every row of a partial read, marking the result
    `partial` would ship a self-contradicting answer: a confident "no matching
    records" message next to an error saying the read never finished. The rows
    that would have matched may well be in the pages that failed, so the honest
    answer is the failure, not an empty set.
    """
    if isinstance(source, dict) and source.get("error") and not response.get("result"):
        return {"error": source["error"]}
    return carry_partial(response, source)
