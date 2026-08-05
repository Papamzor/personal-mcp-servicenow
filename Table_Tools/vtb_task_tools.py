from http_layer import make_nws_request, NWS_API_BASE
from typing import Any, Dict
import anyio
import httpx
from .write_helpers import map_http_error, unwrap_write_response
from constants import (
    ERROR_SHORT_DESC_REQUIRED,
    ERROR_NO_UPDATE_DATA,
    PRIVATE_TASK_NOT_FOUND_UPDATE,
    ERROR_PRIVATE_TASK_REQUEST_FAILED,
    ERROR_PRIVATE_TASK_AUTH_FAILED,
    ERROR_PRIVATE_TASK_ACCESS_DENIED,
    ERROR_PRIVATE_TASK_INVALID_REQUEST,
    ERROR_PRIVATE_TASK_NOT_FOUND,
    ERROR_PRIVATE_TASK_SERVER_ERROR,
    ERROR_PRIVATE_TASK_WRITE_UNCONFIRMED,
    VTB_WRITE_TIMEOUT_SECONDS,
    VTB_UPDATABLE_FIELDS
)

def _handle_http_error(error: httpx.HTTPStatusError, operation: str) -> str:
    """Handle HTTP errors consistently."""
    error_map = {
        401: ERROR_PRIVATE_TASK_AUTH_FAILED.format(operation=operation),
        403: ERROR_PRIVATE_TASK_ACCESS_DENIED.format(operation=operation),
        400: ERROR_PRIVATE_TASK_INVALID_REQUEST.format(operation=operation),
        404: ERROR_PRIVATE_TASK_NOT_FOUND.format(operation=operation),
    }
    return map_http_error(
        error, error_map, ERROR_PRIVATE_TASK_SERVER_ERROR.format(operation=operation)
    )

def _unwrap_write_response(result: Any, operation: str) -> Dict[str, Any] | str:
    """Extract the inner result payload from a write response."""
    return unwrap_write_response(
        result, ERROR_PRIVATE_TASK_WRITE_UNCONFIRMED.format(operation=operation)
    )

async def _write_private_task(
    method: str,
    url: str,
    payload: Dict[str, Any],
    operation: str,
) -> Dict[str, Any] | str:
    """Send a write request through make_nws_request, mapping errors locally."""
    try:
        with anyio.fail_after(VTB_WRITE_TIMEOUT_SECONDS):
            result = await make_nws_request(url, method=method, json_data=payload)
    except httpx.HTTPStatusError as e:
        return _handle_http_error(e, operation)
    except Exception:
        return ERROR_PRIVATE_TASK_REQUEST_FAILED.format(operation=operation)

    return _unwrap_write_response(result, operation)

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

    return await _write_private_task("POST", url, create_data, "creation")

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

    bad = [k for k in update_data if k not in VTB_UPDATABLE_FIELDS]
    if bad:
        return f"Rejected non-updatable field(s): {', '.join(bad)}"

    sys_id = await _get_task_sys_id(task_number)
    if not sys_id:
        return PRIVATE_TASK_NOT_FOUND_UPDATE

    url = f"{NWS_API_BASE}/api/now/table/vtb_task/{sys_id}"
    return await _write_private_task("PATCH", url, update_data, "update")
