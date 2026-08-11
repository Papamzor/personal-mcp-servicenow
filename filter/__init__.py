"""Filter pipeline — ServiceNow query construction, validation, value escaping.

Public API:
    Models:        TableFilterParams, QueryValidationResult
    Construction:  ServiceNowQueryBuilder
    Validation:    validate_query_filters, validate_priority_filter,
                   validate_date_range_filter, validate_result_count,
                   validate_reference_field, suggest_query_improvements,
                   debug_query_construction, cross_verify_critical_incidents,
                   build_pagination_params
    Value escaping: encode_query_value, QueryValueError, QUERY_VALUE_SAFE

v5.0 "Boron" (Tier 2.5): the NL-parsing (`filter.intelligence`) and explanation
(`filter.explainer`) modules were deleted — the tools that reached them
(intelligent_search, explain_servicenow_filters, build_smart_servicenow_filter,
get_servicenow_filter_templates) were culled in Tier 2, and the host model does
NL→filter natively.
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
    # Value escaping
    "QUERY_VALUE_SAFE",
    "QueryValueError",
    "encode_query_value",
]
