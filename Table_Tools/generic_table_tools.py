from service_now_api_oauth import make_nws_request, NWS_API_BASE
from utils import extract_keywords
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field

# Optimized field sets - only essential fields
ESSENTIAL_FIELDS = {
    "incident": ["number", "short_description", "priority", "state"],
    "change_request": ["number", "short_description", "priority", "state"], 
    "universal_request": ["number", "short_description", "priority", "state"],
    "kb_knowledge": ["number", "short_description", "kb_category", "state"],
    "vtb_task": ["number", "short_description", "priority", "state"]
}

DETAIL_FIELDS = {
    "incident": ["number", "short_description", "priority", "state", "sys_created_on", "assigned_to", "assignment_group", "work_notes", "comments"],
    "change_request": ["number", "short_description", "priority", "state", "sys_created_on", "assigned_to", "assignment_group", "work_notes", "comments"],
    "universal_request": ["number", "short_description", "priority", "state", "sys_created_on", "assigned_to", "assignment_group", "comments"],
    "kb_knowledge": ["number", "short_description", "kb_category", "state", "sys_created_on", "assigned_to"],
    "vtb_task": ["number", "short_description", "priority", "state", "sys_created_on", "assigned_to", "assignment_group", "work_notes", "comments"]
}

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
    return "No records found."

async def get_record_description(table_name: str, record_number: str) -> dict[str, Any] | str:
    """Generic function to get short_description for any record."""
    url = f"{NWS_API_BASE}/api/now/table/{table_name}?sysparm_fields=short_description&sysparm_query=number={record_number}"
    data = await make_nws_request(url)
    return data if data else "Record not found."

async def get_record_details(table_name: str, record_number: str) -> dict[str, Any] | str:
    """Generic function to get detailed information for any record."""
    fields = DETAIL_FIELDS.get(table_name, ["number", "short_description"])
    url = f"{NWS_API_BASE}/api/now/table/{table_name}?sysparm_fields={','.join(fields)}&sysparm_query=number={record_number}&sysparm_display_value=true"
    data = await make_nws_request(url)
    return data if data else "Record not found."

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
    except Exception as e:
        return "Connection error: Request failed"

class TableFilterParams(BaseModel):
    filters: Optional[Dict[str, str]] = Field(None, description="Field-value pairs for filtering")
    fields: Optional[List[str]] = Field(None, description="Fields to return")

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
    
    query_parts = []
    if params.filters:
        for field, value in params.filters.items():
            # Handle direct operator syntax (e.g., ">=javascript:gs.daysAgoStart(14)")
            if isinstance(value, str) and any(op in value for op in ['>=', '<=', '>', '<', '=']):
                # Value already contains the operator, use as-is
                query_parts.append(f"{field}{value}")
            elif field.endswith('_gte'):
                base_field = field[:-4]
                query_parts.append(f"{base_field}>={value}")
            elif field.endswith('_lte'):
                base_field = field[:-4]
                query_parts.append(f"{base_field}<={value}")
            elif field.endswith('_gt'):
                base_field = field[:-3]
                query_parts.append(f"{base_field}>{value}")
            elif field.endswith('_lt'):
                base_field = field[:-3]
                query_parts.append(f"{base_field}<{value}")
            elif 'CONTAINS' in field.upper():
                # Handle CONTAINS operations (field already formatted)
                query_parts.append(f"{field}")
            else:
                # Exact match
                query_parts.append(f"{field}={value}")
    
    query_string = "^".join(query_parts) if query_parts else ""
    
    # URL encode the query but preserve ServiceNow JavaScript functions
    from urllib.parse import quote
    encoded_query = quote(query_string, safe='=<>&^():.')
    
    url = f"{NWS_API_BASE}/api/now/table/{table_name}?sysparm_fields={','.join(fields)}&sysparm_display_value=true"
    
    if encoded_query:
        url += f"&sysparm_query={encoded_query}"
    
    data = await make_nws_request(url)
    return data if data else "No records found."