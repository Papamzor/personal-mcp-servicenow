"""Backwards-compat shim — v4.0 moved this module's contents into ``filter/``.

Delete in v4.1 once external callers have migrated to ``from filter import ...``.
"""
from filter.builder import ServiceNowQueryBuilder
from filter.models import QueryValidationResult
from filter.validator import (
    _analyze_caller_exclusion,
    _analyze_date_filtering,
    _analyze_javascript_functions,
    _analyze_original_filters,
    _analyze_priority_filtering,
    _analyze_url_encoding,
    _has_comma_syntax_issue,
    _has_or_format_issue,
    _is_high_priority_query,
    _should_suggest_numeric_format,
    _validate_incident_result_count,
    build_pagination_params,
    cross_verify_critical_incidents,
    debug_query_construction,
    suggest_query_improvements,
    validate_and_correct_filters,
    validate_date_range_filter,
    validate_priority_filter,
    validate_query_filters,
    validate_result_count,
)

__all__ = [
    "ServiceNowQueryBuilder",
    "QueryValidationResult",
    "build_pagination_params",
    "cross_verify_critical_incidents",
    "debug_query_construction",
    "suggest_query_improvements",
    "validate_and_correct_filters",
    "validate_date_range_filter",
    "validate_priority_filter",
    "validate_query_filters",
    "validate_result_count",
]
