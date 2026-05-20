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
    filters = {"workflow_state": "published"}
    return await query_table_with_generic_filters("kb_knowledge", filters)


# ---------------------------------------------------------------------------
# SLA tools — v4.0 consolidation (10 -> 5)
# ---------------------------------------------------------------------------

SLA_STATUS_VALUES = ("active", "breached", "breaching", "critical", "by_stage", "performance")

# Curated field list for the critical-status dashboard view.
# Preserves the v3 token budget for this preset (~1,650 tokens / 24 rows).
_SLA_CRITICAL_FIELDS = [
    TASK_NUMBER_FIELD, "task.priority", "sla.name", "stage",
    "business_percentage", "business_time_left", "has_breached",
]

# Curated field list for the performance-summary view.
# Preserves the v3 token budget for this preset (~11,400 tokens / 100 rows).
_SLA_PERFORMANCE_FIELDS = [
    TASK_NUMBER_FIELD, "task.short_description", "sla.name", "stage",
    "business_percentage", "active", "has_breached", "breach_time",
    "business_time_left", "duration", "sys_created_on",
]


# Per-preset filter builders. Each returns (filters, fields_or_None).
# Extra filters and dispatch are handled by _build_sla_status_filter.

def _sla_filter_active(**_kw) -> tuple[Dict[str, str], Optional[List[str]]]:
    return {"active": "true"}, None


def _sla_filter_breached(days: Optional[int] = None, **_kw) -> tuple[Dict[str, str], Optional[List[str]]]:
    return {
        "has_breached": "true",
        "sys_created_on": build_last_n_days_filter(days if days is not None else 7),
    }, None


def _sla_filter_breaching(threshold_minutes: Optional[int] = None, **_kw) -> tuple[Dict[str, str], Optional[List[str]]]:
    threshold = (threshold_minutes if threshold_minutes is not None else 60) * 60
    return {
        "active": "true",
        "business_time_left": f"<{threshold}",
        "has_breached": "false",
    }, None


def _sla_filter_critical(**_kw) -> tuple[Dict[str, str], Optional[List[str]]]:
    return {
        "active": "true",
        "task.priority": "IN1,2",
        "business_percentage": ">80",
    }, _SLA_CRITICAL_FIELDS


def _sla_filter_by_stage(stage: Optional[str] = None, **_kw) -> tuple[Dict[str, str], Optional[List[str]]]:
    if not stage:
        raise ValueError("query_slas_by_status(status='by_stage') requires the 'stage' argument")
    return {"stage": stage}, None


def _sla_filter_performance(days: Optional[int] = None, **_kw) -> tuple[Dict[str, str], Optional[List[str]]]:
    return (
        {"sys_created_on": build_last_n_days_filter(days if days is not None else 30)},
        _SLA_PERFORMANCE_FIELDS,
    )


_SLA_STATUS_DISPATCH = {
    "active": _sla_filter_active,
    "breached": _sla_filter_breached,
    "breaching": _sla_filter_breaching,
    "critical": _sla_filter_critical,
    "by_stage": _sla_filter_by_stage,
    "performance": _sla_filter_performance,
}


def _build_sla_status_filter(
    status: str,
    days: Optional[int] = None,
    threshold_minutes: Optional[int] = None,
    stage: Optional[str] = None,
    extra_filters: Optional[Dict[str, str]] = None,
) -> tuple[Dict[str, str], Optional[List[str]]]:
    """Translate an SLA status preset into a (filter_dict, fields) pair."""
    handler = _SLA_STATUS_DISPATCH.get(status)
    if handler is None:
        raise ValueError(
            f"Unknown SLA status preset {status!r}. Valid values: {SLA_STATUS_VALUES}"
        )
    filters, fields = handler(days=days, threshold_minutes=threshold_minutes, stage=stage)
    if extra_filters:
        filters.update(extra_filters)
    return filters, fields


async def similar_slas_for_text(input_text: str) -> Dict[str, Any]:
    """Find SLAs whose related task descriptions match the given text."""
    return await query_table_by_text("task_sla", input_text)


async def get_sla_details(sla_sys_id: str) -> Dict[str, Any]:
    """Get a single SLA record by its sys_id.

    v4.0 routes via a `sys_id={sla_sys_id}` filter. v3.0 routed via
    `get_record_details("task_sla", sla_sys_id)` which built a
    `number={sla_sys_id}` filter — but the `task_sla` table has no
    `number` field, so the filter was silently ignored and the call
    returned the full default page (10,000 rows / ~1.2M tokens). The
    v4.0 lookup returns the single record (~69 tokens).
    """
    params = TableFilterParams(filters={"sys_id": sla_sys_id})
    return await query_table_with_filters("task_sla", params)


async def query_slas_by_task(task_number: str) -> Dict[str, Any]:
    """Get all SLA records attached to a given task number."""
    params = TableFilterParams(filters={TASK_NUMBER_FIELD: task_number})
    return await query_table_with_filters("task_sla", params)


async def query_slas_by_status(
    status: str,
    days: Optional[int] = None,
    threshold_minutes: Optional[int] = None,
    stage: Optional[str] = None,
    extra_filters: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Query SLA records by a named status preset.

    Args:
        status: one of "active", "breached", "breaching", "critical",
            "by_stage", "performance":
            - active:      currently active SLAs.
            - breached:    SLAs that have already breached. `days` widens the
                           sys_created_on window (default 7).
            - breaching:   active SLAs at risk of breaching within
                           `threshold_minutes` (default 60).
            - critical:    high-priority (P1/P2) active SLAs >80% consumed.
                           Returns a curated 7-field dashboard view.
            - by_stage:    filter by `stage` (e.g. "in_progress",
                           "completed"). Requires the `stage` argument.
            - performance: last-N-days SLA performance metrics with a curated
                           11-field view (default 30 days).
        extra_filters: optional dict merged on top of the preset's filters.

    Returns:
        Dict in the same shape as the v3 SLA tools (`{"result": [...]}`).
    """
    filters, fields = _build_sla_status_filter(
        status,
        days=days,
        threshold_minutes=threshold_minutes,
        stage=stage,
        extra_filters=extra_filters,
    )
    params = TableFilterParams(filters=filters, fields=fields)
    return await query_table_with_filters("task_sla", params)


async def query_slas_custom(
    filters: Dict[str, str],
    fields: Optional[List[str]] = None,
    days: Optional[int] = None,
) -> Dict[str, Any]:
    """Custom SLA query — escape hatch for filter shapes the presets do not cover.

    Args:
        filters: arbitrary ServiceNow filter dict (required).
        fields:  override returned columns. When None, the query layer falls
                 back to ESSENTIAL_FIELDS for `task_sla` — never returns all
                 columns by default, preserving the per-call token budget.
        days:    when provided, ANDs `sys_created_on=last N days` into the
                 filter dict.
    """
    final_filters = dict(filters)
    if days is not None:
        final_filters["sys_created_on"] = build_last_n_days_filter(days)
    params = TableFilterParams(filters=final_filters, fields=fields)
    return await query_table_with_filters("task_sla", params)
