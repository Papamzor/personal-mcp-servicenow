"""The minimal tool response contract (v5.0 "Boron", plan §3.1).

The target shapes for every tool. The discriminator is the presence of `error`;
there is no `success`/`ok` boolean and no bare-string return.

**Migration status:** the WHOLE registered surface is on this contract as of the
Tier 3.1-rest pass — generic reads (list_response / record_response), the
validation errors (`error_response("VALIDATION", ...)`), consolidated
priority/KB-state/SLA reads, and the write path (`write_helpers` →
record_response / error_response, no more bare strings). `tests/
test_tool_response_contract.py` drives every tool in `tools.tools` through the
real dispatcher and enforces the shapes below; it derives the tool set from
`tools.tools`, so a new tool with no case fails it by name.

Deliberate exceptions, pinned by that test:
  * `health_check` returns a diagnostic STATUS BAG — `error` may sit beside
    `connection`/`server`/`auth`. Not a data tool.
  * `publish_knowledge_article` fail-closed guard outcomes (duplicates found /
    inconclusive / unconfirmed) carry `success: False` and, when the confirming
    read fails, `error` beside status flags. The write itself may have landed.
  * the partial-page shape carries rows AND `error` together (see below).

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
