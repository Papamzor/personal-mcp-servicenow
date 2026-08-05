"""Legacy auth/connectivity test tools.

Read-failure contract (v4.4 Tier 0.3). A failed GET raises
`ServiceNowRequestError` instead of returning None.

Both functions here are registered MCP tools, and both are diagnostics — which
makes reporting the *specific* classified failure the point rather than a
nicety. `nowtestauth` answered "Authentication test failed" for any failure
including a timeout, and `nowtest_auth_input` guessed "table may not exist or no
permissions" for a read that never completed: the same mislabelling this tier
removes elsewhere, in the two tools people reach for when they are already
trying to work out what is broken.
"""
from http_layer import ServiceNowRequestError, make_nws_request, NWS_API_BASE
from constants import TABLE_CONFIGS

async def nowtestauth():
    """Test function to verify authentication with ServiceNow standard API."""
    # Use standard sys_user table as a simple auth test
    url = f"{NWS_API_BASE}/api/now/table/sys_user?sysparm_limit=1&sysparm_fields=sys_id,name"
    try:
        data = await make_nws_request(url)
    except ServiceNowRequestError as error:
        # A diagnostic that says "auth failed" for a timeout sends the reader
        # after the wrong problem. The code distinguishes AUTH from TIMEOUT.
        return error.to_error_dict()
    if not data:
        return "Authentication test failed - unable to access ServiceNow API."
    return {
        "status": "success",
        "message": "Authentication successful - ServiceNow API accessible",
        "test_endpoint": "/api/now/table/sys_user",
        "records_found": len(data.get('result', []))
    }

async def nowtest_auth_input(table_name: str):
    """Get ServiceNow table schema information for a given table."""
    if table_name not in TABLE_CONFIGS:
        return f"Invalid table '{table_name}'. Not in the supported allowlist."
    # Use standard table API to get basic table info
    url = f"{NWS_API_BASE}/api/now/table/{table_name}?sysparm_limit=1"
    try:
        data = await make_nws_request(url)
    except ServiceNowRequestError as error:
        # Not "the table may not exist": the read did not complete.
        return error.to_error_dict()
    if not data:
        return f"Unable to access table '{table_name}' - table may not exist or no permissions."

    result = data.get('result', [])
    if not result:
        return f"Table '{table_name}' is accessible but contains no records."
    
    # Return table info and sample field names
    sample_record = result[0]
    field_names = list(sample_record.keys())
    
    return {
        "table_name": table_name,
        "status": "accessible",
        "sample_fields": field_names[:10],  # First 10 fields
        "total_fields": len(field_names),
        "has_records": len(result) > 0
    }
