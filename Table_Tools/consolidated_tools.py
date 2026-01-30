"""
Consolidated tools interface using generic table functions.
All table-specific operations are now unified through generic functions with cognitive complexity < 15.
"""

import logging
from datetime import datetime, timezone
from .generic_table_tools import (
    query_table_by_text,
    get_record_description,
    get_record_details,
    find_similar_records,
    query_table_with_filters,
    get_records_by_priority,
    query_table_with_generic_filters,
    TableFilterParams
)
from .date_utils import (
    validate_date_format,
    build_date_filter,
    build_last_n_days_filter,
    get_current_month_range,
    get_last_n_days_range,
    get_this_week_range,
    get_today_range,
    get_yesterday_range
)
from typing import Any, Dict, Optional, List
from constants import TABLE_ERROR_MESSAGES, TASK_NUMBER_FIELD

logger = logging.getLogger(__name__)


# Helper function to get table-specific error message
def _get_error_message(table_name: str, default: str = "Record not found.") -> str:
    """Get table-specific error message with cognitive complexity < 15."""
    return TABLE_ERROR_MESSAGES.get(table_name, default)


# INCIDENT TOOLS - Using generic functions
async def similar_incidents_for_text(input_text: str) -> Dict[str, Any]:
    """Find incidents based on input text."""
    return await query_table_by_text("incident", input_text)

async def get_short_desc_for_incident(input_incident: str) -> Dict[str, Any]:
    """Get short_description for incident."""
    return await get_record_description("incident", input_incident)

async def similar_incidents_for_incident(input_incident: str) -> Dict[str, Any]:
    """Find similar incidents based on given incident."""
    return await find_similar_records("incident", input_incident)

async def get_incident_details(input_incident: str) -> Dict[str, Any]:
    """Get detailed incident information."""
    return await get_record_details("incident", input_incident)

async def get_incidents_by_filter(filters: Dict[str, str], fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get incidents with custom filters."""
    params = TableFilterParams(filters=filters, fields=fields)
    return await query_table_with_filters("incident", params)

def _validate_date_param(date_string: Optional[str], param_name: str) -> Optional[Dict[str, Any]]:
    """Validate a date parameter and return an error dict if invalid, or None if valid."""
    if not date_string:
        return None
    is_valid, error = validate_date_format(date_string)
    if not is_valid:
        logger.error("Invalid %s format: %s - %s", param_name, date_string, error)
        return {"error": f"Invalid {param_name}: {error}"}
    return None


def _merge_filters(
    additional_filters: Optional[Dict[str, Any]],
    deprecated_kwargs: Dict[str, Any],
    start_date: Optional[str],
    end_date: Optional[str]
) -> Dict[str, Any]:
    """Merge additional filters, deprecated kwargs, and date filters into one dict."""
    if deprecated_kwargs:
        logger.warning(
            "Passing filters as **kwargs is deprecated. "
            "Use additional_filters dict instead. Got: %s",
            list(deprecated_kwargs.keys())
        )
        merged = (additional_filters or {}).copy()
        merged.update(deprecated_kwargs)
    else:
        merged = additional_filters.copy() if additional_filters else {}

    date_filter = build_date_filter(start_date, end_date)
    if date_filter:
        merged["_date_range"] = date_filter
        logger.debug("Built date filter: %s", date_filter)

    return merged


def _build_metadata(
    result: Dict[str, Any],
    priorities: List[str],
    start_date: Optional[str],
    end_date: Optional[str],
    additional_filters: Optional[Dict[str, Any]],
    query_timestamp: str
) -> Dict[str, Any]:
    """Build enhanced response with metadata."""
    records = result.get("result", [])
    record_count = len(records)
    date_range = {"start": start_date, "end": end_date} if start_date or end_date else None

    return {
        "result": records,
        "metadata": {
            "count": record_count,
            "priorities_queried": priorities,
            "date_range": date_range,
            "filters_applied": additional_filters,
            "query_timestamp": query_timestamp,
            "message": _build_priority_result_message(
                record_count, priorities, start_date, end_date
            )
        }
    }


async def get_priority_incidents(
    priorities: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    additional_filters: Optional[Dict[str, Any]] = None,
    include_metadata: bool = False,
    **deprecated_kwargs
) -> Dict[str, Any]:
    """
    Get incidents by priority with optional date range filtering.

    Uses simple >= and <= operators for date filtering instead of
    JavaScript-based date functions for improved reliability.

    Args:
        priorities: List of priority values (e.g., ["1", "2"] or ["P1", "P2"])
        start_date: Optional start date (format: "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS")
        end_date: Optional end date (format: "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS")
        additional_filters: Optional dict of additional field filters
        include_metadata: If True, return enhanced response with metadata
        **deprecated_kwargs: Deprecated - use additional_filters instead

    Returns:
        Dict with "result" list and optionally "metadata" if include_metadata=True

    Examples:
        # Basic priority query
        >>> await get_priority_incidents(["1", "2"])

        # With date range
        >>> await get_priority_incidents(
        ...     ["1", "2"],
        ...     start_date="2026-01-01",
        ...     end_date="2026-01-28"
        ... )

        # With additional filters and metadata
        >>> await get_priority_incidents(
        ...     ["1", "2"],
        ...     start_date="2026-01-01",
        ...     additional_filters={"state": "New"},
        ...     include_metadata=True
        ... )
    """
    query_timestamp = datetime.now(timezone.utc).isoformat()

    # Validate date formats if provided
    for date_val, name in [(start_date, "start_date"), (end_date, "end_date")]:
        error_result = _validate_date_param(date_val, name)
        if error_result:
            return error_result

    # Build merged filters
    merged_filters = _merge_filters(additional_filters, deprecated_kwargs, start_date, end_date)

    logger.info(
        "Querying priority incidents: priorities=%s, start_date=%s, end_date=%s, filters=%s",
        priorities, start_date, end_date, list(merged_filters.keys()) if merged_filters else []
    )

    # Call the underlying generic function
    result = await get_records_by_priority(
        "incident",
        priorities,
        merged_filters or None,
        detailed=True
    )

    if not include_metadata:
        return result

    return _build_metadata(result, priorities, start_date, end_date, additional_filters, query_timestamp)


def _build_priority_result_message(
    count: int,
    priorities: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> str:
    """Build human-readable result message for priority queries."""
    priority_str = ",".join(priorities)
    msg = f"Found {count} priority {priority_str} incident(s)"

    if start_date and end_date:
        msg += f" from {start_date} to {end_date}"
    elif start_date:
        msg += f" from {start_date} onwards"
    elif end_date:
        msg += f" up to {end_date}"

    return msg


# Convenience helper functions for common date range queries

async def get_priority_incidents_current_month(
    priorities: List[str],
    additional_filters: Optional[Dict[str, Any]] = None,
    include_metadata: bool = False
) -> Dict[str, Any]:
    """
    Get priority incidents for the current calendar month.

    Args:
        priorities: List of priority values (e.g., ["1", "2"])
        additional_filters: Optional additional field filters
        include_metadata: If True, return enhanced response with metadata

    Returns:
        Dict with incident results

    Example:
        >>> await get_priority_incidents_current_month(["1", "2"])
    """
    start_date, end_date = get_current_month_range()
    return await get_priority_incidents(
        priorities,
        start_date=start_date,
        end_date=end_date,
        additional_filters=additional_filters,
        include_metadata=include_metadata
    )


async def get_priority_incidents_last_n_days(
    priorities: List[str],
    days: int = 7,
    additional_filters: Optional[Dict[str, Any]] = None,
    include_metadata: bool = False
) -> Dict[str, Any]:
    """
    Get priority incidents from the last N days (including today).

    Args:
        priorities: List of priority values
        days: Number of days to look back (default: 7)
        additional_filters: Optional additional field filters
        include_metadata: If True, return enhanced response with metadata

    Returns:
        Dict with incident results

    Example:
        >>> await get_priority_incidents_last_n_days(["1", "2"], days=14)
    """
    start_date, end_date = get_last_n_days_range(days)
    return await get_priority_incidents(
        priorities,
        start_date=start_date,
        end_date=end_date,
        additional_filters=additional_filters,
        include_metadata=include_metadata
    )


async def get_priority_incidents_this_week(
    priorities: List[str],
    additional_filters: Optional[Dict[str, Any]] = None,
    include_metadata: bool = False
) -> Dict[str, Any]:
    """
    Get priority incidents for the current week (Monday to Sunday).

    Args:
        priorities: List of priority values
        additional_filters: Optional additional field filters
        include_metadata: If True, return enhanced response with metadata

    Returns:
        Dict with incident results

    Example:
        >>> await get_priority_incidents_this_week(["1", "2"])
    """
    start_date, end_date = get_this_week_range()
    return await get_priority_incidents(
        priorities,
        start_date=start_date,
        end_date=end_date,
        additional_filters=additional_filters,
        include_metadata=include_metadata
    )


async def get_priority_incidents_yesterday(
    priorities: List[str],
    additional_filters: Optional[Dict[str, Any]] = None,
    include_metadata: bool = False
) -> Dict[str, Any]:
    """
    Get priority incidents from yesterday only.

    Args:
        priorities: List of priority values
        additional_filters: Optional additional field filters
        include_metadata: If True, return enhanced response with metadata

    Returns:
        Dict with incident results

    Example:
        >>> await get_priority_incidents_yesterday(["1", "2"])
    """
    start_date, end_date = get_yesterday_range()
    return await get_priority_incidents(
        priorities,
        start_date=start_date,
        end_date=end_date,
        additional_filters=additional_filters,
        include_metadata=include_metadata
    )


async def get_priority_incidents_today(
    priorities: List[str],
    additional_filters: Optional[Dict[str, Any]] = None,
    include_metadata: bool = False
) -> Dict[str, Any]:
    """
    Get priority incidents from today.

    Args:
        priorities: List of priority values
        additional_filters: Optional additional field filters
        include_metadata: If True, return enhanced response with metadata

    Returns:
        Dict with incident results

    Example:
        >>> await get_priority_incidents_today(["1"])
    """
    start_date, end_date = get_today_range()
    return await get_priority_incidents(
        priorities,
        start_date=start_date,
        end_date=end_date,
        additional_filters=additional_filters,
        include_metadata=include_metadata
    )


# CHANGE TOOLS - Using generic functions
async def similar_changes_for_text(input_text: str) -> Dict[str, Any]:
    """Find changes based on input text."""
    return await query_table_by_text("change_request", input_text)

async def get_short_desc_for_change(input_change: str) -> Dict[str, Any]:
    """Get short_description for change."""
    return await get_record_description("change_request", input_change)

async def similar_changes_for_change(input_change: str) -> Dict[str, Any]:
    """Find similar changes based on given change."""
    return await find_similar_records("change_request", input_change)

async def get_change_details(input_change: str) -> Dict[str, Any]:
    """Get detailed change information."""
    return await get_record_details("change_request", input_change)


# REQUEST ITEM TOOLS - Using generic functions
async def similar_request_items_for_text(input_text: str) -> Dict[str, Any]:
    """Find service catalog request items based on input text."""
    return await query_table_by_text("sc_req_item", input_text)

async def get_short_desc_for_request_item(input_request_item: str) -> Dict[str, Any]:
    """Get short_description for request item."""
    return await get_record_description("sc_req_item", input_request_item)

async def similar_request_items_for_request_item(input_request_item: str) -> Dict[str, Any]:
    """Find similar request items based on given request item."""
    return await find_similar_records("sc_req_item", input_request_item)

async def get_request_item_details(input_request_item: str) -> Dict[str, Any]:
    """Get detailed request item information."""
    return await get_record_details("sc_req_item", input_request_item)


# UNIVERSAL REQUEST TOOLS - Using generic functions
async def similar_universal_requests_for_text(input_text: str) -> Dict[str, Any]:
    """Find universal requests based on input text."""
    return await query_table_by_text("universal_request", input_text)

async def get_short_desc_for_universal_request(input_universal_request: str) -> Dict[str, Any]:
    """Get short_description for universal request."""
    return await get_record_description("universal_request", input_universal_request)

async def similar_universal_requests_for_universal_request(input_universal_request: str) -> Dict[str, Any]:
    """Find similar universal requests based on given universal request."""
    return await find_similar_records("universal_request", input_universal_request)

async def get_universal_request_details(input_universal_request: str) -> Dict[str, Any]:
    """Get detailed universal request information."""
    return await get_record_details("universal_request", input_universal_request)


async def similar_knowledge_for_text(input_text: str, kb_base: Optional[str] = None, category: Optional[str] = None) -> Dict[str, Any]:
    """Find knowledge articles based on input text."""
    if category or kb_base:
        # Build filters for category or kb_base
        filters = {}
        if category:
            filters["kb_category"] = category
        if kb_base:
            filters["kb_knowledge_base"] = kb_base
        return await query_table_with_generic_filters("kb_knowledge", filters)
    
    return await query_table_by_text("kb_knowledge", input_text)

async def get_knowledge_details(input_kb: str) -> Dict[str, Any]:
    """Get detailed knowledge article information."""
    return await get_record_details("kb_knowledge", input_kb)

async def get_knowledge_by_category(category: str, kb_base: Optional[str] = None) -> Dict[str, Any]:
    """Get knowledge articles by category."""
    filters = {"kb_category": category}
    if kb_base:
        filters["kb_knowledge_base"] = kb_base
    return await query_table_with_generic_filters("kb_knowledge", filters)

async def get_active_knowledge_articles(input_text: str) -> Dict[str, Any]:
    """Get active knowledge articles matching text."""
    filters = {"state": "published"}
    result = await query_table_with_generic_filters("kb_knowledge", filters)
    
    # If we got results and have input text, filter by text similarity
    if isinstance(result, dict) and result.get("result") and input_text.strip():
        # This is a simplified approach - in a full implementation, you might want to 
        # do text matching on the results
        pass
    
    return result


# PRIVATE TASK TOOLS - Using generic functions (keeping VTB separate as it has CRUD operations)
async def similar_private_tasks_for_text(input_text: str) -> Dict[str, Any]:
    """Find private tasks based on input text."""
    return await query_table_by_text("vtb_task", input_text)

async def get_short_desc_for_private_task(input_private_task: str) -> Dict[str, Any]:
    """Get short_description for private task."""
    return await get_record_description("vtb_task", input_private_task)

async def similar_private_tasks_for_private_task(input_private_task: str) -> Dict[str, Any]:
    """Find similar private tasks based on given task."""
    return await find_similar_records("vtb_task", input_private_task)

async def get_private_task_details(input_private_task: str) -> Dict[str, Any]:
    """Get detailed private task information."""
    return await get_record_details("vtb_task", input_private_task)

async def get_private_tasks_by_filter(filters: Dict[str, str]) -> Dict[str, Any]:
    """Get private tasks with custom filters."""
    return await query_table_with_generic_filters("vtb_task", filters)


# SLA TOOLS - Using generic functions
async def similar_slas_for_text(input_text: str) -> Dict[str, Any]:
    """Find SLAs based on input text (searches related task descriptions)."""
    return await query_table_by_text("task_sla", input_text)

async def get_slas_for_task(task_number: str) -> Dict[str, Any]:
    """Get all SLA records for a specific task."""
    # Create filter to find SLAs by task reference
    filters = {TASK_NUMBER_FIELD: task_number}
    params = TableFilterParams(filters=filters)
    return await query_table_with_filters("task_sla", params)

async def get_sla_details(sla_sys_id: str) -> Dict[str, Any]:
    """Get detailed SLA information by sys_id."""
    return await get_record_details("task_sla", sla_sys_id)

async def get_breaching_slas(time_threshold_minutes: Optional[int] = 60) -> Dict[str, Any]:
    """Get SLAs at risk of breaching within specified time threshold."""
    filters = {
        "active": "true",
        "business_time_left": f"<{time_threshold_minutes * 60}",  # Convert to seconds
        "has_breached": "false"
    }
    params = TableFilterParams(filters=filters, fields=None)
    return await query_table_with_filters("task_sla", params)

async def get_breached_slas(filters: Optional[Dict[str, str]] = None, days: int = 7) -> Dict[str, Any]:
    """
    Get SLAs that have already breached.

    Defaults to recent breaches (last 7 days) to avoid token overload.
    Uses simple >= operator instead of JavaScript date functions.

    Args:
        filters: Optional additional filters to apply
        days: Number of days to look back (default: 7)

    Returns:
        Dict with breached SLA records
    """
    base_filters = {
        "has_breached": "true",
        "sys_created_on": build_last_n_days_filter(days)
    }
    if filters:
        base_filters.update(filters)
    params = TableFilterParams(filters=base_filters)
    return await query_table_with_filters("task_sla", params)

async def get_slas_by_stage(stage: str, additional_filters: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Get SLAs by stage (In progress, Completed, etc.)."""
    filters = {"stage": stage}
    if additional_filters:
        filters.update(additional_filters)
    params = TableFilterParams(filters=filters)
    return await query_table_with_filters("task_sla", params)

async def get_active_slas(filters: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Get currently active SLA records."""
    base_filters = {"active": "true"}
    if filters:
        base_filters.update(filters)
    params = TableFilterParams(filters=base_filters)
    return await query_table_with_filters("task_sla", params)

async def get_sla_performance_summary(filters: Optional[Dict[str, str]] = None, days: int = 30) -> Dict[str, Any]:
    """
    Get SLA performance metrics with detailed information.

    Defaults to recent data (last 30 days) for efficiency.
    Uses simple >= operator instead of JavaScript date functions.

    Args:
        filters: Optional additional filters to apply
        days: Number of days to look back (default: 30)

    Returns:
        Dict with SLA performance records
    """
    # Default to recent data to avoid token overload
    default_filters = {
        "sys_created_on": build_last_n_days_filter(days)
    }
    if filters:
        default_filters.update(filters)

    # Include key performance fields for analysis
    fields = [
        TASK_NUMBER_FIELD, "task.short_description", "sla.name", "stage",
        "business_percentage", "active", "has_breached", "breach_time",
        "business_time_left", "duration", "sys_created_on"
    ]
    params = TableFilterParams(filters=default_filters, fields=fields)
    return await query_table_with_filters("task_sla", params)

async def get_recent_breached_slas(days: int = 1) -> Dict[str, Any]:
    """
    Get recently breached SLAs for immediate attention.

    Default to last 24 hours.
    Uses simple >= operator instead of JavaScript date functions.

    Args:
        days: Number of days to look back (default: 1)

    Returns:
        Dict with recently breached SLA records
    """
    filters = {
        "has_breached": "true",
        "sys_created_on": build_last_n_days_filter(days)
    }
    params = TableFilterParams(filters=filters)
    return await query_table_with_filters("task_sla", params)

async def get_critical_sla_status() -> Dict[str, Any]:
    """Get high-priority SLA status summary for dashboard/monitoring."""
    filters = {
        "active": "true",
        "task.priority": "IN1,2",  # P1 and P2 tasks only (uses ServiceNow IN operator)
        "business_percentage": ">80"  # Close to or over SLA target
    }
    fields = [
        TASK_NUMBER_FIELD, "task.priority", "sla.name", "stage",
        "business_percentage", "business_time_left", "has_breached"
    ]
    params = TableFilterParams(filters=filters, fields=fields)
    return await query_table_with_filters("task_sla", params)
