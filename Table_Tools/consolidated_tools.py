"""
Consolidated tools with unique logic that cannot be replaced by generic wrappers.

Kept:
- Priority incidents (complex date logic, metadata)
- Knowledge-specific tools (category/kb_base filtering, active articles)
- SLA tools (each has specialised query patterns)
- Helper functions used by the above
"""

import logging
from datetime import datetime, timezone
from .generic_table_tools import (
    query_table_with_filters,
    get_records_by_priority,
    TableFilterParams
)
from .read_helpers import carry_partial, carry_partial_after_filter, is_read_failure
from .response import error_response, list_response
from .date_utils import (
    validate_date_format,
    build_date_filter,
    build_last_n_days_filter,
)
from typing import Any, Dict, Optional, List, Set
from constants import (
    TABLE_ERROR_MESSAGES,
    TASK_NUMBER_FIELD,
    KB_STATE_SCAN_LIMIT,
    KB_STATE_SCAN_WARNING,
)
from param_coercion import OptJsonList, OptJsonDict

# v5.0 "Boron" Tier 3.3: get_priority_incidents dropped its **deprecated_kwargs
# backwards-compat path (deprecated since v4.0). Extra field filters go through
# `additional_filters` now; the hand-rolled _mcp_get_priority_incidents shim in
# tools.py (which only existed because fastmcp rejects **kwargs) is gone with it.

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
        return error_response("VALIDATION", f"Invalid {param_name}: {error}")
    return None

def _merge_filters(
    additional_filters: Optional[Dict[str, Any]],
    start_date: Optional[str],
    end_date: Optional[str]
) -> Dict[str, Any]:
    """Merge additional filters and the date window into one filter dict."""
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

    # List-contract shape (result + returned_count + truncated); the descriptive
    # block stays under `metadata` (nested, not a top-level message dialect).
    return list_response(
        records,
        truncated=bool(result.get("truncated", False)),
        metadata={
            "count": record_count,
            "priorities_queried": priorities,
            "date_range": date_range,
            "filters_applied": additional_filters,
            "query_timestamp": query_timestamp,
            "message": _build_priority_result_message(
                record_count, priorities, start_date, end_date
            ),
        },
    )

async def get_priority_incidents(
    priorities: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    additional_filters: OptJsonDict = None,
    include_metadata: bool = False,
) -> Dict[str, Any]:
    """
    Get incidents filtered by priority value, with an optional date window.

    TABLES: incident only.
    SIDE EFFECT: read-only.
    EXAMPLE: show me all P1 incidents from last week.

    Uses simple >= / <= date operators (not JavaScript date functions) for
    reliability.

    Args:
        priorities: Priority values, e.g. ["1","2"] or ["P1","P2"]
        start_date: Optional "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
        end_date: Optional, same formats as start_date
        additional_filters: Optional dict of extra field filters
        include_metadata: If True, include a metadata block in the response

    Returns:
        Dict with "result" list (+ "metadata" when include_metadata=True)
    """
    query_timestamp = datetime.now(timezone.utc).isoformat()

    # Validate date formats if provided
    for date_val, name in [(start_date, "start_date"), (end_date, "end_date")]:
        error_result = _validate_date_param(date_val, name)
        if error_result:
            return error_result

    # Build merged filters
    merged_filters = _merge_filters(additional_filters, start_date, end_date)

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

    # A failed read has no rows to count. Wrapping it in metadata would report
    # "Found 0 priority 1 incident(s)" for a timeout, which is the not-found
    # mislabelling v4.4 Tier 0.3 exists to remove.
    if is_read_failure(result):
        return result

    enriched = _build_metadata(
        result, priorities, start_date, end_date, additional_filters, query_timestamp
    )
    return carry_partial(enriched, result)

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

# ---------------------------------------------------------------------------
# Knowledge-specific tools (unique params / logic)
# ---------------------------------------------------------------------------

# v5.0 "Boron" (Tier 2): similar_knowledge_for_text, get_knowledge_by_category
# and get_active_knowledge_articles were culled. Replacements:
#   similar_knowledge_for_text  -> search_records("kb_knowledge", text)
#   get_knowledge_by_category   -> filter_records("kb_knowledge", {"kb_category": ...})
#   get_active_knowledge_articles -> get_kb_articles_by_state("published")
# The old "smart" KB search silently discarded input_text when category/kb_base
# was set; do not reintroduce it (plan §Tier 2).

# Canonical workflow_state precedence for KB de-duplication.
# Lower index = higher priority (= the row chosen as "current" when one number has multiple versions).
# Rationale: published reflects live content; draft/review are in-flight; outdated is a versioning
# artefact left behind by ServiceNow when a newer version publishes; retired = explicitly killed.
_KB_STATE_PRIORITY = ["published", "draft", "review", "outdated", "retired"]
_KB_STATE_RANK = {state: idx for idx, state in enumerate(_KB_STATE_PRIORITY)}
_KB_DEDUP_FIELDS = [
    "number", "sys_id", "short_description", "workflow_state",
    "kb_category", "sys_updated_on",
]

def _pick_canonical_kb_row(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """De-duplicate kb_knowledge rows by `number`, keeping the highest-priority workflow_state row.

    Returns a dict keyed by number with {row, rank, version_count, states}.

    `states` — every distinct workflow_state seen for that number — is what makes
    a draft on an already-published article discoverable. Collapsing to the
    priority winner alone hid 47 of one KB's 48 pending drafts (see
    tests/test_kb_state_rollup.py): re-drafting an update leaves a `published`
    row beside the `draft` one, and `published` outranks it.
    """
    by_number: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        num = row.get("number")
        if not num:
            continue
        state = (row.get("workflow_state") or "").strip().lower()
        rank = _KB_STATE_RANK.get(state, len(_KB_STATE_PRIORITY))
        entry = by_number.get(num)
        if entry is None:
            by_number[num] = {
                "row": row, "rank": rank, "version_count": 1, "states": {state},
            }
        else:
            entry["version_count"] += 1
            entry["states"].add(state)
            if rank < entry["rank"]:
                entry["row"] = row
                entry["rank"] = rank
    return by_number

def _order_states(states: Set[str]) -> List[str]:
    """Distinct states in priority order (unknown states last, alphabetical)."""
    return sorted(
        states, key=lambda s: (_KB_STATE_RANK.get(s, len(_KB_STATE_PRIORITY)), s)
    )

def _format_deduped_kb_row(number: str, info: Dict[str, Any]) -> Dict[str, Any]:
    """Render a de-duplicated KB row in the public response shape."""
    row = info["row"]
    return {
        "number": number,
        "sys_id": row.get("sys_id"),
        "short_description": row.get("short_description"),
        "current_state": (row.get("workflow_state") or "").strip().lower(),
        "states_present": _order_states(info["states"]),
        "version_count": info["version_count"],
        "kb_category": row.get("kb_category"),
        "sys_updated_on": row.get("sys_updated_on"),
    }

async def get_kb_articles_by_state(
    workflow_state: Optional[str] = None,
    category: Optional[str] = None,
    kb_base: Optional[str] = None,
    max_results: int = 100,
) -> Dict[str, Any]:
    """List kb_knowledge articles de-duplicated by article number.

    TABLES: kb_knowledge only.
    SIDE EFFECT: read-only.
    EXAMPLE: which knowledge articles are currently in published state.

    ServiceNow KB versioning surfaces one article number across several
    workflow states (publish creates a new sys_id and marks the prior row
    `outdated`). This collapses them to one entry per number:

      * `current_state`   — the highest-priority state found (the canonical /
        live view). Priority: published > draft > review > outdated > retired.
      * `states_present`  — EVERY distinct state found for that number.
      * `version_count`   — how many raw rows the number had.

    `workflow_state` filters on `states_present` MEMBERSHIP, not on
    `current_state`. Re-drafting an update leaves a `published` row beside the
    new `draft` one, so an equality test on the priority winner hid the draft
    entirely — live, that reported 1 pending draft where there were 48.
    Membership only ever widens the non-published states: `published` is rank 0,
    so `current_state == "published"` already implies membership.

    Args:
        workflow_state: Optional state filter — matches any article carrying
            that state in ANY of its versions (e.g. "draft" → articles with
            pending draft work, including already-published ones).
        category: Optional kb_category filter (server-side).
        kb_base: Optional kb_knowledge_base filter (server-side).
        max_results: Cap on the deduped entries RETURNED (1..1000, default 100).
            The raw scan is separate and always runs to KB_STATE_SCAN_LIMIT —
            capping the scan by this value used to corrupt `current_state`.

    Returns:
        {"result": [{"number","sys_id","short_description","current_state",
                     "states_present","version_count","kb_category",
                     "sys_updated_on"}, ...],
         "returned_count": N, "truncated": bool}
        `truncated` means the deduped output was capped at `max_results`.
        A capped raw scan instead adds `scan_incomplete: true` + `warning`,
        because then the reported states themselves may be wrong.
    """
    if not 1 <= max_results <= KB_STATE_SCAN_LIMIT:
        return error_response(
            "VALIDATION",
            f"max_results must be between 1 and {KB_STATE_SCAN_LIMIT}, got {max_results}.",
        )

    filters: Dict[str, str] = {}
    if category:
        filters["kb_category"] = category
    if kb_base:
        filters["kb_knowledge_base"] = kb_base

    # The scan ceiling, NOT max_results. Dedup over a partial row set reports the
    # wrong `current_state` (rows for one number are scattered across the
    # sys_created_on DESC sort), so the scan must not inherit an output cap.
    params = TableFilterParams(
        filters=filters or None,
        fields=_KB_DEDUP_FIELDS,
        max_results=KB_STATE_SCAN_LIMIT,
    )
    raw = await query_table_with_filters("kb_knowledge", params)
    # De-duplicating a failure would answer "No matching KB articles." for a
    # read that never happened. Pass the failure through untouched.
    if is_read_failure(raw):
        return raw
    rows = raw.get("result", []) or []

    by_number = _pick_canonical_kb_row(rows)

    target_state = workflow_state.strip().lower() if workflow_state else None
    matched = []
    for num, info in by_number.items():
        formatted = _format_deduped_kb_row(num, info)
        # Membership, not equality against the priority winner — see the docstring.
        if target_state and target_state not in formatted["states_present"]:
            continue
        matched.append(formatted)

    deduped = matched[:max_results]
    extra: Dict[str, Any] = {}
    if raw.get("truncated"):
        # Loud, not just a bool: a caller spot-checking a few fields must not read
        # a poisoned state as authoritative.
        extra["scan_incomplete"] = True
        extra["warning"] = KB_STATE_SCAN_WARNING.format(limit=KB_STATE_SCAN_LIMIT)

    response = list_response(
        deduped, truncated=len(matched) > len(deduped), **extra
    )

    # Dedup + the workflow_state filter can empty a partial set. Answering
    # "No matching KB articles." from pages that never arrived would be the same
    # confident-wrong answer this tier removes, so that case reports the failure.
    if not deduped:
        return carry_partial_after_filter(response, raw)

    return carry_partial(response, raw)

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

# v5.0 "Boron" (Tier 2): similar_slas_for_text was culled. It queried a bare
# short_description that task_sla lacks, so ServiceNow dropped the condition and
# returned an arbitrary page of SLAs — it never worked. For a free-text task
# search use filter_records("task_sla", {"task.short_description": "LIKE..."}).

async def get_sla_details(sla_sys_id: str) -> Dict[str, Any]:
    """Get one SLA record by its sys_id (task_sla lookup).

    TABLES: task_sla only.
    SIDE EFFECT: read-only.
    EXAMPLE: get SLA sys_id 26bc0f3b47c1... .

    Routes via a `sys_id=` filter. (A prior version used `number=`, which
    task_sla lacks, so ServiceNow silently returned the default 10,000-row
    page (~1.2M tokens); the sys_id lookup returns the single ~69-token row.)
    """
    params = TableFilterParams(filters={"sys_id": sla_sys_id})
    return await query_table_with_filters("task_sla", params)

async def query_slas_by_task(task_number: str) -> Dict[str, Any]:
    """Get every SLA record attached to one task, addressed by task number.

    TABLES: task_sla (filters on the task reference).
    SIDE EFFECT: read-only.
    EXAMPLE: all SLA records attached to INC0012345.
    """
    params = TableFilterParams(filters={TASK_NUMBER_FIELD: task_number})
    return await query_table_with_filters("task_sla", params)

async def query_slas_by_status(
    status: str,
    days: Optional[int] = None,
    threshold_minutes: Optional[int] = None,
    stage: Optional[str] = None,
    extra_filters: OptJsonDict = None,
) -> Dict[str, Any]:
    """Query SLA records by a named status preset.

    TABLES: task_sla only.
    SIDE EFFECT: read-only.
    EXAMPLE: which SLAs are breached.

    Args:
        status: one of:
            - active:      currently active SLAs.
            - breached:    already-breached SLAs; `days` widens the
                           sys_created_on window (default 7).
            - breaching:   active SLAs breaching within `threshold_minutes`
                           (default 60).
            - critical:    P1/P2 active SLAs >80% consumed; curated 7-field view.
            - by_stage:    filter by `stage` (requires the `stage` arg).
            - performance: last-N-days metrics, curated 11-field view (default 30d).
        extra_filters: optional dict merged on top of the preset's filters.

    Returns:
        Dict shaped like the v3 SLA tools (`{"result": [...]}`).
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
    fields: OptJsonList = None,
    days: Optional[int] = None,
) -> Dict[str, Any]:
    """Custom SLA query — escape hatch for filter shapes the presets do not cover.

    TABLES: task_sla only.
    SIDE EFFECT: read-only.
    EXAMPLE: SLA query with a filter shape the presets do not cover.

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
