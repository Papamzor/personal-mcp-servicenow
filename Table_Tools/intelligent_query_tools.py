"""ServiceNow encoded-query operator reference (MCP tool).

v5.0 "Boron" (Tier 2): the five NL/filter tools this module used to expose —
`intelligent_search`, `explain_servicenow_filters`, `build_smart_servicenow_filter`,
`get_servicenow_filter_templates`, `get_query_examples` — were culled. The host
model builds and explains filters natively, and the regex NLP façade was
strictly dominated by `search_records` / `filter_records` (a parse-fail fell
back to the identical keyword LIKE, a partial parse to *worse* recall). Only the
operator reference survives, because CONTAINS-vs-LIKE is a real repo footgun
where a wrong operator silently returns zero rows.

The dead NL engine (`query_table_intelligently`, `filter/intelligence.py`) is
removed in the Tier 2.5 sweep.
"""

from typing import Any, Dict

from constants import SERVICENOW_QUERY_OPERATORS, QUERY_SYNTAX_NOTES

def get_query_syntax_help() -> Dict[str, Any]:
    """Return the authoritative ServiceNow encoded-query operator reference.

    SIDE EFFECT: none — returns a static reference.
    EXAMPLE: which encoded query operators does ServiceNow support.

    Use this BEFORE constructing a `sysparm_query` / filter value to avoid
    guessing operator syntax. Key gotcha: the substring/"contains" operator in
    encoded queries is **LIKE** (`fieldLIKEvalue`), NOT `CONTAINS` — `CONTAINS`
    is a GlideRecord scripting operator and is silently ignored in encoded
    queries (returns zero rows). Reference fields (assignment_group,
    assigned_to, caller_id, cmdb_ci, ...) store sys_ids: filter by sys_id or
    dot-walk (e.g. `assignment_group.nameLIKEFleet`).
    """
    return {
        "success": True,
        "notes": QUERY_SYNTAX_NOTES,
        "operators": SERVICENOW_QUERY_OPERATORS,
        "common_mistakes": [
            "Using CONTAINS in an encoded query — use LIKE instead.",
            "Filtering a reference field by display name — use a sys_id or dot-walk (field.name).",
            "Comma-separated priorities without OR — use priority=1^ORpriority=2 or priorityIN1,2.",
        ],
    }
