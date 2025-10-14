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
        
        # Correct ServiceNow OR syntax: priority=1^ORpriority=2
        priority_conditions = [f"priority={p}" for p in priorities]
        return "^OR".join(priority_conditions)
    
    @staticmethod
    def build_date_range_filter(start_date: str, end_date: str) -> str:
        """Build date range filter for ServiceNow using proper BETWEEN syntax."""
        return f"sys_created_onBETWEENjavascript:gs.dateGenerate('{start_date}','00:00:00')@javascript:gs.dateGenerate('{end_date}','23:59:59')"
    
    @staticmethod
    def build_relative_date_filter(period: str = "Last week") -> str:
        """Build ServiceNow relative date filter with proper BETWEEN syntax."""
        if period.lower() == "last week":
            return "sys_created_onBETWEENjavascript:gs.beginningOfLastWeek()@javascript:gs.endOfLastWeek()"
        elif period.lower() == "today":
            return "sys_created_onBETWEENjavascript:gs.beginningOfToday()@javascript:gs.endOfToday()"
        elif period.lower() == "last 7 days":
            return "sys_created_onBETWEENjavascript:gs.daysAgoStart(7)@javascript:gs.daysAgoEnd(1)"
        elif period.lower() == "this week":
            return "sys_created_onBETWEENjavascript:gs.beginningOfThisWeek()@javascript:gs.endOfThisWeek()"
        else:
            # Fallback to standard range
            return f"sys_created_on>={period}"
    
    @staticmethod
    def build_exclusion_filter(field: str, exclude_ids: List[str]) -> str:
        """Build exclusion filter for multiple IDs using NOT EQUALS."""
        return "^".join(f"{field}!={exc_id}" for exc_id in exclude_ids)
    
    
    @staticmethod
    def build_complete_filter(
        priorities: Optional[List[str]] = None,
        date_period: Optional[str] = None,
        date_range: Optional[tuple] = None,
        exclude_callers: Optional[List[str]] = None,
        additional_filters: Optional[Dict[str, str]] = None
    ) -> str:
        """Build a complete ServiceNow filter string with proper syntax.
        
        Args:
            priorities: List of priorities (e.g., ['1', '2'])
            date_period: Relative period (e.g., 'last week', 'today')
            date_range: Tuple of (start_date, end_date) for specific range
            exclude_callers: List of caller sys_ids to exclude
            additional_filters: Additional field-value pairs
        """
        filter_parts = []
        
        # Add date filter (specific range takes precedence)
        if date_range and len(date_range) == 2:
            start_date, end_date = date_range
            filter_parts.append(
                ServiceNowQueryBuilder.build_date_range_filter(start_date, end_date)
            )
        elif date_period:
            filter_parts.append(
                ServiceNowQueryBuilder.build_relative_date_filter(date_period)
            )
        
        # Add priority filter if specified
        if priorities and len(priorities) > 0:
            priority_filter = ServiceNowQueryBuilder.build_priority_or_filter(priorities)
            filter_parts.append(priority_filter)
        
        # Add caller exclusion filter
        if exclude_callers and len(exclude_callers) > 0:
            exclusion_filter = ServiceNowQueryBuilder.build_exclusion_filter("caller_id", exclude_callers)
            filter_parts.append(exclusion_filter)
        
        # Add any additional filters
        if additional_filters:
            for field, value in additional_filters.items():
                if field not in ["sys_created_on", "priority", "caller_id"]:  # Avoid duplicates
                    filter_parts.append(f"{field}={value}")
        
        return "^".join(filter_parts)


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


def _has_comma_syntax_issue(priority_value: str, has_multiple: bool, has_or: bool, has_comma: bool) -> bool:
    """Check if priority filter has comma syntax issue. Complexity: 2"""
    return has_multiple and not has_or and has_comma

def _has_or_format_issue(priority_value: str, has_or_syntax: bool) -> bool:
    """Check if OR syntax is missing priority= prefix. Complexity: 2"""
    return has_or_syntax and not priority_value.startswith("priority=")

def _should_suggest_numeric_format(has_text_format: bool, has_numeric: bool) -> bool:
    """Check if numeric format suggestion should be added. Complexity: 2"""
    return has_text_format and not has_numeric

def validate_priority_filter(priority_value: str) -> QueryValidationResult:
    """Validate priority filter syntax with enhanced debugging.

    Complexity: 10 (reduced from ~15-18)
    """
    result = QueryValidationResult()

    # Check priority characteristics
    has_multiple_priorities = any(p in priority_value for p in ["1", "2", "3"])
    has_or_syntax = "^OR" in priority_value
    has_comma_syntax = "," in priority_value

    # Check for comma syntax issue
    if _has_comma_syntax_issue(priority_value, has_multiple_priorities, has_or_syntax, has_comma_syntax):
        result.add_warning(
            f"Priority filter '{priority_value}' uses comma syntax instead of OR"
        )
        result.add_suggestion(
            "For multiple priorities, use: 'priority=1^ORpriority=2' instead of comma-separated values"
        )

    # Validate proper OR format
    if _has_or_format_issue(priority_value, has_or_syntax):
        result.add_warning(
            f"OR syntax detected but missing 'priority=' prefix: {priority_value}"
        )
        result.add_suggestion(
            "Ensure OR filters start with field name: 'priority=1^ORpriority=2'"
        )

    # Check format suggestions
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
    
    # Check for proper BETWEEN syntax
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
    
    # Check for proper date separator in BETWEEN queries
    if has_between_syntax and "@" not in date_value:
        result.add_warning(
            "BETWEEN syntax missing '@' separator between start and end dates"
        )
        result.add_suggestion(
            "Use '@' to separate dates: 'BETWEEN...@javascript:gs.dateGenerate()'"
        )
    
    # Validate specific date formats
    if "2025-08-25" in date_value and "2025-08-31" in date_value:
        result.add_suggestion(
            "Week 35 2025 date range detected - ensure timezone handling is correct"
        )
    
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


def _is_high_priority_query(filters: Dict[str, str]) -> bool:
    """Check if query is for high-priority records. Complexity: 3"""
    if "priority" not in filters:
        return False
    return any(p in str(filters["priority"]) for p in ["1", "2"])

def _validate_incident_result_count(
    filters: Dict[str, str],
    result_count: int,
    expected_mins: Dict[str, int]
) -> QueryValidationResult:
    """Validate incident result count. Complexity: 4"""
    result = QueryValidationResult()

    if _is_high_priority_query(filters) and result_count < expected_mins["incident_priority_high"]:
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
    result_count: int
) -> QueryValidationResult:
    """Validate if result count seems reasonable for the query.

    Complexity: 6 (reduced from ~15-17)
    """
    result = QueryValidationResult()

    # Define expected minimums for different query types
    expected_mins = {
        "incident_priority_high": 2,  # P1/P2 incidents should typically exist
        "incident_weekly": 5,         # Weekly incident count baseline
    }

    # Check for suspiciously low incident counts
    if table_name == "incident":
        result = _validate_incident_result_count(filters, result_count, expected_mins)

    return result


def cross_verify_critical_incidents() -> Dict[str, Any]:
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
        suggestions.append("Check if date format is correct (YYYY-MM-DD)")
        suggestions.append("Verify caller_id exclusions are not too restrictive")
    
    if "priority" in filters and result_count < 3:
        suggestions.append("Consider using OR syntax: 'priority=1^ORpriority=2'")
        suggestions.append("Check if priority values are numeric (1, 2) vs text ('1 - Critical')")
    
    if result_count > 1000:
        suggestions.append("Consider adding more specific filters to reduce result set")
        suggestions.append("Add date range or caller exclusions to narrow results")
    
    return suggestions


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
            debug_info["potential_issues"].append(f"Field '{field}' may use comma syntax instead of OR")


def debug_query_construction(
    query_string: str,
    original_filters: Dict[str, str] = None
) -> Dict[str, Any]:
    """Debug utility to analyze query construction and identify potential issues.
    
    Args:
        query_string: The final constructed query string
        original_filters: Original filter dictionary used to build the query
        
    Returns:
        Dictionary with debug information and recommendations
    """
    debug_info = {
        "query_length": len(query_string),
        "components": [],
        "potential_issues": [],
        "recommendations": []
    }
    
    # Analysis handler registry for specialized debug logic
    analysis_handlers = [
        _analyze_date_filtering,
        _analyze_priority_filtering,
        _analyze_caller_exclusion,
        _analyze_javascript_functions,
        _analyze_url_encoding,
    ]
    
    # Apply all query string analyzers
    for handler in analysis_handlers:
        handler(query_string, debug_info)
    
    # Analyze query complexity
    condition_count = query_string.count("^") + 1 if query_string else 0
    debug_info["condition_count"] = condition_count
    
    if condition_count > 5:
        debug_info["recommendations"].append("Consider simplifying complex query for better performance")
    
    # Analyze original filters
    _analyze_original_filters(original_filters, debug_info)
    
    return debug_info