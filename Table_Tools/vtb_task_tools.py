from service_now_api_oauth import make_nws_request, NWS_API_BASE
from typing import Any, Dict, Optional, List
from utils import extract_keywords
import httpx
from constants import JSON_HEADERS, COMMON_VTB_TASK_FIELDS, DETAILED_VTB_TASK_FIELDS, NO_RECORDS_FOUND, RECORD_NOT_FOUND, CONNECTION_ERROR, NO_DESCRIPTION_FOUND

async def _get_authenticated_headers() -> Dict[str, str]:
    """Get headers with appropriate authentication."""
    from service_now_api_oauth import _should_use_oauth
    from oauth_client import get_oauth_client
    
    headers = JSON_HEADERS.copy()
    
    if _should_use_oauth():
        oauth_client = get_oauth_client()
        auth_headers = await oauth_client.get_auth_headers()
        headers.update(auth_headers)
    
    return headers

async def _make_authenticated_request(
    method: str, 
    url: str, 
    json_data: Optional[Dict] = None,
    operation: str = "operation"
) -> Dict[str, Any] | str:
    """Make an authenticated HTTP request with error handling."""
    from service_now_api_oauth import SERVICENOW_USERNAME, SERVICENOW_PASSWORD, _should_use_oauth
    
    headers = await _get_authenticated_headers()
    
    async with httpx.AsyncClient(verify=True) as client:
        try:
            if _should_use_oauth():
                response = await client.request(method, url, json=json_data, headers=headers, timeout=30.0)
            else:
                auth = (SERVICENOW_USERNAME, SERVICENOW_PASSWORD)
                response = await client.request(method, url, json=json_data, headers=headers, auth=auth, timeout=30.0)
            
            response.raise_for_status()
            result = response.json()
            
            if result and result.get('result'):
                return result['result']
            else:
                return result if result else f"Private Task {operation} successful but no data returned."
                
        except httpx.HTTPStatusError as e:
            return _handle_http_error(e, operation)
        except Exception:
            return f"Error during private task {operation}: Request failed"

def _handle_http_error(error: httpx.HTTPStatusError, operation: str) -> str:
    """Handle HTTP errors consistently."""
    status_code = error.response.status_code
    
    error_messages = {
        401: f"Error during private task {operation}: Authentication failed",
        403: f"Error during private task {operation}: Access denied", 
        400: f"Error during private task {operation}: Invalid request data",
        404: f"Error during private task {operation}: Task not found"
    }
    
    return error_messages.get(status_code, f"Error during private task {operation}: Server error")

def _prepare_task_create_data(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare and validate data for task creation."""
    create_data = {
        'short_description': task_data['short_description'],
        'state': task_data.get('state', '1'),  # Default to New/Open state
        'priority': task_data.get('priority', '3'),  # Default to moderate priority
    }
    
    # Add optional fields if provided
    optional_fields = [
        'description', 'assigned_to', 'assignment_group', 'due_date', 
        'parent', 'comments', 'work_notes'
    ]
    
    for field in optional_fields:
        if field in task_data:
            create_data[field] = task_data[field]
    
    return create_data

async def _get_task_sys_id(task_number: str) -> str | None:
    """Get the sys_id for a task by its number."""
    sys_id_url = f"{NWS_API_BASE}/api/now/table/vtb_task?sysparm_fields=sys_id&sysparm_query=number={task_number}"
    sys_id_data = await make_nws_request(sys_id_url)
    
    if not sys_id_data or not sys_id_data.get('result') or not sys_id_data['result']:
        return None
    
    return sys_id_data['result'][0]['sys_id']

async def similar_private_tasks_for_text(input_text: str) -> dict[str, Any] | str:
    """Get private task records based on input text."""
    keywords = extract_keywords(input_text)
    for keyword in keywords:
        url = f"{NWS_API_BASE}/api/now/table/vtb_task?sysparm_fields={','.join(COMMON_VTB_TASK_FIELDS)}&sysparm_query=short_descriptionCONTAINS{keyword}"
        data = await make_nws_request(url)
        if data and data.get('result') and len(data['result']) > 0:
            return data
    return NO_RECORDS_FOUND

async def get_short_desc_for_private_task(input_private_task: str) -> dict[str, Any] | str:
    """Get short_description for a given private task based on input private task number."""
    url = f"{NWS_API_BASE}/api/now/table/vtb_task?sysparm_fields=short_description&sysparm_query=number={input_private_task}"
    data = await make_nws_request(url)
    return data if data else RECORD_NOT_FOUND

async def similar_private_tasks_for_private_task(input_private_task: str) -> dict[str, Any] | str:
    """Get similar private task records based on given private task."""
    try:
        desc_data = await get_short_desc_for_private_task(input_private_task)
        if isinstance(desc_data, dict) and desc_data.get('result'):
            if len(desc_data['result']) > 0:
                desc_text = desc_data['result'][0].get('short_description', '')
                if desc_text:
                    return await similar_private_tasks_for_text(desc_text)
        return NO_DESCRIPTION_FOUND
    except Exception:
        return CONNECTION_ERROR

async def get_private_task_details(input_private_task: str) -> dict[str, Any] | str:
    """Get detailed information for a given private task based on input private task number.
    
    Args:
        input_private_task: The private task number.
    
    Returns:
        A dictionary containing private task details or an error message if the request fails.
    """
    url = f"{NWS_API_BASE}/api/now/table/vtb_task?sysparm_fields={','.join(DETAILED_VTB_TASK_FIELDS)}&sysparm_query=number={input_private_task}"
    data = await make_nws_request(url)
    if data and data.get('result'):
        results = data['result']
        if isinstance(results, list) and results:
            return results[0]
        elif isinstance(results, dict):
            return results
    return "Unable to fetch private task details or no private task found."

async def create_private_task(task_data: Dict[str, Any]) -> dict[str, Any] | str:
    """Create a new private task record in ServiceNow.
    
    Args:
        task_data: Dictionary containing the private task data to create.
                  Required fields: short_description
                  Optional fields: description, priority, assigned_to, assignment_group, due_date, parent, etc.
    
    Returns:
        A dictionary containing the created private task details or an error message if the request fails.
    """
    if not task_data.get('short_description'):
        return "Error: short_description is required to create a private task."
    
    create_data = _prepare_task_create_data(task_data)
    url = f"{NWS_API_BASE}/api/now/table/vtb_task"
    
    return await _make_authenticated_request("POST", url, create_data, "creation")

async def update_private_task(task_number: str, update_data: Dict[str, Any]) -> dict[str, Any] | str:
    """Update an existing private task record in ServiceNow.
    
    Args:
        task_number: The private task number to update.
        update_data: Dictionary containing the fields to update.
    
    Returns:
        A dictionary containing the updated private task details or an error message if the request fails.
    """
    if not update_data:
        return "Error: No update data provided."
    
    sys_id = await _get_task_sys_id(task_number)
    if not sys_id:
        return "Private Task not found for update."
    
    url = f"{NWS_API_BASE}/api/now/table/vtb_task/{sys_id}"
    return await _make_authenticated_request("PUT", url, update_data, "update")

async def get_private_tasks_by_filter(filters: Dict[str, str], fields: Optional[List[str]] = None) -> dict[str, Any] | str:
    """Get private task records with custom filters.
    
    Args:
        filters: Dictionary of field-value pairs for filtering.
        fields: Optional list of fields to return.
    
    Returns:
        A dictionary containing filtered private task records or an error message.
    """
    query_fields = fields or COMMON_VTB_TASK_FIELDS
    query_parts = []
    
    if filters:
        for field, value in filters.items():
            if field.endswith('_gte'):
                base_field = field[:-4]
                query_parts.append(f"{base_field}>={value}")
            elif field.endswith('_lte'):
                base_field = field[:-4]
                query_parts.append(f"{base_field}<={value}")
            else:
                query_parts.append(f"{field}={value}")
    
    sysparm_query = "^".join(query_parts) if query_parts else ""
    url = f"{NWS_API_BASE}/api/now/table/vtb_task?sysparm_fields={','.join(query_fields)}"
    
    if sysparm_query:
        url += f"&sysparm_query={sysparm_query}"
    
    data = await make_nws_request(url)
    return data if data else NO_RECORDS_FOUND