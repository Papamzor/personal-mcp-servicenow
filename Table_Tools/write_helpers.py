"""Shared helpers for ServiceNow write-path responses (KB + VTB CRUD).

Both write subsystems map HTTP status codes to localized error strings and
unwrap the single-record result envelope. The mechanism is identical; only
the message tables (and KB's response-field filter) differ, so the caller
passes those in. Centralizing the mechanism means the detail-extraction and
unwrap logic live in one place instead of being duplicated per subsystem.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

import httpx
import structlog

_log = structlog.get_logger("write")


def _extract_error_detail(error: httpx.HTTPStatusError) -> Any:
    """Best-effort response body (JSON, else text) for error messages."""
    try:
        return error.response.json()
    except Exception:
        return error.response.text


def map_http_error(
    error: httpx.HTTPStatusError,
    error_map: Dict[int, str],
    default: str,
    *,
    detail_codes: Iterable[int] = (),
    detail_on_default: bool = False,
) -> str:
    """Map an HTTPStatusError to a localized message.

    error_map: {status_code: message}; ``default`` is used for unmapped codes.
    detail_codes / detail_on_default: for those codes, the response body is
        logged server-side (structlog, stderr) for debugging — it is never
        included in the returned string, which stays the stable base message
        so ServiceNow internals (response bodies, stack traces, ACL hints)
        never reach the MCP client.
    """
    status = error.response.status_code
    base = error_map.get(status, default)
    is_default = status not in error_map
    if status in set(detail_codes) or (is_default and detail_on_default):
        _log.error("write_http_error", status=status, detail=_extract_error_detail(error))
    return base


def unwrap_write_response(
    result: Any,
    unconfirmed_message: str,
    *,
    fields: Optional[Iterable[str]] = None,
) -> Dict[str, Any] | str:
    """Extract the single-record payload from a write response.

    fields: when given, filter a dict record down to these keys (KB write).
    unconfirmed_message: returned when the response carried no record.

    An empty response is UNCONFIRMED, not successful (v4.4 Tier 0.3). This
    previously returned a message reading "<operation> successful but no data
    returned" — it asserted the write had landed on the strength of an empty
    response, which is the one thing an empty response cannot establish. #59
    fixed the transport half (a failed write now raises instead of returning
    None), so a falsy value reaching here means ServiceNow answered 2xx with no
    record: real, rare, and not a success.
    """
    if result and isinstance(result, dict) and result.get("result"):
        record = result["result"]
        if fields is not None and isinstance(record, dict):
            allowed = set(fields)
            return {k: v for k, v in record.items() if k in allowed}
        return record
    return result if result else unconfirmed_message
