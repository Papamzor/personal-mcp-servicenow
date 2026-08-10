from http_layer import test_oauth_connection, get_auth_info

def nowtest():
    """Confirm this MCP server process is alive (contacts nothing).

    WHEN TO USE: sanity-check that this MCP server is running and responding.
    WHEN NOT TO USE: checking ServiceNow reachability (now_test_oauth) or
        reading auth config (now_auth_info).
    PREFER OVER: now_test_oauth when you only care that the server itself
        answers, not that ServiceNow does.
    SIDE EFFECT: none; returns a static string.
    EXAMPLE: is the MCP server responding.
    """
    return "Server is running and ready to handle requests!"

async def now_test_oauth():
    """Check the live ServiceNow connection and OAuth credentials.

    WHEN TO USE: verify ServiceNow is reachable and credentials work — a
        connectivity or health probe of the instance.
    WHEN NOT TO USE: building or explaining a filter
        (build_smart_servicenow_filter / explain_servicenow_filters); reading
        local auth config without a call (now_auth_info).
    PREFER OVER: nowtest when you need to know ServiceNow itself answers, not
        just this process.
    SIDE EFFECT: read-only — makes one lightweight authenticated call.
    EXAMPLE: check the ServiceNow connection is healthy.
    """
    result = await test_oauth_connection()
    return result

def now_auth_info():
    """Report the current authentication configuration (no ServiceNow call).

    WHEN TO USE: inspect which instance and auth mode are configured locally.
    WHEN NOT TO USE: testing whether it actually works — use now_test_oauth.
    PREFER OVER: now_test_oauth when you only need the configured values, not a
        live probe.
    SIDE EFFECT: none; reads local config only.
    EXAMPLE: show my ServiceNow auth configuration.
    """
    return get_auth_info()
