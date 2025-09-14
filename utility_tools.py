from service_now_api_oauth import test_oauth_connection, get_auth_info

def nowtest():
    """Test function to verify mcp is running."""
    return "Server is running and ready to handle requests!"

async def now_test_oauth():
    """Test OAuth 2.0 connection to ServiceNow."""
    result = await test_oauth_connection()
    return result

def now_auth_info():
    """Get information about current authentication configuration."""
    return get_auth_info()
