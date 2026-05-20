"""Response payload transformation for ServiceNow read responses.

When ``sysparm_display_value=true`` is set, ServiceNow returns each
field as a ``{"display_value": str, "value": str}`` envelope. The LLM
only consumes the display value, so the envelope is flattened to its
display string here. This is half of the v3 token-saving story — the
other half is the query-string params in ``url_builder.py``.

Write paths MUST NOT pass their responses through these helpers — the
write response shape (``{"result": {...record fields...}}``) is
different and contains no display-value envelope to flatten.
"""
from __future__ import annotations

from typing import Any, Dict


def extract_field_value(value: Any) -> Any:
    """Extract the display value if available, otherwise return the raw value."""
    if isinstance(value, dict) and "display_value" in value:
        return value["display_value"]
    return value


def process_item_dict(item: dict) -> dict:
    """Process a single record dict and flatten its display-value envelopes."""
    return {key: extract_field_value(value) for key, value in item.items()}


def extract_display_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """Walk a ServiceNow list response and flatten every row's envelopes."""
    if not isinstance(data, dict):
        return data
    if "result" not in data or not isinstance(data["result"], list):
        return data

    data["result"] = [
        process_item_dict(item) if isinstance(item, dict) else item
        for item in data["result"]
    ]
    return data
