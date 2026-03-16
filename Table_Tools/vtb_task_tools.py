from service_now_api_oauth import make_nws_request, NWS_API_BASE
from typing import Any, Dict, Optional
import httpx
from constants import (
    ERROR_SHORT_DESC_REQUIRED,
    ERROR_NO_UPDATE_DATA,
    PRIVATE_TASK_NOT_FOUND_UPDATE,
    ERROR_PRIVATE_TASK_REQUEST_FAILED,
    ERROR_PRIVATE_TASK_AUTH_FAILED,
    ERROR_PRIVATE_TASK_ACCESS_DENIED,
    ERROR_PRIVATE_TASK_INVALID_REQUEST,
    ERROR_PRIVATE_TASK_NOT_FOUND,
    ERROR_PRIVATE_TASK_SERVER_ERROR
)

async def _get_authenticated_headers() -> Dict[str, str]:
    """Get headers with OAuth authentication."""
    from oauth_client import get_oauth_client

    oauth_client = get_oauth_client()
    return await oauth_client.get_auth_headers()

async def _make_authenticated_request(
    method: str,
    url: str,
    json_data: Optional[Dict] = None,
    operation: str = "operation"
) -> Dict[str, Any] | str:
    """Make an authenticated HTTP request with error handling."""
    headers = await _get_authenticated_headers()

    async with httpx.AsyncClient(verify=True) as client:
        try:
            response = await client.request(method, url, json=json_data, headers=headers, timeout=30.0)
            response.raise_for_status()
            result = response.json()
            
            if result and result.get('result'):
                return result['result']
            else:
                return result if result else f"Private Task {operation} successful but no data returned."
                
        except httpx.HTTPStatusError as e:
            return _handle_http_error(e, operation)
        except Exception:
            return ERROR_PRIVATE_TASK_REQUEST_FAILED.format(operation=operation)

def _handle_http_error(error: httpx.HTTPStatusError, operation: str) -> str:
    """Handle HTTP errors consistently."""
    status_code = error.response.status_code
    
    error_messages = {
        401: ERROR_PRIVATE_TASK_AUTH_FAILED.format(operation=operation),
        403: ERROR_PRIVATE_TASK_ACCESS_DENIED.format(operation=operation),
        400: ERROR_PRIVATE_TASK_INVALID_REQUEST.format(operation=operation),
        404: ERROR_PRIVATE_TASK_NOT_FOUND.format(operation=operation)
    }

    return error_messages.get(status_code, ERROR_PRIVATE_TASK_SERVER_ERROR.format(operation=operation))

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
        return ERROR_SHORT_DESC_REQUIRED
    
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
        return ERROR_NO_UPDATE_DATA
    
    sys_id = await _get_task_sys_id(task_number)
    if not sys_id:
        return PRIVATE_TASK_NOT_FOUND_UPDATE
    
    url = f"{NWS_API_BASE}/api/now/table/vtb_task/{sys_id}"
    return await _make_authenticated_request("PATCH", url, update_data, "update")