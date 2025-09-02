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

# Table Field Definitions
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

# Query validation messages
QUERY_WARNINGS = {
    "multiple_priorities_no_or": "Multiple priorities detected but no OR syntax used",
    "incomplete_date_range": "Date range appears incomplete - missing start or end date",
    "low_critical_incident_count": "Unusually low count for critical incidents - verify completeness",
    "zero_results_high_priority": "No results for high priority query - check filter syntax"
}