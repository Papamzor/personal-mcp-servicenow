"""Filter pipeline — ServiceNow query construction, validation, NL parsing, explanation.

v4.0 Sprint 1 consolidated `query_validation.py`, `query_intelligence.py`,
and the `TableFilterParams` / `SmartQueryParams` models that previously
lived in `Table_Tools/generic_table_tools.py` into one cohesive package.

Public API:
    Models:        TableFilterParams, SmartQueryParams, QueryValidationResult
    Construction:  ServiceNowQueryBuilder
    Validation:    validate_query_filters, validate_priority_filter,
                   validate_date_range_filter, validate_result_count,
                   suggest_query_improvements, debug_query_construction,
                   cross_verify_critical_incidents, build_pagination_params
    NL parsing:    QueryIntelligence, build_smart_filter, get_filter_templates
    Explanation:   QueryExplainer, explain_existing_filter
"""
from filter.models import (
    QueryValidationResult,
    SmartQueryParams,
    TableFilterParams,
)
from filter.builder import ServiceNowQueryBuilder
from filter.validator import (
    build_pagination_params,
    cross_verify_critical_incidents,
    debug_query_construction,
    suggest_query_improvements,
    validate_date_range_filter,
    validate_priority_filter,
    validate_query_filters,
    validate_result_count,
)
from filter.intelligence import (
    QueryIntelligence,
    build_smart_filter,
    get_filter_templates,
)
from filter.explainer import (
    QueryExplainer,
    explain_existing_filter,
)

__all__ = [
    # Models
    "QueryValidationResult",
    "SmartQueryParams",
    "TableFilterParams",
    # Construction
    "ServiceNowQueryBuilder",
    # Validation
    "build_pagination_params",
    "cross_verify_critical_incidents",
    "debug_query_construction",
    "suggest_query_improvements",
    "validate_date_range_filter",
    "validate_priority_filter",
    "validate_query_filters",
    "validate_result_count",
    # NL parsing
    "QueryIntelligence",
    "build_smart_filter",
    "get_filter_templates",
    # Explanation
    "QueryExplainer",
    "explain_existing_filter",
]
