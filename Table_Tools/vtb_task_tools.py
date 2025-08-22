from service_now_api_oauth import make_nws_request, NWS_API_BASE
from typing import Any, Dict, Optional, List
from utils import extract_keywords
import httpx

# Define common fields for vtb_task table
COMMON_VTB_TASK_FIELDS = [
    "number",
    "short_description", 
    "priority",
    "sys_created_on",
    "state",
    "assigned_to",
    "assignment_group"
]

# Extended fields for detailed queries
DETAILED_VTB_TASK_FIELDS = COMMON_VTB_TASK_FIELDS + [
    "description",
    "comments",
    "work_notes", 
    "close_code",
    "close_notes",
    "sys_updated_on",
    "due_date",
    "parent"
]

async def similarvtbtasksfortext(inputText: str) -> dict[str, Any] | str:
    """Get vtb_task records based on input text."""
    keywords = extract_keywords(inputText)
    for keyword in keywords:
        url = f"{NWS_API_BASE}/api/now/table/vtb_task?sysparm_fields={','.join(COMMON_VTB_TASK_FIELDS)}&sysparm_query=short_descriptionCONTAINS{keyword}"
        data = await make_nws_request(url)
        if data and data.get('result') and len(data['result']) > 0:
            return data
    return "No vtb_task records found."

async def getshortdescforvtbtask(inputvtbtask: str) -> dict[str, Any] | str:
    """Get short_description for a given vtb_task based on input vtb_task number."""
    url = f"{NWS_API_BASE}/api/now/table/vtb_task?sysparm_fields=short_description&sysparm_query=number={inputvtbtask}"
    data = await make_nws_request(url)
    return data if data else "VTB Task not found."

async def similarvtbtasksforvtbtask(inputvtbtask: str) -> dict[str, Any] | str:
    """Get similar vtb_task records based on given vtb_task."""
    try:
        desc_data = await getshortdescforvtbtask(inputvtbtask)
        if isinstance(desc_data, dict) and desc_data.get('result'):
            if len(desc_data['result']) > 0:
                desc_text = desc_data['result'][0].get('short_description', '')
                if desc_text:
                    return await similarvtbtasksfortext(desc_text)
        return "No description found."
    except Exception as e:
        return f"Connection error: {str(e)}"

async def getvtbtaskdetails(inputvtbtask: str) -> dict[str, Any] | str:
    """Get detailed information for a given vtb_task based on input vtb_task number.
    
    Args:
        inputvtbtask: The vtb_task number.
    
    Returns:
        A dictionary containing vtb_task details or an error message if the request fails.
    """
    url = f"{NWS_API_BASE}/api/now/table/vtb_task?sysparm_fields={','.join(DETAILED_VTB_TASK_FIELDS)}&sysparm_query=number={inputvtbtask}"
    data = await make_nws_request(url)
    if data and data.get('result'):
        results = data['result']
        if isinstance(results, list) and results:
            return results[0]
        elif isinstance(results, dict):
            return results
    return "Unable to fetch vtb_task details or no vtb_task found."

async def createvtbtask(task_data: Dict[str, Any]) -> dict[str, Any] | str:
    """Create a new vtb_task record in ServiceNow.
    
    Args:
        task_data: Dictionary containing the vtb_task data to create.
                  Required fields: short_description
                  Optional fields: description, priority, assigned_to, assignment_group, due_date, parent, etc.
    
    Returns:
        A dictionary containing the created vtb_task details or an error message if the request fails.
    """
    if not task_data.get('short_description'):
        return "Error: short_description is required to create a vtb_task."
    
    # Validate required fields and set defaults
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
    
    # Make POST request to create the record
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Get authentication details from service_now_api_oauth
    from service_now_api_oauth import SERVICENOW_USERNAME, SERVICENOW_PASSWORD, _should_use_oauth
    from oauth_client import get_oauth_client
    
    url = f"{NWS_API_BASE}/api/now/table/vtb_task"
    
    async with httpx.AsyncClient() as client:
        try:
            if _should_use_oauth():
                # Use OAuth authentication
                oauth_client = get_oauth_client()
                auth_headers = await oauth_client.get_auth_headers()
                headers.update(auth_headers)
                response = await client.post(url, json=create_data, headers=headers, timeout=30.0)
            else:
                # Use basic authentication
                auth = (SERVICENOW_USERNAME, SERVICENOW_PASSWORD)
                response = await client.post(url, json=create_data, headers=headers, auth=auth, timeout=30.0)
            
            response.raise_for_status()
            result = response.json()
            
            if result and result.get('result'):
                return result['result']
            else:
                return result if result else "VTB Task created but no data returned."
                
        except httpx.HTTPStatusError as e:
            return f"HTTP error creating vtb_task: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"Error creating vtb_task: {str(e)}"

async def updatevtbtask(task_number: str, update_data: Dict[str, Any]) -> dict[str, Any] | str:
    """Update an existing vtb_task record in ServiceNow.
    
    Args:
        task_number: The vtb_task number to update.
        update_data: Dictionary containing the fields to update.
    
    Returns:
        A dictionary containing the updated vtb_task details or an error message if the request fails.
    """
    if not update_data:
        return "Error: No update data provided."
    
    # First, get the sys_id of the record
    sys_id_url = f"{NWS_API_BASE}/api/now/table/vtb_task?sysparm_fields=sys_id&sysparm_query=number={task_number}"
    sys_id_data = await make_nws_request(sys_id_url)
    
    if not sys_id_data or not sys_id_data.get('result') or not sys_id_data['result']:
        return "VTB Task not found for update."
    
    sys_id = sys_id_data['result'][0]['sys_id']
    
    # Make PUT request to update the record
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    from service_now_api_oauth import SERVICENOW_USERNAME, SERVICENOW_PASSWORD, _should_use_oauth
    from oauth_client import get_oauth_client
    
    url = f"{NWS_API_BASE}/api/now/table/vtb_task/{sys_id}"
    
    async with httpx.AsyncClient() as client:
        try:
            if _should_use_oauth():
                # Use OAuth authentication
                oauth_client = get_oauth_client()
                auth_headers = await oauth_client.get_auth_headers()
                headers.update(auth_headers)
                response = await client.put(url, json=update_data, headers=headers, timeout=30.0)
            else:
                # Use basic authentication
                auth = (SERVICENOW_USERNAME, SERVICENOW_PASSWORD)
                response = await client.put(url, json=update_data, headers=headers, auth=auth, timeout=30.0)
            
            response.raise_for_status()
            result = response.json()
            
            if result and result.get('result'):
                return result['result']
            else:
                return result if result else "VTB Task updated but no data returned."
                
        except httpx.HTTPStatusError as e:
            return f"HTTP error updating vtb_task: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"Error updating vtb_task: {str(e)}"

async def getvtbtasksbyfilter(filters: Dict[str, str], fields: Optional[List[str]] = None) -> dict[str, Any] | str:
    """Get vtb_task records with custom filters.
    
    Args:
        filters: Dictionary of field-value pairs for filtering.
        fields: Optional list of fields to return.
    
    Returns:
        A dictionary containing filtered vtb_task records or an error message.
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
    return data if data else "No vtb_task records found."