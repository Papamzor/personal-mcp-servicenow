from service_now_api import make_nws_request, NWS_API_BASE

async def nowtestauth():
    """Test function to verify nowauth is running with authentication."""
    url = f"{NWS_API_BASE}/api/x_146833_awesomevi/test"
    data = await make_nws_request(url)
    if not data:
        return "Unable to fetch alerts or no alerts found."
    return data

async def nowtestauthInput(tableName: str):
    """Get ServiceNow table description for a given table."""
    url = f"{NWS_API_BASE}/api/x_146833_awesomevi/test/{tableName}"
    data = await make_nws_request(url)
    if not data:
        return "Unable to fetch alerts or no alerts found."
    return data
