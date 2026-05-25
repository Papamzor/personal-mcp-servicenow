"""Audit logging middleware for MCP tool calls.

Emits one structured JSON log line to stderr per tool invocation, capturing
the caller identity (from JWT in Authorization header), tool name, arguments,
duration, and outcome. structlog is configured in the entry point so this
module does not reconfigure it on import.
"""

import base64
import json
import time

import structlog
from fastmcp.server.middleware import Middleware, MiddlewareContext

_log = structlog.get_logger("audit")

_SENSITIVE = {"password", "secret", "token", "key", "auth", "credential"}


def _sanitize(args: dict | None) -> dict:
    if not args:
        return {}
    return {
        k: "[REDACTED]" if any(s in k.lower() for s in _SENSITIVE) else v
        for k, v in args.items()
    }


def _user_from_headers() -> str:
    try:
        from fastmcp.server.dependencies import get_http_headers
        headers = get_http_headers() or {}
        auth = headers.get("authorization", "")
        if not auth.startswith("Bearer "):
            return "unauthenticated"

        token = auth[7:]
        parts = token.split(".")
        if len(parts) != 3:
            return "unknown"

        # Azure APIM validates the JWT at ingress; here we only decode the
        # payload to attribute the call to a user. No signature verification.
        padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))

        return (
            payload.get("preferred_username")
            or payload.get("upn")
            or payload.get("email")
            or payload.get("sub")
            or "unknown"
        )
    except Exception:
        return "unauthenticated"


class AuditMiddleware(Middleware):
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        tool_name = context.message.name
        args = _sanitize(context.message.arguments)
        user = _user_from_headers()
        request_id = getattr(context, "request_id", None) or getattr(
            getattr(context, "fastmcp_context", None), "request_id", None
        )
        start = time.monotonic()

        try:
            result = await call_next(context)
            _log.info(
                "tool_call",
                tool=tool_name,
                user=user,
                request_id=str(request_id) if request_id else None,
                args=args,
                duration_ms=round((time.monotonic() - start) * 1000, 2),
                status="success",
            )
            return result
        except Exception as e:
            _log.error(
                "tool_call",
                tool=tool_name,
                user=user,
                request_id=str(request_id) if request_id else None,
                args=args,
                duration_ms=round((time.monotonic() - start) * 1000, 2),
                status="error",
                error=str(e),
            )
            raise
