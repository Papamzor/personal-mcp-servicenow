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