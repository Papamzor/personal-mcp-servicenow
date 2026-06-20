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
    detail_codes / detail_on_default: append the response body to the message
        for those codes (KB writes want this for debuggable 400 / 5xx errors).
    """
    status = error.response.status_code
    base = error_map.get(status, default)
    is_default = status not in error_map
    if status in set(detail_codes) or (is_default and detail_on_default):
        return f"{base}: {_extract_error_detail(error)}"
    return base


def unwrap_write_response(
    result: Any,
    success_message: str,
    *,
    fields: Optional[Iterable[str]] = None,
) -> Dict[str, Any] | str:
    """Extract the single-record payload from a write response.

    fields: when given, filter a dict record down to these keys (KB write).
    success_message: returned when the response carried no data.
    """
    if result and isinstance(result, dict) and result.get("result"):
        record = result["result"]
        if fields is not None and isinstance(record, dict):
            allowed = set(fields)
            return {k: v for k, v in record.items() if k in allowed}
        return record
    return result if result else success_message
