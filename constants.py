"""
Constants used throughout the ServiceNow MCP server.
"""

# HTTP Content Types
APPLICATION_JSON = "application/json"

# Common HTTP Headers
JSON_HEADERS = {
    "Accept": APPLICATION_JSON,
    "Content-Type": APPLICATION_JSON
}

# API Response Messages
NO_DESCRIPTION_FOUND = "No description found."
CONNECTION_ERROR = "Connection error: Request failed"
RECORD_NOT_FOUND = "Record not found."
NO_RECORDS_FOUND = "No records found."
UNABLE_TO_FETCH_RECORDS = "Unable to fetch alerts or no alerts found."
UNABLE_TO_FETCH_DETAILS = "Unable to fetch {record_type} details or no {record_type} found."
NO_SIMILAR_RECORDS_FOUND = "No similar records found (only exact match)"
REQUEST_FAILED_ERROR = "Request failed: {error}"
NO_FIELD_CONFIG_ERROR = "No field configuration found for table {table_name}"
NO_VALID_PRIORITIES_ERROR = "No valid priorities provided"
TABLE_NO_PRIORITY_SUPPORT_ERROR = "Table {table_name} does not support priority filtering"

# CMDB-specific error messages
NO_CIS_FOUND_FOR_TYPE = "No CIs found for type: {ci_type}"
NO_CIS_FOUND_MATCHING_CRITERIA = "No CIs found matching search criteria"
CI_NOT_FOUND = "CI {ci_number} not found in any CMDB table"
NO_SIMILAR_CIS_FOUND = "No similar CIs found for {ci_number}"
NO_CI_TYPES_FOUND = "No CI types found"
NO_CIS_FOUND_FOR_SEARCH = "No CIs found for search term: {search_term}"
ERROR_SEARCHING_CIS = "Error searching CIs: Request failed"
ERROR_SEARCHING_CIS_BY_TYPE = "Error searching CIS by type: Request failed"
ERROR_FINDING_SIMILAR_CIS = "Error finding similar CIs: Request failed"
ERROR_GETTING_CI_TYPES = "Error getting CI types: Request failed"
ERROR_QUICK_CI_SEARCH = "Error in quick CI search: Request failed"

# VTB Task-specific error messages
ERROR_SHORT_DESC_REQUIRED = "Error: short_description is required to create a private task."
ERROR_NO_UPDATE_DATA = "Error: No update data provided."
PRIVATE_TASK_NOT_FOUND_UPDATE = "Private Task not found for update."
UNABLE_TO_FETCH_PRIVATE_TASK_DETAILS = "Unable to fetch private task details or no private task found."
ERROR_PRIVATE_TASK_OPERATION = "Error during private task {operation}: {message}"
ERROR_PRIVATE_TASK_REQUEST_FAILED = "Error during private task {operation}: Request failed"
ERROR_PRIVATE_TASK_AUTH_FAILED = "Error during private task {operation}: Authentication failed"
ERROR_PRIVATE_TASK_ACCESS_DENIED = "Error during private task {operation}: Access denied"
ERROR_PRIVATE_TASK_INVALID_REQUEST = "Error during private task {operation}: Invalid request data"
ERROR_PRIVATE_TASK_NOT_FOUND = "Error during private task {operation}: Task not found"
ERROR_PRIVATE_TASK_SERVER_ERROR = "Error during private task {operation}: Server error"

# Table-specific error messages
TABLE_ERROR_MESSAGES = {
    "incident": "Incident not found.",
    "change_request": "Change not found.",
    "sc_req_item": "Request Item not found.",
    "kb_knowledge": "Knowledge article not found.",
    "vtb_task": "Private task not found.",
    "universal_request": "Universal Request not found.",
    "task_sla": "SLA record not found."
}

# Table Field Definitions
ESSENTIAL_FIELDS = {
    "incident": ["number", "short_description", "priority", "state", "sys_created_on"],
    "change_request": ["number", "short_description", "priority", "state", "sys_created_on"],
    "universal_request": ["number", "short_description", "priority", "state", "sys_created_on"],
    "kb_knowledge": ["number", "short_description", "kb_category", "state", "sys_created_on"],
    "vtb_task": ["number", "short_description", "priority", "state", "sys_created_on"],
    "task_sla": ["task", "sla", "stage", "business_percentage", "active", "sys_created_on"]
}

DETAIL_FIELDS = {
    "incident": ["number", "short_description", "priority", "state", "sys_created_on", "assigned_to", "assignment_group", "work_notes", "comments", "u_reference_1", "company", "cmdb_ci", "correlation_id", "major_incident_state"],
    "change_request": ["number", "short_description", "priority", "state", "sys_created_on", "assigned_to", "assignment_group", "work_notes", "comments", "u_reference_1", "company", "cmdb_ci"],
    "universal_request": ["number", "short_description", "priority", "state", "sys_created_on", "assigned_to", "assignment_group", "comments", "u_reference_1", "company", "cmdb_ci"],
    "kb_knowledge": ["number", "short_description", "kb_category", "state", "sys_created_on", "assigned_to"],
    "vtb_task": ["number", "short_description", "priority", "state", "sys_created_on", "assigned_to", "assignment_group", "work_notes", "comments"],
    "task_sla": ["task", "sla", "stage", "business_percentage", "active", "sys_created_on", "breach_time", "business_time_left", "duration", "has_breached", "business_duration", "business_elapsed_time", "planned_end_time"]
}

# VTB Task specific field definitions
COMMON_VTB_TASK_FIELDS = [
    "number",
    "short_description", 
    "priority",
    "sys_created_on",
    "state",
    "assigned_to",
    "assignment_group"
]

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

# ServiceNow Query Patterns and Validation
SERVICENOW_OR_SYNTAX_EXAMPLE = "1^ORpriority=2"
SERVICENOW_DATE_RANGE_EXAMPLE = ">=2024-01-01 00:00:00^<=2024-01-31 23:59:59"

# Common ServiceNow priority values
PRIORITY_VALUES = {
    "critical": "1",
    "high": "2",
    "moderate": "3",
    "low": "4",
    "planning": "5"
}

# Month name to number mapping for date parsing
MONTH_NAME_TO_NUMBER = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12
}

# Query validation messages
QUERY_WARNINGS = {
    "multiple_priorities_no_or": "Multiple priorities detected but no OR syntax used",
    "incomplete_date_range": "Date range appears incomplete - missing start or end date",
    "low_critical_incident_count": "Unusually low count for critical incidents - verify completeness",
    "zero_results_high_priority": "No results for high priority query - check filter syntax"
}
# ServiceNow table configurations
TABLE_CONFIGS = {
    "incident": {
        "display_name": "Incident",
        "api_name": "incident",
        "supports_work_notes": True,
        "supports_comments": True,
        "number_prefix": "INC",
        "priority_field": "priority",
        "state_field": "state"
    },
    "change_request": {
        "display_name": "Change Request", 
        "api_name": "change_request",
        "supports_work_notes": True,
        "supports_comments": True,
        "number_prefix": "CHG",
        "priority_field": "priority",
        "state_field": "state"
    },
    "sc_req_item": {
        "display_name": "Service Catalog Request Item",
        "api_name": "sc_req_item", 
        "supports_work_notes": False,
        "supports_comments": True,
        "number_prefix": "RITM",
        "priority_field": "priority",
        "state_field": "state"
    },
    "universal_request": {
        "display_name": "Universal Request",
        "api_name": "universal_request",
        "supports_work_notes": False,
        "supports_comments": True,
        "number_prefix": "UR",
        "priority_field": "priority",
        "state_field": "state"
    },
    "kb_knowledge": {
        "display_name": "Knowledge Base Article",
        "api_name": "kb_knowledge",
        "supports_work_notes": False,
        "supports_comments": False,
        "number_prefix": "KB",
        "priority_field": None,
        "state_field": "state"
    },
    "vtb_task": {
        "display_name": "Private Task",
        "api_name": "vtb_task",
        "supports_work_notes": True,
        "supports_comments": True,
        "number_prefix": "VTB",
        "priority_field": "priority",
        "state_field": "state"
    },
    "task_sla": {
        "display_name": "Task SLA",
        "api_name": "task_sla",
        "supports_work_notes": False,
        "supports_comments": False,
        "number_prefix": None,
        "priority_field": None,
        "state_field": "stage"
    }
}

# API endpoint patterns
API_ENDPOINTS = {
    "table_query": "/api/now/table/{table_name}",
    "table_record": "/api/now/table/{table_name}/{sys_id}",
    "test_endpoint": "/api/x_146833_awesomevi/test",
    "test_table_endpoint": "/api/x_146833_awesomevi/test/{table_name}"
}

# Common query parameters  
QUERY_PARAMS = {
    "display_value": "sysparm_display_value=true",
    "fields": "sysparm_fields={fields}",
    "query": "sysparm_query={query}",
    "limit": "sysparm_limit={limit}",
    "offset": "sysparm_offset={offset}"
}
# Field reference constants
TASK_NUMBER_FIELD = "task.number"
