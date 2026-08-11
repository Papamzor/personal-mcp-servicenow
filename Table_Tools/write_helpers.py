"""Shared helpers for ServiceNow write-path responses (KB + VTB CRUD).

Both write subsystems map HTTP status codes to localized error messages and
unwrap the single-record result envelope. The mechanism is identical; only
the message tables (and KB's response-field filter) differ, so the caller
passes those in. Centralizing the mechanism means the detail-extraction and
unwrap logic live in one place instead of being duplicated per subsystem.

Response contract (v5.0 "Boron" Tier 3.1). Both helpers now return the §3.1
shapes from `Table_Tools/response.py`, never a bare string:

  * `map_http_error` → `error_response(code, message)`. The status→code map
    (401→AUTH, 403→FORBIDDEN, 400→VALIDATION, 404→NOT_FOUND, 408→TIMEOUT, else
    HTTP) is the write-path twin of `http_layer.errors.classify_read_failure`;
    the localized message table the caller passes is unchanged.
  * `unwrap_write_response` → `record_response(record, message=...)` on a
    confirmed single-record write, and `error_response("INTERNAL", ...)` for the
    UNCONFIRMED case (2xx with no record body). Unconfirmed is not success
    (v4.4 Tier 0.3): an empty response cannot establish that the write landed,
    so it must not read as one.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

import httpx
import structlog

from .response import error_response, record_response

_log = structlog.get_logger("write")

# Write-path status→code map — the twin of classify_read_failure for the codes a
# write can surface. Unmapped statuses fall to HTTP.
_STATUS_TO_CODE = {
    400: "VALIDATION",
    401: "AUTH",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    408: "TIMEOUT",
}


def _status_to_code(status: int) -> str:
    return _STATUS_TO_CODE.get(status, "HTTP")


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
) -> Dict[str, Any]:
    """Map an HTTPStatusError to a `{"error": {"code", "message"}}` dict.

    error_map: {status_code: message}; ``default`` is used for unmapped codes.
    The code comes from the status (see `_status_to_code`); the message is the
    localized base text from the caller's table.

    detail_codes / detail_on_default: for those codes, the response body is
        logged server-side (structlog, stderr) for debugging — it is never
        included in the returned message, which stays the stable base text
        so ServiceNow internals (response bodies, stack traces, ACL hints)
        never reach the MCP client.
    """
    status = error.response.status_code
    base = error_map.get(status, default)
    is_default = status not in error_map
    if status in set(detail_codes) or (is_default and detail_on_default):
        _log.error("write_http_error", status=status, detail=_extract_error_detail(error))
    return error_response(_status_to_code(status), base)


def unwrap_write_response(
    result: Any,
    unconfirmed_message: str,
    *,
    fields: Optional[Iterable[str]] = None,
    success_message: Optional[str] = None,
) -> Dict[str, Any]:
    """Extract the single-record write payload into the §3.1 write shape.

    Confirmed write → `record_response(record, message=success_message)`
    (`{"record": {...}, "message": ...}`). `fields`, when given, filters the
    record down to those keys (KB write).

    An empty response is UNCONFIRMED, not successful (v4.4 Tier 0.3), so it maps
    to `error_response("INTERNAL", unconfirmed_message)`. This previously
    returned a message reading "<operation> successful but no data returned" — it
    asserted the write had landed on the strength of an empty response, which is
    the one thing an empty response cannot establish. #59 fixed the transport
    half (a failed write now raises instead of returning None), so a falsy value
    reaching here means ServiceNow answered 2xx with no record: real, rare, and
    not a success.
    """
    if result and isinstance(result, dict) and result.get("result"):
        record = result["result"]
        if fields is not None and isinstance(record, dict):
            allowed = set(fields)
            record = {k: v for k, v in record.items() if k in allowed}
        return record_response(record, message=success_message)
    return error_response("INTERNAL", unconfirmed_message)
