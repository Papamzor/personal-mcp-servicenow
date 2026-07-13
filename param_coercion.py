"""
Param-boundary JSON coercion for MCP tool signatures.

LLM-driven MCP clients sometimes send optional/complex params as
*stringified JSON* (e.g. '["a","b"]' instead of ["a","b"]), and some
MCP clients double-encode flat top-level params — the raw value is a
JSON string of a JSON string (e.g. '"[\\"a\\",\\"b\\"]"'). Pydantic
(via FastMCP signature introspection) rejects these before the tool
runs. The BeforeValidator-backed aliases below transparently unwrap
repeated JSON-string layers and coerce a stringified (single- or
double-encoded) JSON list/dict to its native Python form at the param
boundary. Correct native lists/dicts pass through unchanged, and None
passes through unchanged so Optional[...] semantics are preserved.
"""

import json
from typing import Annotated, Any, Dict, List, Optional

from pydantic import BeforeValidator

_MAX_UNWRAP = 3


def _unwrap_json_str(v: Any) -> Any:
    """Peel repeated JSON-string layers (handles single- AND double-encoded input).
    Stops at the first non-str value or when a layer fails to parse."""
    for _ in range(_MAX_UNWRAP):
        if not isinstance(v, str):
            return v
        try:
            v = json.loads(v)
        except ValueError:  # json.JSONDecodeError is a subclass
            return v  # leave as-is; the type check below will raise
    return v


def coerce_json_list(v: Any) -> Any:
    """Coerce a (possibly double-encoded) stringified JSON array to a native list."""
    if v is None:
        return None
    v = _unwrap_json_str(v)
    if not isinstance(v, list):
        raise ValueError("expected a JSON array")
    return v


def coerce_json_dict(v: Any) -> Any:
    """Coerce a (possibly double-encoded) stringified JSON object to a native dict."""
    if v is None:
        return None
    v = _unwrap_json_str(v)
    if not isinstance(v, dict):
        raise ValueError("expected a JSON object")
    return v


JsonList = Annotated[List[str], BeforeValidator(coerce_json_list)]
OptJsonList = Annotated[Optional[List[str]], BeforeValidator(coerce_json_list)]
JsonDict = Annotated[Dict[str, Any], BeforeValidator(coerce_json_dict)]
OptJsonDict = Annotated[Optional[Dict[str, Any]], BeforeValidator(coerce_json_dict)]
