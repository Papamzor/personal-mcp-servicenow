"""The minimal tool response contract (v5.0 "Boron", plan §3.1).

Every registered tool answers in exactly one of these shapes. The discriminator
is the presence of `error`; there is no `success`/`ok` boolean and no bare-string
return. Pinned across the whole surface by tests/test_tool_response_contract.py.

| case                  | shape                                                        |
|-----------------------|--------------------------------------------------------------|
| list success / empty  | {"result": [...], "returned_count": int, "truncated": bool}  |
| single-record success | {"record": {...}}  (never "result" for one record)           |
| single-record miss    | {"record": None}                                             |
| write success         | {"record": {...}, "message": str}                            |
| failure               | {"error": {"code": <one of ERROR_CODES>, "message": str}}    |
| partial page          | list shape + {"partial": true, "error": {...}}               |

Extra descriptive keys (e.g. `ci_type`, `search_criteria`) may accompany a
success shape; the forbidden things are a bare `str`, a `{"message": ...}`
success dialect parallel to `error`, and an `error` key inside a success.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# The seven-code vocabulary, identical to http_layer.errors.ALL_ERROR_CODES.
ERROR_CODES = frozenset(
    {"VALIDATION", "NOT_FOUND", "AUTH", "FORBIDDEN", "TIMEOUT", "HTTP", "INTERNAL"}
)


def error_response(code: str, message: str) -> Dict[str, Any]:
    """A failure: {"error": {"code", "message"}} and nothing else."""
    return {"error": {"code": code, "message": message}}


def list_response(
    rows: List[Dict[str, Any]], *, truncated: bool = False, **extra: Any
) -> Dict[str, Any]:
    """A list result. Empty is success (returned_count 0, no error)."""
    return {
        "result": rows,
        "returned_count": len(rows),
        "truncated": truncated,
        **extra,
    }


def record_response(
    record: Optional[Dict[str, Any]], *, message: Optional[str] = None, **extra: Any
) -> Dict[str, Any]:
    """A single record (read or write). `record` is None for a miss.

    `message` is only for the write case (§3.1 write success carries it); a
    read never adds a parallel message dialect.
    """
    out: Dict[str, Any] = {"record": record, **extra}
    if message is not None:
        out["message"] = message
    return out
