from service_now_api_oauth import make_nws_request, NWS_API_BASE
from utils import extract_keywords
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
from constants import ESSENTIAL_FIELDS, DETAIL_FIELDS, NO_RECORDS_FOUND, RECORD_NOT_FOUND
from query_validation import (
    validate_query_filters, 
    validate_result_count, 
    build_pagination_params,
    suggest_query_improvements
)
from query_intelligence import QueryIntelligence, QueryExplainer, build_smart_filter, explain_existing_filter

async def query_table_by_text(table_name: str, input_text: str, detailed: bool = False) -> dict[str, Any] | str:
    """Generic function to query any ServiceNow table by text similarity."""
    fields = DETAIL_FIELDS[table_name] if detailed else ESSENTIAL_FIELDS[table_name]
    keywords = extract_keywords(input_text)
    
    for keyword in keywords:
        url = f"{NWS_API_BASE}/api/now/table/{table_name}?sysparm_fields={','.join(fields)}&sysparm_query=short_descriptionCONTAINS{keyword}"
        data = await make_nws_request(url)
        # Check if we got data AND it contains actual results
        if data and data.get('result') and len(data['result']) > 0:
            return data
    return NO_RECORDS_FOUND

async def get_record_description(table_name: str, record_number: str) -> dict[str, Any] | str:
    """Generic function to get short_description for any record."""
    url = f"{NWS_API_BASE}/api/now/table/{table_name}?sysparm_fields=short_description&sysparm_query=number={record_number}"
    data = await make_nws_request(url)
    return data if data else RECORD_NOT_FOUND

async def get_record_details(table_name: str, record_number: str) -> dict[str, Any] | str:
    """Generic function to get detailed information for any record."""
    fields = DETAIL_FIELDS.get(table_name, ["number", "short_description"])
    url = f"{NWS_API_BASE}/api/now/table/{table_name}?sysparm_fields={','.join(fields)}&sysparm_query=number={record_number}&sysparm_display_value=true"
    data = await make_nws_request(url)
    return data if data else RECORD_NOT_FOUND

async def find_similar_records(table_name: str, record_number: str) -> dict[str, Any] | str:
    """Generic function to find similar records based on a given record's description."""
    try:
        desc_data = await get_record_description(table_name, record_number)
        if isinstance(desc_data, str):
            return desc_data
        
        # Extract description text from the response
        if desc_data and desc_data.get('result') and len(desc_data['result']) > 0:
            desc_text = desc_data['result'][0].get('short_description', '')
            if desc_text and desc_text.strip():
                return await query_table_by_text(table_name, desc_text)
        return "No description found."
    except Exception:
        return "Connection error: Request failed"

class TableFilterParams(BaseModel):
    filters: Optional[Dict[str, str]] = Field(None, description="Field-value pairs for filtering")
    fields: Optional[List[str]] = Field(None, description="Fields to return")

def _has_operator_in_value(value: str) -> bool:
    """Check if value already contains a comparison operator."""
    return isinstance(value, str) and any(op in value for op in ['>=', '<=', '>', '<', '='])

def _is_complete_servicenow_filter(value: str) -> bool:
    """Check if value is already a complete ServiceNow filter (e.g., priority=1^ORpriority=2)."""
    return isinstance(value, str) and ('^OR' in value or 'ON' in value)

def _parse_date_range_from_text(text: str) -> Optional[tuple]:
    """Parse date range from natural language text.
    
    Handles formats like:
    - "Week 35 2025" or "week 35 of 2025"
    - "August 25-31, 2025" 
    - "2025-08-25 to 2025-08-31"
    - "last week", "this week"
    """
    import re
    from datetime import datetime, timedelta
    
    text = text.lower().strip()
    
    # Handle "Week X YYYY" format
    week_match = re.search(r'week\s+(\d+)\s+(?:of\s+)?(\d{4})', text)
    if week_match:
        week_num = int(week_match.group(1))
        year = int(week_match.group(2))
        
        # Calculate start date of the week (assuming week starts on Monday)
        # Week 1 is the first week with at least 4 days in the new year
        jan_4 = datetime(year, 1, 4)
        week_start = jan_4 - timedelta(days=jan_4.weekday()) + timedelta(weeks=week_num - 1)
        week_end = week_start + timedelta(days=6)
        
        return (week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d'))
    
    # Handle "Month DD-DD, YYYY" format
    month_range_match = re.search(r'(\w+)\s+(\d+)-(\d+),\s*(\d{4})', text)
    if month_range_match:
        month_name = month_range_match.group(1)
        start_day = int(month_range_match.group(2))
        end_day = int(month_range_match.group(3))
        year = int(month_range_match.group(4))
        
        # Convert month name to number
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        month_num = months.get(month_name.lower())
        if month_num:
            start_date = f"{year}-{month_num:02d}-{start_day:02d}"
            end_date = f"{year}-{month_num:02d}-{end_day:02d}"
            return (start_date, end_date)
    
    # Handle "YYYY-MM-DD to YYYY-MM-DD" format
    date_range_match = re.search(r'(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})', text)
    if date_range_match:
        return (date_range_match.group(1), date_range_match.group(2))
    
    return None

def _parse_priority_list(value: str) -> str:
    """Parse priority list and convert to proper OR syntax.
    
    Handles formats like:
    - "1,2" -> "priority=1^ORpriority=2"
    - ["1", "2"] as string -> "priority=1^ORpriority=2"
    - "P1,P2" -> "priority=1^ORpriority=2"
    """
    if not isinstance(value, str):
        return str(value)
    
    # Handle comma-separated values
    if "," in value and "^OR" not in value:
        # Clean up the value - remove brackets, quotes, etc.
        clean_value = value.strip("[]\"'")
        priorities = [p.strip().strip("\"'") for p in clean_value.split(",")]
        
        # Convert P1/P2 notation to numbers
        priority_nums = []
        for p in priorities:
            if p.upper().startswith("P"):
                priority_nums.append(p[1:])  # Remove 'P' prefix
            else:
                priority_nums.append(p)
        
        # Build OR syntax
        priority_conditions = [f"priority={p}" for p in priority_nums]
        return "^OR".join(priority_conditions)
    
    return value

def _parse_caller_exclusions(value: str) -> str:
    """Parse caller exclusion list and convert to NOT EQUALS syntax.
    
    Handles formats like:
    - "logicmonitor" -> "caller_id!=1727339e47d99190c43d3171e36d43ad"
    - "sys_id1,sys_id2" -> "caller_id!=sys_id1^caller_id!=sys_id2"
    """
    if not isinstance(value, str):
        return str(value)
    
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
        exclusions = [f"caller_id!={caller_id}" for caller_id in caller_ids]
        return "^".join(exclusions)
    
    # Single caller exclusion
    if not value.startswith("caller_id!="):
        return f"caller_id!={value}"
    
    return value

def _build_query_condition(field: str, value: str) -> str:
    """Build a single query condition based on field and value."""
    # Handle special complete query case
    if field == "_complete_query":
        return value
    
    # Handle date range parsing for sys_created_on field
    if field == "sys_created_on" and not value.startswith(">=") and "BETWEEN" not in value:
        date_range = _parse_date_range_from_text(value)
        if date_range:
            start_date, end_date = date_range
            return f"sys_created_onBETWEENjavascript:gs.dateGenerate('{start_date}','00:00:00')@javascript:gs.dateGenerate('{end_date}','23:59:59')"
    
    # Handle priority list parsing
    if field == "priority" and ("," in value or value.upper().startswith("P")):
        return _parse_priority_list(value)
    
    # Handle caller exclusions
    if field == "exclude_caller" or field == "caller_exclusion":
        return _parse_caller_exclusions(value)
    
    # Handle complete ServiceNow filters (e.g., "priority=1^ORpriority=2")
    if _is_complete_servicenow_filter(value):
        return value
    
    # Handle direct operator syntax (e.g., ">=javascript:gs.daysAgoStart(14)")
    if _has_operator_in_value(value):
        return f"{field}{value}"
    
    # Handle suffix-based operators
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
        # Handle CONTAINS operations (field already formatted)
        return f"{field}"
    else:
        # Exact match
        return f"{field}={value}"

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
    max_results: int = 1000,
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


async def query_table_with_filters(table_name: str, params: TableFilterParams) -> dict[str, Any] | str:
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
    
    return NO_RECORDS_FOUND


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
    """
    # Build intelligent filter
    intelligence_result = build_smart_filter(natural_language_query, table_name, context)
    
    # If we got filters, execute the query
    if intelligence_result["filters"]:
        params = TableFilterParams(
            filters=intelligence_result["filters"],
            fields=ESSENTIAL_FIELDS.get(table_name, ["number", "short_description"])
        )
        
        query_result = await query_table_with_filters(table_name, params)
        
        # Combine query results with intelligence metadata
        if isinstance(query_result, dict) and query_result.get('result'):
            return {
                "result": query_result["result"],
                "intelligence": {
                    "explanation": intelligence_result["explanation"],
                    "confidence": intelligence_result["confidence"],
                    "suggestions": intelligence_result["suggestions"],
                    "template_used": intelligence_result.get("template_used"),
                    "sql_equivalent": intelligence_result.get("sql_equivalent"),
                    "filters_used": intelligence_result["filters"]
                }
            }
    
    # Fallback to keyword-based search if no intelligent filters were generated
    fallback_result = await query_table_by_text(table_name, natural_language_query)
    
    return {
        "result": fallback_result.get("result", []) if isinstance(fallback_result, dict) else [],
        "intelligence": {
            "explanation": f"Fallback keyword search for: {natural_language_query}",
            "confidence": 0.3,
            "suggestions": ["Try being more specific with priorities, dates, or states"],
            "template_used": None,
            "sql_equivalent": f"SELECT * FROM {table_name} WHERE short_description CONTAINS '{natural_language_query}'",
            "filters_used": {"short_description": f"short_descriptionCONTAINS{natural_language_query}"}
        }
    }


async def explain_filter_query(
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


async def build_and_validate_smart_filter(
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