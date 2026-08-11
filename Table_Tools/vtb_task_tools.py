"""Private task (vtb_task) CRUD.

Read-failure contract (v4.4 Tier 0.3). A failed GET raises
`ServiceNowRequestError` instead of returning None. There is exactly one read
here — the pre-write `sys_id` lookup — and it is the sensitive kind (decision
(d)): `_get_task_sys_id` returns None ONLY for a task that genuinely does not
exist, and a failed lookup propagates. `update_private_task` maps the raise to
`error.to_error_dict()` and keeps `PRIVATE_TASK_NOT_FOUND_UPDATE` for a real
absence, so an update no longer tells the user their task does not exist because
the lookup timed out.
"""
from http_layer import ServiceNowRequestError, make_nws_request, NWS_API_BASE
from filter import QueryValueError, encode_query_value
from typing import Any, Dict
import anyio
import httpx
from .response import error_response
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

def _handle_http_error(error: httpx.HTTPStatusError, operation: str) -> Dict[str, Any]:
    """Map an HTTP error to the {"error": {code, message}} contract shape."""
    error_map = {
        401: ERROR_PRIVATE_TASK_AUTH_FAILED.format(operation=operation),
        403: ERROR_PRIVATE_TASK_ACCESS_DENIED.format(operation=operation),
        400: ERROR_PRIVATE_TASK_INVALID_REQUEST.format(operation=operation),
        404: ERROR_PRIVATE_TASK_NOT_FOUND.format(operation=operation),
    }
    return map_http_error(
        error, error_map, ERROR_PRIVATE_TASK_SERVER_ERROR.format(operation=operation)
    )

def _unwrap_write_response(result: Any, operation: str) -> Dict[str, Any]:
    """Extract the inner result payload into the §3.1 write shape."""
    return unwrap_write_response(
        result,
        ERROR_PRIVATE_TASK_WRITE_UNCONFIRMED.format(operation=operation),
        success_message=f"Private task {operation} succeeded.",
    )

async def _write_private_task(
    method: str,
    url: str,
    payload: Dict[str, Any],
    operation: str,
) -> Dict[str, Any]:
    """Send a write request through make_nws_request, mapping errors locally."""
    try:
        with anyio.fail_after(VTB_WRITE_TIMEOUT_SECONDS):
            result = await make_nws_request(url, method=method, json_data=payload)
    except httpx.HTTPStatusError as e:
        return _handle_http_error(e, operation)
    except Exception:
        return error_response("INTERNAL", ERROR_PRIVATE_TASK_REQUEST_FAILED.format(operation=operation))

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
    """Get the sys_id for a task by its number, or None if no such task exists.

    None means "looked, absent" and nothing else (decision (d)). A failed read
    raises `ServiceNowRequestError` for the caller to map — returning None for it
    is what let a timeout report the task as missing, on the one code path where
    that answer stops a write.

    The number is escaped (v4.4.1) because this lookup chooses the record the
    PATCH then writes to: a `^` in it could OR-in a second condition and resolve
    to a different task. Unrepresentable, so refused rather than escaped.
    """
    sys_id_url = (
        f"{NWS_API_BASE}/api/now/table/vtb_task"
        f"?sysparm_fields=sys_id&sysparm_query=number={encode_query_value(task_number)}"
    )
    sys_id_data = await make_nws_request(sys_id_url)

    if not sys_id_data or not sys_id_data.get('result') or not sys_id_data['result']:
        return None

    return sys_id_data['result'][0]['sys_id']

async def create_private_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a NEW private task (vtb_task) record.

    WHEN TO USE: the user wants a brand-new private task opened.
    WHEN NOT TO USE: to modify a task that already exists (its VTB number is
        known) — use update_private_task instead.
    PREFER OVER: nothing; this is the only insert path for vtb_task.
    TABLES: vtb_task only (the sole table with CRUD support).
    SIDE EFFECT: WRITE — inserts one record. Not idempotent.
    EXAMPLE: create a private task to review the firewall configuration.

    Args:
        task_data: Dictionary containing the private task data to create.
                  Required fields: short_description
                  Optional fields: description, priority, assigned_to, assignment_group, due_date, parent, etc.

    Returns:
        {"record": {...created task...}, "message": ...} on success, or
        {"error": {"code", "message"}} on failure.
    """
    if not task_data.get('short_description'):
        return error_response("VALIDATION", ERROR_SHORT_DESC_REQUIRED)

    create_data = _prepare_task_create_data(task_data)
    url = f"{NWS_API_BASE}/api/now/table/vtb_task"

    return await _write_private_task("POST", url, create_data, "creation")

async def update_private_task(task_number: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update / change an EXISTING private task (vtb_task), addressed by number.

    WHEN TO USE: the task already exists and the user wants to set, close,
        reassign, or otherwise change it. A VTB number together with a change
        verb (set / close / update / reassign) is always this tool.
    WHEN NOT TO USE: opening a brand-new task — use create_private_task.
    PREFER OVER: create_private_task whenever the record already exists.
    TABLES: vtb_task only.
    SIDE EFFECT: WRITE — patches one record; resolves sys_id by number first.
    EXAMPLE: set private task VTB0001234 to closed complete.

    Args:
        task_number: The private task number to update (e.g. "VTB0001234").
        update_data: Dictionary containing the fields to update.

    Returns:
        {"record": {...updated task...}, "message": ...} on success, or
        {"error": {"code", "message"}} on failure.
    """
    if not update_data:
        return error_response("VALIDATION", ERROR_NO_UPDATE_DATA)

    bad = [k for k in update_data if k not in VTB_UPDATABLE_FIELDS]
    if bad:
        return error_response(
            "VALIDATION", f"Rejected non-updatable field(s): {', '.join(bad)}"
        )

    try:
        sys_id = await _get_task_sys_id(task_number)
    except (ServiceNowRequestError, QueryValueError) as error:
        # Not "task not found": the lookup never answered. Reporting absence here
        # sends the user looking for a task that is probably sitting right there.
        # An unqueryable task number means the same thing — no lookup happened —
        # and both types expose the same `to_error_dict()`.
        return error.to_error_dict()
    if not sys_id:
        return error_response("NOT_FOUND", PRIVATE_TASK_NOT_FOUND_UPDATE)

    url = f"{NWS_API_BASE}/api/now/table/vtb_task/{sys_id}"
    return await _write_private_task("PATCH", url, update_data, "update")
