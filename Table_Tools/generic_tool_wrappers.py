"""
Generic MCP tool wrappers that replace 24 table-specific 1-line functions.

Each function validates the table name against TABLE_CONFIGS and delegates
to the corresponding generic function in generic_table_tools.py.
"""

from typing import Any, Dict, List, Optional
from constants import (
    TABLE_CONFIGS,
    ESSENTIAL_FIELDS,
    DETAIL_FIELDS,
    TABLES_WITHOUT_RECORD_IDENTITY,
    TABLE_LACKS_RECORD_IDENTITY,
)
from param_coercion import OptJsonList
from .generic_table_tools import (
    query_table_by_text,
    get_record_description,
    get_record_details,
    find_similar_records,
    query_table_with_filters,
    query_table_with_generic_filters,
    TableFilterParams,
)

SUPPORTED_TABLES = sorted(TABLE_CONFIGS.keys())
INVALID_TABLE_ERROR = "Invalid table '{table}'. Supported tables: {tables}"


def _validate_table(table: str) -> Optional[Dict[str, Any]]:
    """Return an error dict if *table* is not in TABLE_CONFIGS, else None."""
    if table not in TABLE_CONFIGS:
        return {"error": INVALID_TABLE_ERROR.format(table=table, tables=", ".join(SUPPORTED_TABLES))}
    return None


def _validate_identity_table(table: str) -> Optional[Dict[str, Any]]:
    """Table validation for the tools that address records by number or description.

    Rejects tables listed in TABLES_WITHOUT_RECORD_IDENTITY. Those tools build
    `number={x}` or `short_descriptionLIKE{x}` queries, and ServiceNow silently
    DROPS a condition on a field the table does not have — so the request
    succeeds and returns unrelated rows instead of failing. Refusing up front
    is the only way the caller learns the tool cannot do what was asked.

    `filter_records` deliberately keeps every table: the caller supplies the
    field names there, so nothing is assumed on their behalf.
    """
    error = _validate_table(table)
    if error:
        return error
    if table in TABLES_WITHOUT_RECORD_IDENTITY:
        return {"error": TABLE_LACKS_RECORD_IDENTITY.format(table=table)}
    return None


async def search_records(table: str, query: str) -> Dict[str, Any]:
    """Search records in a ServiceNow table by text similarity.

    Tokenises *query* into keywords and searches short_description.

    Supported tables: incident, change_request, sc_req_item, sc_task,
    universal_request, kb_knowledge, vtb_task. NOT task_sla — it has no
    short_description of its own; use similar_slas_for_text for SLA text search.

    Args:
        table: ServiceNow table name (e.g. "incident")
        query: Free-text search string

    Returns:
        {"result": [...], "message": "..."}
    """
    error = _validate_identity_table(table)
    if error:
        return error
    return await query_table_by_text(table, query)


async def get_record_summary(table: str, number: str) -> Dict[str, Any]:
    """Get the short_description for a single record by its number.

    Supported tables: incident, change_request, sc_req_item, sc_task,
    universal_request, kb_knowledge, vtb_task. NOT task_sla — that table has
    neither number nor short_description; use get_sla_details(sla_sys_id).

    Args:
        table: ServiceNow table name
        number: Record number (e.g. "INC0012345")

    Returns:
        {"result": [{"short_description": "..."}]}
    """
    error = _validate_identity_table(table)
    if error:
        return error
    return await get_record_description(table, number)


async def get_record(table: str, number: str) -> Dict[str, Any]:
    """Get full detail fields for a single known record by number.

    Use when you know the record number and need complete field coverage.
    Returns all DETAIL_FIELDS — more fields (and tokens) than search_records/
    filter_records, so prefer filter_records for list views and reserve
    get_record for full detail on one record.

    Tables: incident, change_request, sc_req_item, sc_task, universal_request,
    kb_knowledge, vtb_task. NOT task_sla — that table has no number field; use
    get_sla_details(sla_sys_id) or query_slas_by_task(task_number).

    Args:
        table: ServiceNow table name
        number: Record number (e.g. "CHG0054321")

    Returns:
        {"result": [{...all DETAIL_FIELDS...}]}
    """
    error = _validate_identity_table(table)
    if error:
        return error
    return await get_record_details(table, number)


async def find_similar(table: str, number: str) -> Dict[str, Any]:
    """Find records similar to an existing record (by short_description).

    Looks up the description of *number*, then searches the same table
    for records with similar text.

    Supported tables: incident, change_request, sc_req_item, sc_task,
    universal_request, kb_knowledge, vtb_task. NOT task_sla — it has neither
    number nor short_description; use similar_slas_for_text for SLA text search.

    Args:
        table: ServiceNow table name
        number: Record number to find similarities for

    Returns:
        {"result": [...], "message": "..."}
    """
    error = _validate_identity_table(table)
    if error:
        return error
    return await find_similar_records(table, number)


async def filter_records(
    table: str,
    filters: Dict[str, str],
    fields: OptJsonList = None,
    max_results: int = 100,
) -> Dict[str, Any]:
    """Query a ServiceNow table with field-value filters.

    Supports suffix operators (_gte, _lte, _gt, _lt), encoded-query text
    operators (LIKE, NOT LIKE, STARTSWITH, IN, ISEMPTY, BETWEEN, ...), date
    ranges, priority lists, and OR filters. Use LIKE (not CONTAINS) for
    substring matches. Reference fields (assignment_group, assigned_to, ...)
    hold sys_ids — filter by sys_id or dot-walk
    (assignment_group.nameLIKEFleet); a bare display value returns zero rows.
    See get_query_syntax_help for the full operator reference.

    TOKEN COST: low by default — returns ESSENTIAL_FIELDS only unless `fields`
    is given; use get_record for full detail on one record.

    Tables: incident, change_request, sc_req_item, sc_task, universal_request,
    kb_knowledge, vtb_task, task_sla. task_sla works here (unlike get_record /
    search_records) because you name the fields — use task, sla, stage, active,
    has_breached; there is no number or short_description column.

    Args:
        table: ServiceNow table name
        filters: Dict of field-value filter pairs
        fields: Fields to return; defaults to ESSENTIAL_FIELDS
        max_results: Row cap (default 100, max 1000); response sets
            truncated=True when the cap is hit

    Returns:
        {"result": [...], "returned_count": N, "truncated": bool, "max_results": N}
    """
    error = _validate_table(table)
    if error:
        return error
    if fields:
        allowed = set(DETAIL_FIELDS.get(table, []))
        bad = [f for f in fields if f not in allowed]
        if bad:
            return {"error": f"Unsupported field(s) for {table}: {', '.join(bad)}"}
    params = TableFilterParams(filters=filters, fields=fields, max_results=max_results)
    return await query_table_with_filters(table, params)
