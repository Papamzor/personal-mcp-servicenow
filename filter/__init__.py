"""Filter pipeline — ServiceNow query construction, validation, NL parsing, explanation.

Public API:
    Models:        TableFilterParams, QueryValidationResult
    Construction:  ServiceNowQueryBuilder
    Validation:    validate_query_filters, validate_priority_filter,
                   validate_date_range_filter, validate_result_count,
                   validate_reference_field, suggest_query_improvements,
                   debug_query_construction, cross_verify_critical_incidents,
                   build_pagination_params
    NL parsing:    QueryIntelligence, build_smart_filter, get_filter_templates
    Explanation:   QueryExplainer, explain_existing_filter
    Value escaping: encode_query_value, QueryValueError, QUERY_VALUE_SAFE
"""
from filter.models import (
    QueryValidationResult,
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
    validate_reference_field,
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
from filter.value_encoding import (
    QUERY_VALUE_SAFE,
    QueryValueError,
    encode_query_value,
)

__all__ = [
    # Models
    "QueryValidationResult",
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
    "validate_reference_field",
    "validate_result_count",
    # NL parsing
    "QueryIntelligence",
    "build_smart_filter",
    "get_filter_templates",
    # Explanation
    "QueryExplainer",
    "explain_existing_filter",
    # Value escaping
    "QUERY_VALUE_SAFE",
    "QueryValueError",
    "encode_query_value",
]
