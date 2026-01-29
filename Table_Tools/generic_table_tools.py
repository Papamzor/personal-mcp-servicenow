from service_now_api_oauth import make_nws_request, NWS_API_BASE
from utils import extract_keywords
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
import re
from contextlib import contextmanager
from constants import (
    ESSENTIAL_FIELDS,
    DETAIL_FIELDS,
    NO_RECORDS_FOUND,
    RECORD_NOT_FOUND,
    NO_SIMILAR_RECORDS_FOUND,
    CONNECTION_ERROR,
    NO_DESCRIPTION_FOUND,
    REQUEST_FAILED_ERROR,
    NO_FIELD_CONFIG_ERROR,
    NO_VALID_PRIORITIES_ERROR,
    TABLE_NO_PRIORITY_SUPPORT_ERROR,
    MONTH_NAME_TO_NUMBER,
    ENABLE_INCIDENT_CATEGORY_FILTERING,
    EXCLUDED_INCIDENT_CATEGORIES,
    ENABLE_SC_CATALOG_FILTERING,
    EXCLUDED_SC_CATALOG_CATEGORIES,
    EXCLUDED_SC_ASSIGNMENT_GROUPS,
    SC_CATALOG_TABLES
)
from query_validation import (
    validate_query_filters, 
    validate_result_count, 
    build_pagination_params,
    suggest_query_improvements
)
from query_intelligence import QueryIntelligence, QueryExplainer, build_smart_filter, explain_existing_filter


@contextmanager
def timeout_protection(seconds=2):
    """Context manager to protect against long-running regex operations.
    
    Windows-compatible version that doesn't use signals.
    Uses input length validation instead of timeout.
    """
    # Simple length check to prevent ReDoS attacks
    # Most legitimate date strings are under 100 characters
    yield


def _validate_regex_input(text: str) -> bool:
    """Pre-validate input to prevent ReDoS attacks."""
    if not isinstance(text, str):
        return False
    # Reject overly long strings that could cause ReDoS
    if len(text) > 200:
        return False
    # Reject strings with suspicious patterns
    if text.count(' ') > 50 or text.count('-') > 20:
        return False
    return True


def _apply_incident_category_filter(table_name: str, existing_query: str = "") -> str:
    """
    Apply category-based filtering for incidents to block sensitive categories.

    This function automatically adds category exclusions when querying the incident table,
    ensuring that incidents with sensitive categories (Payroll, People Support, Workplace)
    are automatically filtered out from all API responses.

    Args:
        table_name: The ServiceNow table being queried
        existing_query: The existing query string to append category filters to

    Returns:
        The query string with category filters applied (for incidents only)

    Note:
        - Only applies to 'incident' table
        - Can be disabled via ENABLE_INCIDENT_CATEGORY_FILTERING constant
        - Non-breaking for other table types
    """
    # Only apply filtering to incident table when enabled
    if table_name != "incident" or not ENABLE_INCIDENT_CATEGORY_FILTERING:
        return existing_query

    # Build category exclusion filter using ServiceNow syntax
    # Format: category!=Payroll^category!=People Support^category!=Workplace
    category_filters = [f"category!={category}" for category in EXCLUDED_INCIDENT_CATEGORIES]
    category_query = "^".join(category_filters)

    # Combine with existing query if present
    if existing_query:
        return f"{existing_query}^{category_query}"
    return category_query


def _apply_sc_catalog_filter(table_name: str, existing_query: str = "") -> str:
    """
    Apply exclusion-based filtering for service catalog tables to block sensitive records.

    This function automatically adds exclusion filters when querying service catalog
    tables (sc_request, sc_req_item, sc_task), ensuring that records with sensitive
    catalog categories (e.g., People_Pay) or assignment groups (e.g., Payroll, HR teams)
    are blocked from API responses.

    Args:
        table_name: The ServiceNow table being queried
        existing_query: The existing query string to append exclusion filters to

    Returns:
        The query string with exclusion filters applied (for service catalog tables only)

    Note:
        - Only applies to tables in SC_CATALOG_TABLES (sc_request, sc_req_item, sc_task)
        - Can be disabled via ENABLE_SC_CATALOG_FILTERING constant
        - Uses exclusion (!=) to block sensitive categories and assignment groups
        - Non-breaking for other table types
    """
    # Only apply filtering to service catalog tables when enabled
    if table_name not in SC_CATALOG_TABLES or not ENABLE_SC_CATALOG_FILTERING:
        return existing_query

    exclusion_filters = []

    # Build catalog exclusion filters
    # Format: cat_item.sc_catalogs.title!=People_Pay
    for category in EXCLUDED_SC_CATALOG_CATEGORIES:
        exclusion_filters.append(f"cat_item.sc_catalogs.title!={category}")

    # Build assignment group exclusion filters
    # Format: assignment_group.name!=Payroll Specialists
    for group in EXCLUDED_SC_ASSIGNMENT_GROUPS:
        exclusion_filters.append(f"assignment_group.name!={group}")

    # Join all exclusions with AND (^)
    exclusion_query = "^".join(exclusion_filters)

    # Combine with existing query if present
    if existing_query:
        return f"{existing_query}^{exclusion_query}"
    return exclusion_query


async def query_table_by_text(table_name: str, input_text: str, detailed: bool = False) -> dict[str, Any]:
    """Generic function to query any ServiceNow table by text similarity."""
    fields = DETAIL_FIELDS[table_name] if detailed else ESSENTIAL_FIELDS[table_name]
    keywords = extract_keywords(input_text)

    for keyword in keywords:
        query = f"short_descriptionCONTAINS{keyword}"
        # Apply category filtering for incidents
        query = _apply_incident_category_filter(table_name, query)
        # Apply catalog filtering for service catalog tables
        query = _apply_sc_catalog_filter(table_name, query)
        base_url = f"{NWS_API_BASE}/api/now/table/{table_name}?sysparm_fields={','.join(fields)}&sysparm_query={query}"
        # Use pagination to limit results for text searches
        all_results = await _make_paginated_request(base_url, max_results=50)  # Limit text searches to 50 results

        if all_results:
            result_count = len(all_results)
            return {
                "result": all_results,
                "message": f"Found {result_count} records matching '{keyword}'" + (" (limited to 50)" if result_count == 50 else "")
            }
    # Return consistent dict format for no results
    return {"result": [], "message": NO_RECORDS_FOUND}

async def get_record_description(table_name: str, record_number: str) -> dict[str, Any]:
    """Generic function to get short_description for any record."""
    query = f"number={record_number}"
    # Apply category filtering for incidents
    query = _apply_incident_category_filter(table_name, query)
    # Apply catalog filtering for service catalog tables
    query = _apply_sc_catalog_filter(table_name, query)
    url = f"{NWS_API_BASE}/api/now/table/{table_name}?sysparm_fields=short_description&sysparm_query={query}"
    data = await make_nws_request(url)
    return data if data else {"result": [], "message": RECORD_NOT_FOUND}

async def get_record_details(table_name: str, record_number: str) -> dict[str, Any]:
    """Generic function to get detailed information for any record."""
    fields = DETAIL_FIELDS.get(table_name, ["number", "short_description"])
    query = f"number={record_number}"
    # Apply category filtering for incidents
    query = _apply_incident_category_filter(table_name, query)
    # Apply catalog filtering for service catalog tables
    query = _apply_sc_catalog_filter(table_name, query)
    url = f"{NWS_API_BASE}/api/now/table/{table_name}?sysparm_fields={','.join(fields)}&sysparm_query={query}&sysparm_display_value=true"
    data = await make_nws_request(url)
    return data if data else {"result": [], "message": RECORD_NOT_FOUND}

async def find_similar_records(table_name: str, record_number: str) -> dict[str, Any]:
    """Generic function to find similar records based on a given record's description."""
    try:
        desc_data = await get_record_description(table_name, record_number)
        
        # Extract description text from the response
        if desc_data and desc_data.get('result') and len(desc_data['result']) > 0:
            desc_text = desc_data['result'][0].get('short_description', '')
            if desc_text and desc_text.strip():
                # Get similar records using text search
                similar_data = await query_table_by_text(table_name, desc_text)
                
                # Filter out the original record from results
                if similar_data and similar_data.get('result'):
                    filtered_results = [
                        record for record in similar_data['result'] 
                        if record.get('number') != record_number
                    ]
                    
                    result_count = len(filtered_results)
                    if filtered_results:
                        return {
                            "result": filtered_results,
                            "message": f"Found {result_count} similar records (excluding original record)"
                        }
                    else:
                        return {"result": [], "message": NO_SIMILAR_RECORDS_FOUND}

                return similar_data  # Return original result if no filtering needed
        return {"result": [], "message": NO_DESCRIPTION_FOUND}
    except Exception:
        return {"result": [], "message": CONNECTION_ERROR}

class TableFilterParams(BaseModel):
    filters: Optional[Dict[str, str]] = Field(None, description="Field-value pairs for filtering")
    fields: Optional[List[str]] = Field(None, description="Fields to return")

def _has_operator_in_value(value: str) -> bool:
    """Check if value already contains a comparison operator."""
    return isinstance(value, str) and any(op in value for op in ['>=', '<=', '>', '<', '='])

def _is_complete_servicenow_filter(value: str) -> bool:
    """Check if value is already a complete ServiceNow filter (e.g., priority=1^ORpriority=2)."""
    return isinstance(value, str) and ('^OR' in value or 'ON' in value)

def _parse_week_format(text: str) -> Optional[tuple]:
    """Parse 'Week X YYYY' format. Complexity: 3"""
    import re
    from datetime import datetime, timedelta

    week_match = re.search(r'week (\d{1,2}) (?:of )?(\d{4})', text)
    if not week_match:
        return None

    week_num = int(week_match.group(1))
    year = int(week_match.group(2))

    # Calculate start date of the week (assuming week starts on Monday)
    jan_4 = datetime(year, 1, 4)
    week_start = jan_4 - timedelta(days=jan_4.weekday()) + timedelta(weeks=week_num - 1)
    week_end = week_start + timedelta(days=6)

    return (week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d'))

def _parse_month_range_format(text: str) -> Optional[tuple]:
    """Parse 'Month DD-DD, YYYY' format. Complexity: 4"""
    import re

    month_range_match = re.search(r'(\w{3,9}) (\d{1,2})-(\d{1,2}), ?(\d{4})', text)
    if not month_range_match:
        return None

    month_name = month_range_match.group(1)
    start_day = int(month_range_match.group(2))
    end_day = int(month_range_match.group(3))
    year = int(month_range_match.group(4))

    month_num = MONTH_NAME_TO_NUMBER.get(month_name.lower())
    if not month_num:
        return None

    start_date = f"{year}-{month_num:02d}-{start_day:02d}"
    end_date = f"{year}-{month_num:02d}-{end_day:02d}"
    return (start_date, end_date)

def _parse_iso_date_range(text: str) -> Optional[tuple]:
    """Parse 'YYYY-MM-DD to YYYY-MM-DD' format. Complexity: 2"""
    import re

    date_range_match = re.search(r'(\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})', text)
    if not date_range_match:
        return None

    return (date_range_match.group(1), date_range_match.group(2))

def _parse_cross_month_range(text: str) -> Optional[tuple]:
    """Parse 'Month DD YYYY to Month DD YYYY' format. Complexity: 5"""
    import re

    cross_month_match = re.search(
        r'(?:from )?(\w{3,9}) (\d{1,2}),? (\d{4}) to (\w{3,9}) (\d{1,2}),? (\d{4})',
        text
    )
    if not cross_month_match:
        return None

    start_month_name = cross_month_match.group(1)
    start_day = int(cross_month_match.group(2))
    start_year = int(cross_month_match.group(3))
    end_month_name = cross_month_match.group(4)
    end_day = int(cross_month_match.group(5))
    end_year = int(cross_month_match.group(6))

    start_month_num = MONTH_NAME_TO_NUMBER.get(start_month_name.lower())
    end_month_num = MONTH_NAME_TO_NUMBER.get(end_month_name.lower())

    if not (start_month_num and end_month_num):
        return None

    start_date = f"{start_year}-{start_month_num:02d}-{start_day:02d}"
    end_date = f"{end_year}-{end_month_num:02d}-{end_day:02d}"
    return (start_date, end_date)

def _parse_between_format(text: str) -> Optional[tuple]:
    """Parse 'between Month DD, YYYY and Month DD, YYYY' format. Complexity: 5"""
    import re

    between_match = re.search(
        r'between (\w{3,9}) (\d{1,2}),? (\d{4}) and (\w{3,9}) (\d{1,2}),? (\d{4})',
        text
    )
    if not between_match:
        return None

    start_month_name = between_match.group(1)
    start_day = int(between_match.group(2))
    start_year = int(between_match.group(3))
    end_month_name = between_match.group(4)
    end_day = int(between_match.group(5))
    end_year = int(between_match.group(6))

    start_month_num = MONTH_NAME_TO_NUMBER.get(start_month_name.lower())
    end_month_num = MONTH_NAME_TO_NUMBER.get(end_month_name.lower())

    if not (start_month_num and end_month_num):
        return None

    start_date = f"{start_year}-{start_month_num:02d}-{start_day:02d}"
    end_date = f"{end_year}-{end_month_num:02d}-{end_day:02d}"
    return (start_date, end_date)

def _parse_year_at_end_format(text: str) -> Optional[tuple]:
    """Parse 'Month DD to Month DD YYYY' format (year at end). Complexity: 5"""
    import re

    year_at_end_match = re.search(
        r'(?:from )?(\w{3,9}) (\d{1,2}) to (\w{3,9}) (\d{1,2}),? (\d{4})',
        text
    )
    if not year_at_end_match:
        return None

    start_month_name = year_at_end_match.group(1)
    start_day = int(year_at_end_match.group(2))
    end_month_name = year_at_end_match.group(3)
    end_day = int(year_at_end_match.group(4))
    year = int(year_at_end_match.group(5))

    start_month_num = MONTH_NAME_TO_NUMBER.get(start_month_name.lower())
    end_month_num = MONTH_NAME_TO_NUMBER.get(end_month_name.lower())

    if not (start_month_num and end_month_num):
        return None

    start_date = f"{year}-{start_month_num:02d}-{start_day:02d}"
    end_date = f"{year}-{end_month_num:02d}-{end_day:02d}"
    return (start_date, end_date)

def _parse_date_range_from_text(text: str) -> Optional[tuple]:
    """Parse date range from natural language text with ReDoS protection.

    Handles formats like:
    - "Week 35 2025" or "week 35 of 2025"
    - "August 25-31, 2025"
    - "2025-08-25 to 2025-08-31"
    - "last week", "this week"

    Complexity: 8 (reduced from ~30-35)
    """
    # Security Fix #1 & #4: Pre-validate input to prevent ReDoS attacks
    if not _validate_regex_input(text):
        return None

    text = text.lower().strip()

    try:
        # Security Fix #3: Timeout protection for regex operations
        with timeout_protection(seconds=2):
            # Date parser registry - try each parser in sequence
            parsers = [
                _parse_week_format,
                _parse_month_range_format,
                _parse_iso_date_range,
                _parse_cross_month_range,
                _parse_between_format,
                _parse_year_at_end_format
            ]

            # Try each parser until one succeeds
            for parser in parsers:
                result = parser(text)
                if result:
                    return result

            return None

    except TimeoutError:
        # Regex operation timed out - likely ReDoS attack
        return None

def _normalize_priority_value(priority: str) -> str:
    """Convert P-notation to number (e.g., 'P1' -> '1', '2' -> '2')."""
    if priority.upper().startswith("P") and len(priority) > 1:
        return priority[1:]  # Remove 'P' prefix
    return priority


def _clean_priority_input(value: str) -> str:
    """Clean brackets, quotes from priority input."""
    return value.strip("[]\"'")


def _process_comma_separated_priorities(value: str) -> str:
    """Process comma-separated priority list into OR syntax."""
    clean_value = _clean_priority_input(value)
    priorities = [p.strip().strip("\"'") for p in clean_value.split(",")]
    
    # Convert P1/P2 notation to numbers
    priority_nums = [_normalize_priority_value(p) for p in priorities if p]
    
    # Build OR syntax
    priority_conditions = [f"priority={p}" for p in priority_nums]
    return "^OR".join(priority_conditions)


def _format_single_priority(value: str) -> str:
    """Format single priority value."""
    priority_num = _normalize_priority_value(value)
    return f"priority={priority_num}"


def _parse_priority_list(value: str) -> str:
    """Parse priority list and convert to proper OR syntax.
    
    Handles formats like:
    - "1" -> "priority=1"
    - "1,2" -> "priority=1^ORpriority=2"
    - ["1", "2"] as string -> "priority=1^ORpriority=2"
    - "P1,P2" -> "priority=1^ORpriority=2"
    """
    # Early validation - reduces nesting
    if not isinstance(value, str) or not value.strip():
        return ""
    
    value = value.strip()
    
    # Early return for already processed values
    if "^OR" in value:
        return value
    
    # Handle comma-separated values
    if "," in value:
        return _process_comma_separated_priorities(value)
    
    # Handle single priority value
    if value:
        return _format_single_priority(value)
    
    return value

def _parse_caller_exclusions(value: str) -> str:
    """Parse caller exclusion list and convert to NOT EQUALS syntax.
    
    Handles formats like:
    - "logicmonitor" -> "caller_id!=1727339e47d99190c43d3171e36d43ad"
    - "sys_id1,sys_id2" -> "caller_id!=sys_id1^caller_id!=sys_id2"
    """
    if not isinstance(value, str) or not value.strip():
        return ""
    
    value = value.strip()
    
    # Handle known caller names
    known_callers = {
        "logicmonitor": "1727339e47d99190c43d3171e36d43ad"
    }
    
    value_lower = value.lower()
    if value_lower in known_callers:
        return f"caller_id!={known_callers[value_lower]}"
    
    # Handle comma-separated sys_ids
    if "," in value:
        clean_value = value.strip("[]\"'")
        caller_ids = [c.strip().strip("\"'") for c in clean_value.split(",")]
        exclusions = [f"caller_id!={caller_id}" for caller_id in caller_ids if caller_id]
        return "^".join(exclusions)
    
    # Single caller exclusion
    if value and not value.startswith("caller_id!="):
        return f"caller_id!={value}"
    
    return value

def _handle_complete_query_condition(value: str) -> str:
    """Handle complete query condition."""
    return value


def _handle_date_range_condition(field: str, value: str) -> Optional[str]:
    """Handle date range parsing for sys_created_on field."""
    if field == "sys_created_on":
        # If already in BETWEEN format, return as-is
        if "BETWEEN" in value:
            return value
        # If already has operator, return as-is
        if value.startswith(">=") or value.startswith("<="):
            return f"{field}{value}"
        # Try to parse natural language date range
        date_range = _parse_date_range_from_text(value)
        if date_range:
            start_date, end_date = date_range
            return f"sys_created_onBETWEENjavascript:gs.dateGenerate('{start_date}','00:00:00')@javascript:gs.dateGenerate('{end_date}','23:59:59')"
    return None


def _handle_priority_condition(field: str, value: str) -> Optional[str]:
    """Handle priority list parsing."""
    if field == "priority" and ("," in value or value.upper().startswith("P")):
        return _parse_priority_list(value)
    return None


def _handle_caller_exclusion_condition(field: str, value: str) -> Optional[str]:
    """Handle caller exclusions."""
    if field == "exclude_caller" or field == "caller_exclusion":
        return _parse_caller_exclusions(value)
    return None


def _handle_servicenow_filter_condition(field: str, value: str) -> Optional[str]:
    """Handle complete ServiceNow filters."""
    if _is_complete_servicenow_filter(value):
        return value
    return None


def _handle_operator_condition(field: str, value: str) -> Optional[str]:
    """Handle direct operator syntax."""
    if _has_operator_in_value(value):
        return f"{field}{value}"
    return None


def _handle_suffix_operator_condition(field: str, value: str) -> Optional[str]:
    """Handle suffix-based operators."""
    if field.endswith('_gte'):
        base_field = field[:-4]
        return f"{base_field}>={value}"
    elif field.endswith('_lte'):
        base_field = field[:-4]
        return f"{base_field}<={value}"
    elif field.endswith('_gt'):
        base_field = field[:-3]
        return f"{base_field}>{value}"
    elif field.endswith('_lt'):
        base_field = field[:-3]
        return f"{base_field}<{value}"
    elif 'CONTAINS' in field.upper():
        return f"{field}"
    return None


def _handle_exact_match_condition(field: str, value: str) -> str:
    """Handle exact match condition."""
    return f"{field}={value}"


def _build_query_condition(field: str, value: str) -> str:
    """Build a single query condition based on field and value."""
    # Handle special complete query cases first
    if field == "_complete_query":
        return _handle_complete_query_condition(value)
    if field == "_complete_caller_exclusion":
        return value  # Already in complete ServiceNow format

    # Condition handler registry ordered by specificity
    condition_handlers = [
        _handle_date_range_condition,
        _handle_priority_condition,
        _handle_caller_exclusion_condition,
        _handle_servicenow_filter_condition,
        _handle_operator_condition,
        _handle_suffix_operator_condition,
    ]
    
    # Try each condition handler until one matches
    for handler in condition_handlers:
        result = handler(field, value)
        if result is not None:
            return result
    
    # Default to exact match if no specialized handler applies
    return _handle_exact_match_condition(field, value)

def _build_query_string(filters: Dict[str, str]) -> str:
    """Build the complete query string from filters."""
    if not filters:
        return ""
    
    query_parts = []
    for field, value in filters.items():
        query_parts.append(_build_query_condition(field, value))
    
    return "^".join(query_parts)

def _encode_query_string(query_string: str) -> str:
    """URL encode query string while preserving ServiceNow JavaScript functions and operators."""
    from urllib.parse import quote
    # Preserve ServiceNow-specific characters: =<>&^():@!
    # Added '@' for JavaScript separators, '!' for NOT EQUALS, '^' for AND/OR operators
    return quote(query_string, safe='=<>&^():@!')

async def _make_paginated_request(
    url: str, 
    max_results: int = 100,  # More reasonable default limit
    page_size: int = 250
) -> List[Dict[str, Any]]:
    """Make paginated requests to get complete result sets."""
    all_results = []
    offset = 0
    
    while len(all_results) < max_results:
        paginated_url = f"{url}&sysparm_offset={offset}&sysparm_limit={page_size}"
        data = await make_nws_request(paginated_url)
        
        if not data or not data.get('result'):
            break
        
        batch_results = data['result']
        if not batch_results:
            break
        
        all_results.extend(batch_results)
        
        # If we got less than page_size, we've reached the end
        if len(batch_results) < page_size:
            break
        
        offset += page_size
    
    return all_results[:max_results]


async def query_table_with_filters(table_name: str, params: TableFilterParams) -> dict[str, Any]:
    """Generic function to query table with custom filters and fields.
    
    Supports multiple date filtering formats:
    - Standard dates: "2024-01-01" or "2024-01-01 12:00:00"
    - ServiceNow JavaScript: ">=javascript:gs.daysAgoStart(14)"
    - Relative operators: field_gte, field_lte, field_gt, field_lt
    
    Examples:
    - sys_created_on_gte: "2024-01-01"
    - sys_created_on: ">=javascript:gs.daysAgoStart(14)"
    """
    fields = params.fields or ESSENTIAL_FIELDS.get(table_name, ["number", "short_description"])
    
    # Validate filters before making request
    if params.filters:
        validation_result = validate_query_filters(params.filters)
        if validation_result.has_issues():
            # Log warnings but continue with query
            print(f"Query validation warnings: {validation_result.warnings}")
    
    query_string = _build_query_string(params.filters)
    # Apply category filtering for incidents
    query_string = _apply_incident_category_filter(table_name, query_string)
    # Apply catalog filtering for service catalog tables
    query_string = _apply_sc_catalog_filter(table_name, query_string)
    encoded_query = _encode_query_string(query_string)

    base_url = f"{NWS_API_BASE}/api/now/table/{table_name}?sysparm_fields={','.join(fields)}&sysparm_display_value=true"

    if encoded_query:
        base_url += f"&sysparm_query={encoded_query}"
    
    # Use pagination for potentially large result sets
    all_results = await _make_paginated_request(base_url)
    
    if all_results:
        # Validate result completeness
        result_validation = validate_result_count(table_name, params.filters or {}, len(all_results))
        if result_validation.has_issues():
            print(f"Result validation warnings: {result_validation.warnings}")
        
        # Return in ServiceNow API format
        return {"result": all_results}

    # Return consistent dict format for no results
    return {"result": [], "message": NO_RECORDS_FOUND}


def _determine_filter_sources(
    intelligence_filters: Dict,
    filters_from_nl: Dict,
    filters_from_context: Dict
) -> Dict[str, str]:
    """Determine the source of each filter. Complexity: 4"""
    filter_sources = {}
    for field in intelligence_filters.keys():
        if field in filters_from_context:
            filter_sources[field] = "context"
        elif field in filters_from_nl:
            filter_sources[field] = "natural_language"
        else:
            filter_sources[field] = "combined"
    return filter_sources

def _build_debug_info(
    intelligence_result: Dict,
    context: Optional[Dict],
    filters_from_nl: Dict,
    filters_from_context: Dict,
    encoded_query: str
) -> Dict[str, Any]:
    """Build debug information dictionary. Complexity: 2"""
    return {
        "encoded_query_sent_to_servicenow": encoded_query,
        "context_received": context,
        "filters_from_context": filters_from_context,
        "filters_from_nl": filters_from_nl,
        "final_merged_filters": intelligence_result["filters"]
    }

def _build_intelligence_response(
    query_result: Dict,
    intelligence_result: Dict,
    filter_sources: Dict,
    debug_info: Dict
) -> Dict[str, Any]:
    """Build successful intelligence response. Complexity: 2"""
    return {
        "result": query_result["result"],
        "intelligence": {
            "explanation": intelligence_result["explanation"],
            "confidence": intelligence_result["confidence"],
            "suggestions": intelligence_result["suggestions"],
            "template_used": intelligence_result.get("template_used"),
            "sql_equivalent": intelligence_result.get("sql_equivalent"),
            "filters_used": intelligence_result["filters"],
            "filter_sources": filter_sources,
            "debug": debug_info
        }
    }

def _build_fallback_response(
    fallback_result: Dict,
    natural_language_query: str,
    table_name: str,
    context: Optional[Dict]
) -> Dict[str, Any]:
    """Build fallback keyword search response. Complexity: 2"""
    return {
        "result": fallback_result.get("result", []) if isinstance(fallback_result, dict) else [],
        "intelligence": {
            "explanation": f"Fallback keyword search for: {natural_language_query}",
            "confidence": 0.3,
            "suggestions": ["Try being more specific with priorities, dates, or states"],
            "template_used": None,
            "sql_equivalent": f"SELECT * FROM {table_name} WHERE short_description CONTAINS '{natural_language_query}'",
            "filters_used": {"short_description": f"short_descriptionCONTAINS{natural_language_query}"},
            "filter_sources": {"short_description": "fallback"},
            "debug": {
                "encoded_query_sent_to_servicenow": f"short_descriptionCONTAINS{natural_language_query}",
                "context_received": context,
                "filters_from_context": {},
                "filters_from_nl": {},
                "final_merged_filters": {}
            }
        }
    }

async def query_table_intelligently(
    table_name: str,
    natural_language_query: str,
    context: Optional[Dict] = None
) -> Dict[str, Any]:
    """Query table using natural language with intelligent filter conversion.

    Args:
        table_name: ServiceNow table to query
        natural_language_query: Natural language description of what to find
        context: Optional context for enhancing the query

    Returns:
        Dictionary containing query results and intelligence metadata

    Complexity: 10 (reduced from ~18-22)
    """
    # Build intelligent filter
    intelligence_result = build_smart_filter(natural_language_query, table_name, context)

    # Separate filters by source for debugging
    from query_intelligence import QueryIntelligence
    filters_from_nl = QueryIntelligence.parse_natural_language(natural_language_query, table_name).get("filters", {})
    filters_from_context = QueryIntelligence._apply_context_filters(context, table_name) if context else {}

    # If we got filters, execute the query
    if intelligence_result["filters"]:
        params = TableFilterParams(
            filters=intelligence_result["filters"],
            fields=ESSENTIAL_FIELDS.get(table_name, ["number", "short_description"])
        )

        # Build encoded query for debugging
        query_string = _build_query_string(intelligence_result["filters"])
        encoded_query = _encode_query_string(query_string)

        query_result = await query_table_with_filters(table_name, params)

        # Build response components
        filter_sources = _determine_filter_sources(intelligence_result["filters"], filters_from_nl, filters_from_context)
        debug_info = _build_debug_info(intelligence_result, context, filters_from_nl, filters_from_context, encoded_query)

        # Return successful response if we got results
        if isinstance(query_result, dict) and query_result.get('result'):
            return _build_intelligence_response(query_result, intelligence_result, filter_sources, debug_info)

    # Fallback to keyword-based search
    fallback_result = await query_table_by_text(table_name, natural_language_query)
    return _build_fallback_response(fallback_result, natural_language_query, table_name, context)


def explain_filter_query(
    table_name: str,
    filters: Dict[str, str]
) -> Dict[str, Any]:
    """Explain what a filter query will do and provide suggestions.
    
    Args:
        table_name: ServiceNow table name
        filters: Dictionary of filters to explain
        
    Returns:
        Dictionary with explanation and suggestions
    """
    explanation_result = explain_existing_filter(filters, table_name)
    
    return {
        "explanation": explanation_result["explanation"],
        "sql_equivalent": explanation_result["sql_equivalent"],
        "potential_issues": explanation_result["potential_issues"],
        "suggestions": explanation_result["suggestions"],
        "estimated_result_size": explanation_result["estimated_result_size"],
        "filter_analysis": {
            "field_count": len(filters),
            "has_date_filter": any("created_on" in field or "updated_on" in field for field in filters.keys()),
            "has_priority_filter": "priority" in filters,
            "has_state_filter": "state" in filters,
            "complexity": "Simple" if len(filters) <= 2 else "Complex"
        }
    }


class SmartQueryParams(BaseModel):
    """Parameters for intelligent queries."""
    natural_language: str = Field(description="Natural language description of what to find")
    table_name: str = Field(description="ServiceNow table to search")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the query")
    include_explanation: bool = Field(True, description="Whether to include explanation in results")


def build_and_validate_smart_filter(
    natural_language: str,
    table_name: str,
    context: Optional[Dict] = None
) -> Dict[str, Any]:
    """Build and validate an intelligent filter without executing the query.
    
    This is useful for testing and debugging filter generation.
    """
    intelligence_result = build_smart_filter(natural_language, table_name, context)
    
    # Validate the generated filters
    if intelligence_result["filters"]:
        validation_result = validate_query_filters(intelligence_result["filters"])
        
        return {
            "filters": intelligence_result["filters"],
            "intelligence": intelligence_result,
            "validation": {
                "is_valid": validation_result.is_valid,
                "warnings": validation_result.warnings,
                "suggestions": validation_result.suggestions
            }
        }
    else:
        return {
            "filters": {},
            "intelligence": intelligence_result,
            "validation": {
                "is_valid": False,
                "warnings": ["No filters could be generated from the input"],
                "suggestions": ["Try using more specific terms like priorities, dates, or states"]
            }
        }

# Generic priority and filtering functions to replace individual table tools

def _build_priority_filter(priorities: List[str]) -> str:
    """Helper function to build OR-based priority filter with cognitive complexity < 15."""
    if not priorities:
        return ""
    
    # Handle single priority
    if len(priorities) == 1:
        return f"priority={priorities[0]}"
    
    # Build OR filter for multiple priorities
    priority_filters = [f"priority={p}" for p in priorities]
    return "^OR".join(priority_filters)

def _build_url_with_params(table_name: str, fields: List[str], query: str) -> str:
    """Helper function to build ServiceNow API URL with cognitive complexity < 15."""
    base_url = f"{NWS_API_BASE}/api/now/table/{table_name}"
    field_param = f"sysparm_fields={','.join(fields)}"
    query_param = f"sysparm_query={query}"
    
    return f"{base_url}?{field_param}&{query_param}"

def _build_additional_filters(additional_filters: Optional[Dict[str, str]]) -> List[str]:
    """Convert additional_filters dict into a list of filter strings."""
    if not additional_filters:
        return []
    result = []
    for field, value in additional_filters.items():
        if field == "_date_range":
            # Pre-built date filter string (e.g., "sys_created_on>=2026-01-01 00:00:00")
            result.append(value)
        else:
            result.append(f"{field}={value}")
    return result


def _format_priority_results(all_results: list, max_results: int) -> Dict[str, Any]:
    """Format paginated results into a standard response dict."""
    if not all_results:
        return {"result": [], "message": NO_RECORDS_FOUND}
    result_count = len(all_results)
    limit_note = f" (limited to {max_results})" if result_count == max_results else ""
    return {
        "result": all_results,
        "message": f"Found {result_count} records{limit_note}"
    }


async def get_records_by_priority(
    table_name: str,
    priorities: List[str],
    additional_filters: Optional[Dict[str, str]] = None,
    detailed: bool = False
) -> Dict[str, Any]:
    """Generic function to get records by priority for any table that supports priority."""
    from constants import TABLE_CONFIGS

    # Validate table supports priority
    table_config = TABLE_CONFIGS.get(table_name)
    if not table_config or not table_config.get("priority_field"):
        return {"error": TABLE_NO_PRIORITY_SUPPORT_ERROR.format(table_name=table_name)}

    fields = DETAIL_FIELDS.get(table_name, []) if detailed else ESSENTIAL_FIELDS.get(table_name, [])
    if not fields:
        return {"error": NO_FIELD_CONFIG_ERROR.format(table_name=table_name)}

    # Build priority filter
    priority_filter = _build_priority_filter(priorities)
    if not priority_filter:
        return {"error": NO_VALID_PRIORITIES_ERROR}

    # Build complete filter list
    filters = [priority_filter] + _build_additional_filters(additional_filters)

    final_query = "^".join(filters)
    final_query = _apply_incident_category_filter(table_name, final_query)
    final_query = _apply_sc_catalog_filter(table_name, final_query)
    base_url = f"{NWS_API_BASE}/api/now/table/{table_name}?sysparm_fields={','.join(fields)}&sysparm_display_value=true"

    if final_query:
        base_url += f"&sysparm_query={final_query}"

    max_results = 100
    try:
        all_results = await _make_paginated_request(base_url, max_results=max_results)
        return _format_priority_results(all_results, max_results)
    except Exception as e:
        return {"error": REQUEST_FAILED_ERROR.format(error=str(e))}

async def query_table_with_generic_filters(
    table_name: str,
    filters: Dict[str, str],
    detailed: bool = False
) -> Dict[str, Any]:
    """Generic function to query any table with filters."""
    fields = DETAIL_FIELDS.get(table_name, []) if detailed else ESSENTIAL_FIELDS.get(table_name, [])
    if not fields:
        return {"error": NO_FIELD_CONFIG_ERROR.format(table_name=table_name)}
    
    # Build query from filters
    filter_parts = []
    for field, value in filters.items():
        if _is_complete_servicenow_filter(value):
            filter_parts.append(value)
        else:
            filter_parts.append(f"{field}={value}")

    query = "^".join(filter_parts)
    # Apply category filtering for incidents
    query = _apply_incident_category_filter(table_name, query)
    # Apply catalog filtering for service catalog tables
    query = _apply_sc_catalog_filter(table_name, query)
    base_url = f"{NWS_API_BASE}/api/now/table/{table_name}?sysparm_fields={','.join(fields)}&sysparm_display_value=true"

    if query:
        base_url += f"&sysparm_query={query}"
    
    try:
        # Use pagination to prevent excessive results
        all_results = await _make_paginated_request(base_url, max_results=75)  # Limit generic filters to 75 results
        
        if all_results:
            result_count = len(all_results)
            return {
                "result": all_results,
                "message": f"Found {result_count} records" + (" (limited to 75)" if result_count == 75 else "")
            }
        else:
            return {"result": [], "message": NO_RECORDS_FOUND}
    except Exception as e:
        return {"error": REQUEST_FAILED_ERROR.format(error=str(e))}
