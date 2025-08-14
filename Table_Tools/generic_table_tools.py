from service_now_api_oauth import make_nws_request, NWS_API_BASE
from utils import extract_keywords
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field

# Optimized field sets - only essential fields
ESSENTIAL_FIELDS = {
    "incident": ["number", "short_description", "priority", "state"],
    "change_request": ["number", "short_description", "priority", "state"], 
    "universal_request": ["number", "short_description", "priority", "state"],
    "kb_knowledge": ["number", "short_description", "kb_category", "state"]
}

DETAIL_FIELDS = {
    "incident": ["number", "short_description", "priority", "state", "sys_created_on", "assigned_to", "assignment_group"],
    "change_request": ["number", "short_description", "priority", "state", "sys_created_on", "assigned_to", "assignment_group"],
    "universal_request": ["number", "short_description", "priority", "state", "sys_created_on", "assigned_to", "assignment_group"],
    "kb_knowledge": ["number", "short_description", "kb_category", "state", "sys_created_on", "assigned_to"]
}

async def query_table_by_text(table_name: str, input_text: str, detailed: bool = False) -> dict[str, Any] | str:
    """Generic function to query any ServiceNow table by text similarity."""
    fields = DETAIL_FIELDS[table_name] if detailed else ESSENTIAL_FIELDS[table_name]
    keywords = extract_keywords(input_text)
    
    for keyword in keywords:
        url = f"{NWS_API_BASE}/api/now/table/{table_name}?sysparm_fields={','.join(fields)}&sysparm_query=short_descriptionCONTAINS{keyword}"
        data = await make_nws_request(url)
        if data:
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
    url = f"{NWS_API_BASE}/api/now/table/{table_name}?sysparm_fields={','.join(fields)}&sysparm_query=number={record_number}"
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
        return f"Connection error: {str(e)}"

class TableFilterParams(BaseModel):
    filters: Optional[Dict[str, str]] = Field(None, description="Field-value pairs for filtering")
    fields: Optional[List[str]] = Field(None, description="Fields to return")

async def query_table_with_filters(table_name: str, params: TableFilterParams) -> dict[str, Any] | str:
    """Generic function to query table with custom filters and fields."""
    fields = params.fields or ESSENTIAL_FIELDS.get(table_name, ["number", "short_description"])
    
    query_parts = []
    if params.filters:
        for field, value in params.filters.items():
            query_parts.append(f"{field}={value}")
    
    query_string = "^".join(query_parts) if query_parts else ""
    url = f"{NWS_API_BASE}/api/now/table/{table_name}?sysparm_fields={','.join(fields)}"
    
    if query_string:
        url += f"&sysparm_query={query_string}"
    
    data = await make_nws_request(url)
    return data if data else "No records found."