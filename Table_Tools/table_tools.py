from service_now_api_oauth import make_nws_request, NWS_API_BASE

async def nowtestauth():
    """Test function to verify authentication with ServiceNow standard API."""
    # Use standard sys_user table as a simple auth test
    url = f"{NWS_API_BASE}/api/now/table/sys_user?sysparm_limit=1&sysparm_fields=sys_id,name"
    data = await make_nws_request(url)
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
    # Use standard table API to get basic table info
    url = f"{NWS_API_BASE}/api/now/table/{table_name}?sysparm_limit=1"
    data = await make_nws_request(url)
    if not data:
        return f"Unable to access table '{table_name}' - table may not exist or no permissions."
    
    result = data.get('result', [])
    if not result:
        return f"Table '{table_name}' is accessible but contains no records."
    
    # Return table info and sample field names
    sample_record = result[0] if result else {}
    field_names = list(sample_record.keys()) if sample_record else []
    
    return {
        "table_name": table_name,
        "status": "accessible",
        "sample_fields": field_names[:10],  # First 10 fields
        "total_fields": len(field_names),
        "has_records": len(result) > 0
    }
