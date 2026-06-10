"""
Generic MCP tool wrappers that replace 24 table-specific 1-line functions.

Each function validates the table name against TABLE_CONFIGS and delegates
to the corresponding generic function in generic_table_tools.py.
"""

from typing import Any, Dict, List, Optional
from constants import TABLE_CONFIGS, ESSENTIAL_FIELDS, DETAIL_FIELDS
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


async def search_records(table: str, query: str) -> Dict[str, Any]:
    """Search records in a ServiceNow table by text similarity.

    Tokenises *query* into keywords and searches short_description.

    Supported tables: incident, change_request, sc_req_item, sc_task,
    universal_request, kb_knowledge, vtb_task, task_sla.

    Args:
        table: ServiceNow table name (e.g. "incident")
        query: Free-text search string

    Returns:
        {"result": [...], "message": "..."}
    """
    error = _validate_table(table)
    if error:
        return error
    return await query_table_by_text(table, query)


async def get_record_summary(table: str, number: str) -> Dict[str, Any]:
    """Get the short_description for a single record by its number.

    Supported tables: incident, change_request, sc_req_item, sc_task,
    universal_request, kb_knowledge, vtb_task, task_sla.

    Args:
        table: ServiceNow table name
        number: Record number (e.g. "INC0012345")

    Returns:
        {"result": [{"short_description": "..."}]}
    """
    error = _validate_table(table)
    if error:
        return error
    return await get_record_description(table, number)


async def get_record(table: str, number: str) -> Dict[str, Any]:
    """Get full detail fields for a single known record by number.

    Use this tool when you already know the record number and need complete
    field coverage (description, assigned_to, assignment_group, work_notes,
    comments, company, cmdb_ci, etc.). Returns all DETAIL_FIELDS for the
    table — significantly more fields than search_records or filter_records.

    TOKEN COST: Higher than filter_records (DETAIL_FIELDS vs ESSENTIAL_FIELDS).
    Do NOT use this for list views or when only basic fields are needed.
    Use filter_records for multi-record queries; use get_record only when
    full detail on one specific record is required.

    Supported tables: incident, change_request, sc_req_item, sc_task,
    universal_request, kb_knowledge, vtb_task, task_sla.

    Args:
        table: ServiceNow table name
        number: Record number (e.g. "CHG0054321")

    Returns:
        {"result": [{...all DETAIL_FIELDS for the table...}]}
    """
    error = _validate_table(table)
    if error:
        return error
    return await get_record_details(table, number)


async def find_similar(table: str, number: str) -> Dict[str, Any]:
    """Find records similar to an existing record (by short_description).

    Looks up the description of *number*, then searches the same table
    for records with similar text.

    Supported tables: incident, change_request, sc_req_item, sc_task,
    universal_request, kb_knowledge, vtb_task, task_sla.

    Args:
        table: ServiceNow table name
        number: Record number to find similarities for

    Returns:
        {"result": [...], "message": "..."}
    """
    error = _validate_table(table)
    if error:
        return error
    return await find_similar_records(table, number)


async def filter_records(
    table: str,
    filters: Dict[str, str],
    fields: Optional[List[str]] = None,
    max_results: int = 100,
) -> Dict[str, Any]:
    """Query a ServiceNow table with field-value filters.

    Supports operators via suffix (_gte, _lte, _gt, _lt), ServiceNow
    text operators (CONTAINS, LIKE, STARTSWITH, etc.), date ranges,
    priority lists, and OR filters.

    TOKEN COST: Low by default — returns only ESSENTIAL_FIELDS (number,
    short_description, priority, state, sys_created_on) unless you pass
    explicit fields. This is intentional for token budget efficiency on
    list queries. If you need full field coverage for a single known
    record, use get_record instead.

    Supported tables: incident, change_request, sc_req_item, sc_task,
    universal_request, kb_knowledge, vtb_task, task_sla.

    Args:
        table: ServiceNow table name
        filters: Dict of field-value filter pairs
        fields: Optional list of fields to return. Defaults to ESSENTIAL_FIELDS
            (basic fields only). Pass an explicit list for additional fields,
            or use get_record for the full DETAIL_FIELDS set on a single record.
        max_results: Hard cap on rows returned (default 100, max 1000). The
            response carries truncated=True when this cap is hit so callers
            can detect partial result sets.

    Returns:
        {"result": [...], "returned_count": N, "truncated": bool, "max_results": N}
    """
    error = _validate_table(table)
    if error:
        return error
    params = TableFilterParams(filters=filters, fields=fields, max_results=max_results)
    return await query_table_with_filters(table, params)
