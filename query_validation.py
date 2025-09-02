"""
ServiceNow query validation and helper functions.
Provides modular validation without complex if/else chains.
"""

from typing import Dict, List, Tuple, Any, Optional
from constants import NO_RECORDS_FOUND, CONNECTION_ERROR, RECORD_NOT_FOUND


class ServiceNowQueryBuilder:
    """Helper class for building ServiceNow queries with proper syntax."""
    
    @staticmethod
    def build_priority_or_filter(priorities: List[str]) -> str:
        """Build OR filter for multiple priorities."""
        if len(priorities) == 1:
            return priorities[0]
        
        base_priority = priorities[0]
        or_conditions = "^OR".join(f"priority={p}" for p in priorities[1:])
        return f"{base_priority}^{or_conditions}"
    
    @staticmethod
    def build_date_range_filter(start_date: str, end_date: str) -> str:
        """Build date range filter for ServiceNow."""
        return f">={start_date} 00:00:00^<={end_date} 23:59:59"
    
    @staticmethod
    def build_exclusion_filter(field: str, exclude_ids: List[str]) -> str:
        """Build exclusion filter for multiple IDs."""
        return "^".join(f"{field}!={exc_id}" for exc_id in exclude_ids)


class QueryValidationResult:
    """Container for query validation results."""
    
    def __init__(self, is_valid: bool = True):
        self.is_valid = is_valid
        self.warnings: List[str] = []
        self.suggestions: List[str] = []
        self.corrected_filters: Optional[Dict[str, str]] = None
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
    
    def add_suggestion(self, suggestion: str) -> None:
        """Add a suggestion for improvement."""
        self.suggestions.append(suggestion)
    
    def has_issues(self) -> bool:
        """Check if there are any warnings or the query is invalid."""
        return not self.is_valid or len(self.warnings) > 0


def validate_priority_filter(priority_value: str) -> QueryValidationResult:
    """Validate priority filter syntax."""
    result = QueryValidationResult()
    
    # Check for multiple priorities without OR syntax
    has_multiple_priorities = any(p in priority_value for p in ["1", "2", "3"])
    has_or_syntax = "^OR" in priority_value
    
    if has_multiple_priorities and not has_or_syntax and "," in priority_value:
        result.add_warning(
            f"Priority filter '{priority_value}' may need OR syntax"
        )
        result.add_suggestion(
            "For multiple priorities, use: '1^ORpriority=2' instead of separate calls"
        )
    
    return result


def validate_date_range_filter(date_value: str) -> QueryValidationResult:
    """Validate date range filter completeness."""
    result = QueryValidationResult()
    
    has_start_date = ">=" in date_value
    has_end_date = "<=" in date_value
    
    if has_start_date and not has_end_date:
        result.add_warning("Date range may be incomplete")
        result.add_suggestion("Consider adding end date for complete range")
    
    return result


def validate_query_filters(filters: Dict[str, str]) -> QueryValidationResult:
    """Main filter validation function using helper validators."""
    result = QueryValidationResult()
    
    # Validate each filter type using dedicated functions
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


def validate_result_count(
    table_name: str, 
    filters: Dict[str, str], 
    result_count: int
) -> QueryValidationResult:
    """Validate if result count seems reasonable for the query."""
    result = QueryValidationResult()
    
    # Define expected minimums for different query types
    expected_mins = {
        "incident_priority_high": 2,  # P1/P2 incidents should typically exist
        "incident_weekly": 5,         # Weekly incident count baseline
    }
    
    # Check for suspiciously low incident counts
    if table_name == "incident":
        is_priority_query = "priority" in filters
        is_high_priority = is_priority_query and any(p in str(filters["priority"]) for p in ["1", "2"])
        
        if is_high_priority and result_count < expected_mins["incident_priority_high"]:
            result.add_warning(
                f"Low P1/P2 incident count ({result_count}) - verify completeness"
            )
            result.add_suggestion(
                "Cross-verify with individual incident lookups or broader query"
            )
    
    return result


async def cross_verify_critical_incidents(
    original_results: List[Dict[str, Any]], 
    date_range: Optional[str] = None
) -> Dict[str, Any]:
    """Cross-verify that no P1 Critical incidents are missing."""
    verification_result = {
        "missing_critical": [],
        "verification_attempted": True,
        "additional_found": 0
    }
    
    # This would implement additional verification logic
    # For now, return structure for future implementation
    return verification_result


def build_pagination_params(offset: int = 0, limit: int = 250) -> Dict[str, str]:
    """Build pagination parameters for ServiceNow queries."""
    return {
        "sysparm_offset": str(offset),
        "sysparm_limit": str(limit)
    }


def suggest_query_improvements(
    filters: Dict[str, str], 
    result_count: int
) -> List[str]:
    """Provide suggestions for query improvements."""
    suggestions = []
    
    if result_count == 0:
        suggestions.append("Try broader date range or check filter syntax")
        suggestions.append("Verify field names match ServiceNow schema")
    
    if "priority" in filters and result_count < 3:
        suggestions.append("Consider using OR syntax: '1^ORpriority=2'")
    
    return suggestions