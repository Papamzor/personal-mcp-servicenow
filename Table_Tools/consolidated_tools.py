"""
Consolidated tools interface using generic table functions.
All table-specific operations are now unified through generic functions with cognitive complexity < 15.
"""

from .generic_table_tools import (
    query_table_by_text, 
    get_record_description, 
    get_record_details, 
    find_similar_records,
    query_table_with_filters,
    get_records_by_priority,
    query_table_with_generic_filters,
    TableFilterParams
)
from typing import Any, Dict, Optional, List
from constants import TABLE_ERROR_MESSAGES, TASK_NUMBER_FIELD


# Helper function to get table-specific error message
def _get_error_message(table_name: str, default: str = "Record not found.") -> str:
    """Get table-specific error message with cognitive complexity < 15."""
    return TABLE_ERROR_MESSAGES.get(table_name, default)


# INCIDENT TOOLS - Using generic functions
async def similar_incidents_for_text(input_text: str) -> Dict[str, Any]:
    """Find incidents based on input text."""
    return await query_table_by_text("incident", input_text)

async def get_short_desc_for_incident(input_incident: str) -> Dict[str, Any]:
    """Get short_description for incident."""
    return await get_record_description("incident", input_incident)

async def similar_incidents_for_incident(input_incident: str) -> Dict[str, Any]:
    """Find similar incidents based on given incident."""
    return await find_similar_records("incident", input_incident)

async def get_incident_details(input_incident: str) -> Dict[str, Any]:
    """Get detailed incident information."""
    return await get_record_details("incident", input_incident)

async def get_incidents_by_filter(filters: Dict[str, str], fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get incidents with custom filters."""
    params = TableFilterParams(filters=filters, fields=fields)
    return await query_table_with_filters("incident", params)

async def get_priority_incidents(priorities: List[str], **additional_filters) -> Dict[str, Any]:
    """Get incidents by priority using proper ServiceNow OR syntax."""
    return await get_records_by_priority("incident", priorities, additional_filters, detailed=True)


# CHANGE TOOLS - Using generic functions  
async def similar_changes_for_text(input_text: str) -> Dict[str, Any]:
    """Find changes based on input text."""
    return await query_table_by_text("change_request", input_text)

async def get_short_desc_for_change(input_change: str) -> Dict[str, Any]:
    """Get short_description for change."""
    return await get_record_description("change_request", input_change)

async def similar_changes_for_change(input_change: str) -> Dict[str, Any]:
    """Find similar changes based on given change."""
    return await find_similar_records("change_request", input_change)

async def get_change_details(input_change: str) -> Dict[str, Any]:
    """Get detailed change information."""
    return await get_record_details("change_request", input_change)


# REQUEST ITEM TOOLS - Using generic functions
async def similar_request_items_for_text(input_text: str) -> Dict[str, Any]:
    """Find service catalog request items based on input text."""
    return await query_table_by_text("sc_req_item", input_text)

async def get_short_desc_for_request_item(input_request_item: str) -> Dict[str, Any]:
    """Get short_description for request item."""
    return await get_record_description("sc_req_item", input_request_item)

async def similar_request_items_for_request_item(input_request_item: str) -> Dict[str, Any]:
    """Find similar request items based on given request item."""
    return await find_similar_records("sc_req_item", input_request_item)

async def get_request_item_details(input_request_item: str) -> Dict[str, Any]:
    """Get detailed request item information."""
    return await get_record_details("sc_req_item", input_request_item)


# UNIVERSAL REQUEST TOOLS - Using generic functions
async def similar_universal_requests_for_text(input_text: str) -> Dict[str, Any]:
    """Find universal requests based on input text."""
    return await query_table_by_text("universal_request", input_text)

async def get_short_desc_for_universal_request(input_universal_request: str) -> Dict[str, Any]:
    """Get short_description for universal request."""
    return await get_record_description("universal_request", input_universal_request)

async def similar_universal_requests_for_universal_request(input_universal_request: str) -> Dict[str, Any]:
    """Find similar universal requests based on given universal request."""
    return await find_similar_records("universal_request", input_universal_request)

async def get_universal_request_details(input_universal_request: str) -> Dict[str, Any]:
    """Get detailed universal request information."""
    return await get_record_details("universal_request", input_universal_request)


async def similar_knowledge_for_text(input_text: str, kb_base: Optional[str] = None, category: Optional[str] = None) -> Dict[str, Any]:
    """Find knowledge articles based on input text."""
    if category or kb_base:
        # Build filters for category or kb_base
        filters = {}
        if category:
            filters["kb_category"] = category
        if kb_base:
            filters["kb_knowledge_base"] = kb_base
        return await query_table_with_generic_filters("kb_knowledge", filters)
    
    return await query_table_by_text("kb_knowledge", input_text)

async def get_knowledge_details(input_kb: str) -> Dict[str, Any]:
    """Get detailed knowledge article information."""
    return await get_record_details("kb_knowledge", input_kb)

async def get_knowledge_by_category(category: str, kb_base: Optional[str] = None) -> Dict[str, Any]:
    """Get knowledge articles by category."""
    filters = {"kb_category": category}
    if kb_base:
        filters["kb_knowledge_base"] = kb_base
    return await query_table_with_generic_filters("kb_knowledge", filters)

async def get_active_knowledge_articles(input_text: str) -> Dict[str, Any]:
    """Get active knowledge articles matching text."""
    filters = {"state": "published"}
    result = await query_table_with_generic_filters("kb_knowledge", filters)
    
    # If we got results and have input text, filter by text similarity
    if isinstance(result, dict) and result.get("result") and input_text.strip():
        # This is a simplified approach - in a full implementation, you might want to 
        # do text matching on the results
        pass
    
    return result


# PRIVATE TASK TOOLS - Using generic functions (keeping VTB separate as it has CRUD operations)
async def similar_private_tasks_for_text(input_text: str) -> Dict[str, Any]:
    """Find private tasks based on input text."""
    return await query_table_by_text("vtb_task", input_text)

async def get_short_desc_for_private_task(input_private_task: str) -> Dict[str, Any]:
    """Get short_description for private task."""
    return await get_record_description("vtb_task", input_private_task)

async def similar_private_tasks_for_private_task(input_private_task: str) -> Dict[str, Any]:
    """Find similar private tasks based on given task."""
    return await find_similar_records("vtb_task", input_private_task)

async def get_private_task_details(input_private_task: str) -> Dict[str, Any]:
    """Get detailed private task information."""
    return await get_record_details("vtb_task", input_private_task)

async def get_private_tasks_by_filter(filters: Dict[str, str]) -> Dict[str, Any]:
    """Get private tasks with custom filters."""
    return await query_table_with_generic_filters("vtb_task", filters)


# SLA TOOLS - Using generic functions
async def similar_slas_for_text(input_text: str) -> Dict[str, Any]:
    """Find SLAs based on input text (searches related task descriptions)."""
    return await query_table_by_text("task_sla", input_text)

async def get_slas_for_task(task_number: str) -> Dict[str, Any]:
    """Get all SLA records for a specific task."""
    # Create filter to find SLAs by task reference
    filters = {TASK_NUMBER_FIELD: task_number}
    params = TableFilterParams(filters=filters)
    return await query_table_with_filters("task_sla", params)

async def get_sla_details(sla_sys_id: str) -> Dict[str, Any]:
    """Get detailed SLA information by sys_id."""
    return await get_record_details("task_sla", sla_sys_id)

async def get_breaching_slas(time_threshold_minutes: Optional[int] = 60) -> Dict[str, Any]:
    """Get SLAs at risk of breaching within specified time threshold."""
    filters = {
        "active": "true",
        "business_time_left": f"<{time_threshold_minutes * 60}",  # Convert to seconds
        "has_breached": "false"
    }
    params = TableFilterParams(filters=filters, fields=None)
    return await query_table_with_filters("task_sla", params)

async def get_breached_slas(filters: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Get SLAs that have already breached. Defaults to recent breaches (last 7 days) to avoid token overload."""
    base_filters = {
        "has_breached": "true",
        "sys_created_on": ">=javascript:gs.dateGenerate(gs.daysAgo(7))"  # Default to last 7 days
    }
    if filters:
        base_filters.update(filters)
    params = TableFilterParams(filters=base_filters)
    return await query_table_with_filters("task_sla", params)

async def get_slas_by_stage(stage: str, additional_filters: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Get SLAs by stage (In progress, Completed, etc.)."""
    filters = {"stage": stage}
    if additional_filters:
        filters.update(additional_filters)
    params = TableFilterParams(filters=filters)
    return await query_table_with_filters("task_sla", params)

async def get_active_slas(filters: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Get currently active SLA records."""
    base_filters = {"active": "true"}
    if filters:
        base_filters.update(filters)
    params = TableFilterParams(filters=base_filters)
    return await query_table_with_filters("task_sla", params)

async def get_sla_performance_summary(filters: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Get SLA performance metrics with detailed information. Defaults to recent data (last 30 days) for efficiency."""
    # Default to recent data to avoid token overload
    default_filters = {
        "sys_created_on": ">=javascript:gs.dateGenerate(gs.daysAgo(30))"
    }
    if filters:
        default_filters.update(filters)

    # Include key performance fields for analysis
    fields = [
        TASK_NUMBER_FIELD, "task.short_description", "sla.name", "stage",
        "business_percentage", "active", "has_breached", "breach_time",
        "business_time_left", "duration", "sys_created_on"
    ]
    params = TableFilterParams(filters=default_filters, fields=fields)
    return await query_table_with_filters("task_sla", params)

async def get_recent_breached_slas(days: int = 1) -> Dict[str, Any]:
    """Get recently breached SLAs for immediate attention. Default to last 24 hours."""
    filters = {
        "has_breached": "true",
        "sys_created_on": f">=javascript:gs.dateGenerate(gs.daysAgo({days}))"
    }
    params = TableFilterParams(filters=filters)
    return await query_table_with_filters("task_sla", params)

async def get_critical_sla_status() -> Dict[str, Any]:
    """Get high-priority SLA status summary for dashboard/monitoring."""
    filters = {
        "active": "true",
        "task.priority": "1^ORtask.priority=2",  # P1 and P2 tasks only
        "business_percentage": ">80"  # Close to or over SLA target
    }
    fields = [
        TASK_NUMBER_FIELD, "task.priority", "sla.name", "stage",
        "business_percentage", "business_time_left", "has_breached"
    ]
    params = TableFilterParams(filters=filters, fields=fields)
    return await query_table_with_filters("task_sla", params)
