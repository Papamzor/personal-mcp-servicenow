from service_now_api_oauth import test_oauth_connection, get_auth_info

def nowtest():
    """Test function to verify mcp is running."""
    return "Server is running and ready to handle requests!"

async def nowtestoauth():
    """Test OAuth 2.0 connection to ServiceNow."""
    result = await test_oauth_connection()
    return result

async def nowauthinfo():
    """Get information about current authentication configuration."""
    return await get_auth_info()
