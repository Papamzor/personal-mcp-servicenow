"""
Consolidated tools with unique logic that cannot be replaced by generic wrappers.

Kept:
- Priority incidents (complex date logic, metadata, convenience helpers)
- Knowledge-specific tools (category/kb_base filtering, active articles)
- SLA tools (each has specialised query patterns)
- Helper functions used by the above
"""

import logging
from datetime import datetime, timezone
from .generic_table_tools import (
    query_table_by_text,
    get_record_details,
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


# ---------------------------------------------------------------------------
# Priority Incidents (unique date logic + metadata)
# ---------------------------------------------------------------------------

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
    """Get priority incidents for the current calendar month."""
    start_date, end_date = get_current_month_range()
    return await get_priority_incidents(
        priorities, start_date=start_date, end_date=end_date,
        additional_filters=additional_filters, include_metadata=include_metadata
    )


async def get_priority_incidents_last_n_days(
    priorities: List[str],
    days: int = 7,
    additional_filters: Optional[Dict[str, Any]] = None,
    include_metadata: bool = False
) -> Dict[str, Any]:
    """Get priority incidents from the last N days (including today)."""
    start_date, end_date = get_last_n_days_range(days)
    return await get_priority_incidents(
        priorities, start_date=start_date, end_date=end_date,
        additional_filters=additional_filters, include_metadata=include_metadata
    )


async def get_priority_incidents_this_week(
    priorities: List[str],
    additional_filters: Optional[Dict[str, Any]] = None,
    include_metadata: bool = False
) -> Dict[str, Any]:
    """Get priority incidents for the current week (Monday to Sunday)."""
    start_date, end_date = get_this_week_range()
    return await get_priority_incidents(
        priorities, start_date=start_date, end_date=end_date,
        additional_filters=additional_filters, include_metadata=include_metadata
    )


async def get_priority_incidents_yesterday(
    priorities: List[str],
    additional_filters: Optional[Dict[str, Any]] = None,
    include_metadata: bool = False
) -> Dict[str, Any]:
    """Get priority incidents from yesterday only."""
    start_date, end_date = get_yesterday_range()
    return await get_priority_incidents(
        priorities, start_date=start_date, end_date=end_date,
        additional_filters=additional_filters, include_metadata=include_metadata
    )


async def get_priority_incidents_today(
    priorities: List[str],
    additional_filters: Optional[Dict[str, Any]] = None,
    include_metadata: bool = False
) -> Dict[str, Any]:
    """Get priority incidents from today."""
    start_date, end_date = get_today_range()
    return await get_priority_incidents(
        priorities, start_date=start_date, end_date=end_date,
        additional_filters=additional_filters, include_metadata=include_metadata
    )


# ---------------------------------------------------------------------------
# Knowledge-specific tools (unique params / logic)
# ---------------------------------------------------------------------------

async def similar_knowledge_for_text(input_text: str, kb_base: Optional[str] = None, category: Optional[str] = None) -> Dict[str, Any]:
    """Find knowledge articles based on input text."""
    if category or kb_base:
        filters = {}
        if category:
            filters["kb_category"] = category
        if kb_base:
            filters["kb_knowledge_base"] = kb_base
        return await query_table_with_generic_filters("kb_knowledge", filters)

    return await query_table_by_text("kb_knowledge", input_text)

async def get_knowledge_by_category(category: str, kb_base: Optional[str] = None) -> Dict[str, Any]:
    """Get knowledge articles by category."""
    filters = {"kb_category": category}
    if kb_base:
        filters["kb_knowledge_base"] = kb_base
    return await query_table_with_generic_filters("kb_knowledge", filters)

async def get_active_knowledge_articles(input_text: str) -> Dict[str, Any]:  # noqa: ARG001
    """Get active knowledge articles matching text."""
    filters = {"state": "published"}
    return await query_table_with_generic_filters("kb_knowledge", filters)


# ---------------------------------------------------------------------------
# SLA tools (each has specialised query patterns)
# ---------------------------------------------------------------------------

async def similar_slas_for_text(input_text: str) -> Dict[str, Any]:
    """Find SLAs based on input text (searches related task descriptions)."""
    return await query_table_by_text("task_sla", input_text)

async def get_slas_for_task(task_number: str) -> Dict[str, Any]:
    """Get all SLA records for a specific task."""
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
        "business_time_left": f"<{time_threshold_minutes * 60}",
        "has_breached": "false"
    }
    params = TableFilterParams(filters=filters, fields=None)
    return await query_table_with_filters("task_sla", params)

async def get_breached_slas(filters: Optional[Dict[str, str]] = None, days: int = 7) -> Dict[str, Any]:
    """Get SLAs that have already breached (defaults to last 7 days)."""
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
    """Get SLA performance metrics (defaults to last 30 days)."""
    default_filters = {
        "sys_created_on": build_last_n_days_filter(days)
    }
    if filters:
        default_filters.update(filters)

    fields = [
        TASK_NUMBER_FIELD, "task.short_description", "sla.name", "stage",
        "business_percentage", "active", "has_breached", "breach_time",
        "business_time_left", "duration", "sys_created_on"
    ]
    params = TableFilterParams(filters=default_filters, fields=fields)
    return await query_table_with_filters("task_sla", params)

async def get_recent_breached_slas(days: int = 1) -> Dict[str, Any]:
    """Get recently breached SLAs (default last 24 hours)."""
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
        "task.priority": "IN1,2",
        "business_percentage": ">80"
    }
    fields = [
        TASK_NUMBER_FIELD, "task.priority", "sla.name", "stage",
        "business_percentage", "business_time_left", "has_breached"
    ]
    params = TableFilterParams(filters=filters, fields=fields)
    return await query_table_with_filters("task_sla", params)
