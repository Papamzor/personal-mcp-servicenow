"""Shared-secret bearer auth middleware for MCP tool calls.

Guards ``on_call_tool`` with a constant-time comparison against
``MCP_SSE_AUTH_TOKEN``. When that env var is unset, this middleware is a
no-op — the stdio/local transport is trusted by default, and the SSE
startup guard in ``personal_mcp_servicenow_main.py`` refuses to launch the
network transport in that state unless insecure mode was explicitly
requested. Register this middleware before ``AuditMiddleware`` so
unauthenticated calls never reach the audit log's tool-execution path.
"""

import hmac
import os

from fastmcp.server.middleware import Middleware, MiddlewareContext

from constants import MCP_AUTH_REJECTED


class AuthMiddleware(Middleware):
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        expected = os.getenv("MCP_SSE_AUTH_TOKEN")
        if not expected:
            return await call_next(context)

        try:
            from fastmcp.server.dependencies import get_http_headers
            headers = get_http_headers() or {}
            auth = headers.get("authorization", "")
            token = auth[7:] if auth.startswith("Bearer ") else ""
            authorized = bool(token) and hmac.compare_digest(token, expected)
        except Exception:
            authorized = False

        if not authorized:
            raise PermissionError(MCP_AUTH_REJECTED)

        return await call_next(context)
