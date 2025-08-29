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