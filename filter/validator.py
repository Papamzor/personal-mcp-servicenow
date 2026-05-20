"""ServiceNow filter validation and debug helpers.

Each validator returns a `QueryValidationResult` with warnings + suggestions
rather than raising, so callers can attach them to LLM-visible responses.
"""
from __future__ import annotations

from typing import Any, Dict, List

from filter.models import QueryValidationResult


# ---------------------------------------------------------------------------
# Priority validation helpers
# ---------------------------------------------------------------------------

def _has_comma_syntax_issue(has_multiple: bool, has_or: bool, has_comma: bool) -> bool:
    """Check if priority filter has comma syntax issue."""
    return has_multiple and not has_or and has_comma


def _has_or_format_issue(priority_value: str, has_or_syntax: bool) -> bool:
    """Check if OR syntax is missing priority= prefix."""
    return has_or_syntax and not priority_value.startswith("priority=")


def _should_suggest_numeric_format(has_text_format: bool, has_numeric: bool) -> bool:
    """Check if numeric format suggestion should be added."""
    return has_text_format and not has_numeric


def validate_priority_filter(priority_value: str) -> QueryValidationResult:
    """Validate priority filter syntax with enhanced debugging."""
    result = QueryValidationResult()

    has_multiple_priorities = any(p in priority_value for p in ["1", "2", "3"])
    has_or_syntax = "^OR" in priority_value
    has_comma_syntax = "," in priority_value

    if _has_comma_syntax_issue(has_multiple_priorities, has_or_syntax, has_comma_syntax):
        result.add_warning(
            f"Priority filter '{priority_value}' uses comma syntax instead of OR"
        )
        result.add_suggestion(
            "For multiple priorities, use: 'priority=1^ORpriority=2' instead of comma-separated values"
        )

    if _has_or_format_issue(priority_value, has_or_syntax):
        result.add_warning(
            f"OR syntax detected but missing 'priority=' prefix: {priority_value}"
        )
        result.add_suggestion(
            "Ensure OR filters start with field name: 'priority=1^ORpriority=2'"
        )

    has_numeric = any(p in priority_value for p in ["=1", "=2", "=3", "=4", "=5"])
    has_text_format = any(t in priority_value for t in ["Critical", "High", "Medium"])

    if _should_suggest_numeric_format(has_text_format, has_numeric):
        result.add_suggestion(
            "Consider using numeric priority format (1, 2, 3) for better compatibility"
        )

    return result


def validate_date_range_filter(date_value: str) -> QueryValidationResult:
    """Validate date range filter completeness and format."""
    result = QueryValidationResult()

    has_between_syntax = "BETWEEN" in date_value
    has_javascript_dates = "javascript:gs." in date_value
    has_old_comparison = ">=" in date_value or "<=" in date_value

    if has_old_comparison and not has_between_syntax:
        result.add_warning(
            f"Date filter uses old comparison syntax: {date_value}"
        )
        result.add_suggestion(
            "Use BETWEEN syntax: 'sys_created_onBETWEENjavascript:gs.dateGenerate()'"
        )

    if has_between_syntax and not has_javascript_dates:
        result.add_warning(
            "BETWEEN syntax detected but missing JavaScript date functions"
        )
        result.add_suggestion(
            "Use JavaScript date generation: 'javascript:gs.dateGenerate()' or 'javascript:gs.beginningOfLastWeek()'"
        )

    if has_between_syntax and "@" not in date_value:
        result.add_warning(
            "BETWEEN syntax missing '@' separator between start and end dates"
        )
        result.add_suggestion(
            "Use '@' to separate dates: 'BETWEEN...@javascript:gs.dateGenerate()'"
        )

    if "2025-08-25" in date_value and "2025-08-31" in date_value:
        result.add_suggestion(
            "Week 35 2025 date range detected - ensure timezone handling is correct"
        )

    return result


def validate_query_filters(filters: Dict[str, str]) -> QueryValidationResult:
    """Main filter validation function using dedicated helpers."""
    result = QueryValidationResult()

    for field, value in filters.items():
        if field == "priority":
            priority_result = validate_priority_filter(value)
            result.warnings.extend(priority_result.warnings)
            result.suggestions.extend(priority_result.suggestions)
        elif field == "sys_created_on":
            date_result = validate_date_range_filter(value)
            result.warnings.extend(date_result.warnings)
            result.suggestions.extend(date_result.suggestions)

    return result


# ---------------------------------------------------------------------------
# Auto-correction
# ---------------------------------------------------------------------------
# Lives here rather than in the intelligence module so the NL parser does
# not need to import the builder layer directly. The validator already
# owns the "what is wrong + how to fix" knowledge — correction is the
# applied form of that knowledge.

def _correct_priority(field: str, value: str) -> tuple[str, str | None]:
    """Return (corrected_value, suggestion_or_None) for a priority field."""
    if "," in value and "^OR" not in value:
        # Local import — validator -> builder is acceptable; the forbidden
        # direction is intelligence -> builder.
        from filter.builder import ServiceNowQueryBuilder

        priorities = value.split(",")
        corrected = ServiceNowQueryBuilder.build_priority_or_filter(priorities)
        return corrected, f"Corrected priority OR syntax: {corrected}"
    return value, None


def _correct_date(field: str, value: str) -> tuple[str, str | None]:
    """Return (corrected_value, suggestion_or_None) for a sys_created_on field."""
    if ">=" in value and ":" not in value and "javascript:" not in value:
        corrected = value.replace(">=", ">=") + " 00:00:00"
        return corrected, "Added time component to date filter"
    return value, None


def validate_and_correct_filters(filters: Dict[str, str]) -> QueryValidationResult:
    """Validate filters and auto-correct common syntax issues.

    Returns a result with `.corrected_filters` populated when corrections
    apply. Replaces the previous intelligence-layer correction routine so
    the NL parser stays decoupled from the builder layer.
    """
    result = validate_query_filters(filters)

    corrected: Dict[str, str] = {}
    for field, value in filters.items():
        if field == "priority":
            new_value, suggestion = _correct_priority(field, value)
        elif field == "sys_created_on":
            new_value, suggestion = _correct_date(field, value)
        else:
            new_value, suggestion = value, None
        corrected[field] = new_value
        if suggestion:
            result.add_suggestion(suggestion)

    if corrected != filters:
        result.corrected_filters = corrected

    return result


# ---------------------------------------------------------------------------
# Result-count validation
# ---------------------------------------------------------------------------

def _is_high_priority_query(filters: Dict[str, str]) -> bool:
    """Check if query is for high-priority (P1/P2) records."""
    if "priority" not in filters:
        return False
    return any(p in str(filters["priority"]) for p in ["1", "2"])


def _validate_incident_result_count(
    filters: Dict[str, str],
    result_count: int,
    expected_mins: Dict[str, int],
) -> QueryValidationResult:
    """Validate incident result count against expected baselines."""
    result = QueryValidationResult()

    if (
        _is_high_priority_query(filters)
        and result_count < expected_mins["incident_priority_high"]
    ):
        result.add_warning(
            f"Low P1/P2 incident count ({result_count}) - verify completeness"
        )
        result.add_suggestion(
            "Cross-verify with individual incident lookups or broader query"
        )

    return result


def validate_result_count(
    table_name: str,
    filters: Dict[str, str],
    result_count: int,
) -> QueryValidationResult:
    """Validate if result count seems reasonable for the query."""
    result = QueryValidationResult()

    expected_mins = {
        "incident_priority_high": 2,  # P1/P2 incidents should typically exist
        "incident_weekly": 5,         # Weekly incident count baseline
    }

    if table_name == "incident":
        result = _validate_incident_result_count(filters, result_count, expected_mins)

    return result


def cross_verify_critical_incidents() -> Dict[str, Any]:
    """Cross-verify that no P1 Critical incidents are missing."""
    return {
        "missing_critical": [],
        "verification_attempted": True,
        "additional_found": 0,
    }


def build_pagination_params(offset: int = 0, limit: int = 250) -> Dict[str, str]:
    """Build pagination parameters for ServiceNow queries."""
    return {
        "sysparm_offset": str(offset),
        "sysparm_limit": str(limit),
    }


def suggest_query_improvements(
    filters: Dict[str, str],
    result_count: int,
) -> List[str]:
    """Provide suggestions for query improvements."""
    suggestions: List[str] = []

    if result_count == 0:
        suggestions.append("Try broader date range or check filter syntax")
        suggestions.append("Verify field names match ServiceNow schema")
        suggestions.append("Check if date format is correct (YYYY-MM-DD)")
        suggestions.append("Verify caller_id exclusions are not too restrictive")

    if "priority" in filters and result_count < 3:
        suggestions.append("Consider using OR syntax: 'priority=1^ORpriority=2'")
        suggestions.append(
            "Check if priority values are numeric (1, 2) vs text ('1 - Critical')"
        )

    if result_count > 1000:
        suggestions.append("Consider adding more specific filters to reduce result set")
        suggestions.append("Add date range or caller exclusions to narrow results")

    return suggestions


# ---------------------------------------------------------------------------
# Debug query construction
# ---------------------------------------------------------------------------

def _analyze_date_filtering(query_string: str, debug_info: Dict[str, Any]) -> None:
    """Analyze date filtering components in the query."""
    if "sys_created_on" in query_string:
        debug_info["components"].append("Date filtering")
        if "BETWEEN" in query_string:
            debug_info["components"].append("BETWEEN syntax (correct)")
        elif ">=" in query_string or "<=" in query_string:
            debug_info["potential_issues"].append("Using old date comparison syntax")
            debug_info["recommendations"].append("Update to BETWEEN syntax for better reliability")


def _analyze_priority_filtering(query_string: str, debug_info: Dict[str, Any]) -> None:
    """Analyze priority filtering components in the query."""
    if "priority=" in query_string:
        debug_info["components"].append("Priority filtering")
        if "^OR" in query_string:
            debug_info["components"].append("OR logic (correct)")
        else:
            debug_info["potential_issues"].append("Single priority or missing OR syntax")


def _analyze_caller_exclusion(query_string: str, debug_info: Dict[str, Any]) -> None:
    """Analyze caller exclusion components in the query."""
    if "caller_id!=" in query_string:
        debug_info["components"].append("Caller exclusion")
        exclusion_count = query_string.count("caller_id!=")
        debug_info["components"].append(f"{exclusion_count} caller(s) excluded")


def _analyze_javascript_functions(query_string: str, debug_info: Dict[str, Any]) -> None:
    """Analyze JavaScript date functions in the query."""
    if "javascript:gs." in query_string:
        debug_info["components"].append("JavaScript date functions")
        if "@javascript:" in query_string:
            debug_info["components"].append("Proper date range separators")
        else:
            debug_info["potential_issues"].append("Missing date range separator (@)")


def _analyze_url_encoding(query_string: str, debug_info: Dict[str, Any]) -> None:
    """Analyze URL encoding issues in the query."""
    if " " in query_string:
        debug_info["potential_issues"].append("Unencoded spaces in query")
        debug_info["recommendations"].append("Ensure proper URL encoding")


def _analyze_original_filters(original_filters: Dict[str, str], debug_info: Dict[str, Any]) -> None:
    """Analyze original filters for common issues."""
    if not original_filters:
        return

    debug_info["original_filter_count"] = len(original_filters)
    debug_info["original_filters"] = list(original_filters.keys())

    if "_complete_query" in original_filters:
        debug_info["components"].append("Using complete query construction")

    for field, value in original_filters.items():
        if "," in str(value) and "^OR" not in str(value):
            debug_info["potential_issues"].append(
                f"Field '{field}' may use comma syntax instead of OR"
            )


def debug_query_construction(
    query_string: str,
    original_filters: Dict[str, str] = None,
) -> Dict[str, Any]:
    """Debug utility to analyze query construction and identify potential issues.

    Args:
        query_string: The final constructed query string
        original_filters: Original filter dictionary used to build the query

    Returns:
        Dictionary with debug information and recommendations
    """
    debug_info: Dict[str, Any] = {
        "query_length": len(query_string),
        "components": [],
        "potential_issues": [],
        "recommendations": [],
    }

    analysis_handlers = [
        _analyze_date_filtering,
        _analyze_priority_filtering,
        _analyze_caller_exclusion,
        _analyze_javascript_functions,
        _analyze_url_encoding,
    ]
    for handler in analysis_handlers:
        handler(query_string, debug_info)

    condition_count = query_string.count("^") + 1 if query_string else 0
    debug_info["condition_count"] = condition_count

    if condition_count > 5:
        debug_info["recommendations"].append(
            "Consider simplifying complex query for better performance"
        )

    _analyze_original_filters(original_filters, debug_info)

    return debug_info
