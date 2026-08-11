"""Regression tests for the P2 security-sanitization hardening.

Covers the auth middleware (C-2), audit PII summarization (H-4), and the
error-detail suppression in the write-path error mapper (H-5).
"""
import os

import httpx
import pytest

from audit_middleware import _sanitize
from auth_middleware import AuthMiddleware
from constants import MCP_AUTH_REJECTED
from Table_Tools.write_helpers import map_http_error


# --- C-2: AuthMiddleware ---------------------------------------------------

class _Ctx:
    """Minimal stand-in for a MiddlewareContext (unused fields)."""


async def _call_next(_ctx):
    return "OK"


@pytest.mark.asyncio
async def test_auth_noop_when_token_unset(monkeypatch):
    monkeypatch.delenv("MCP_SSE_AUTH_TOKEN", raising=False)
    result = await AuthMiddleware().on_call_tool(_Ctx(), _call_next)
    assert result == "OK"


@pytest.mark.asyncio
async def test_auth_accepts_matching_bearer(monkeypatch):
    monkeypatch.setenv("MCP_SSE_AUTH_TOKEN", "s3cret-token-value")
    monkeypatch.setattr(
        "fastmcp.server.dependencies.get_http_headers",
        lambda: {"authorization": "Bearer s3cret-token-value"},
    )
    result = await AuthMiddleware().on_call_tool(_Ctx(), _call_next)
    assert result == "OK"


@pytest.mark.asyncio
async def test_auth_rejects_wrong_token(monkeypatch):
    monkeypatch.setenv("MCP_SSE_AUTH_TOKEN", "s3cret-token-value")
    monkeypatch.setattr(
        "fastmcp.server.dependencies.get_http_headers",
        lambda: {"authorization": "Bearer wrong"},
    )
    middleware = AuthMiddleware()
    ctx = _Ctx()
    with pytest.raises(PermissionError, match=MCP_AUTH_REJECTED):
        await middleware.on_call_tool(ctx, _call_next)


@pytest.mark.asyncio
async def test_auth_rejects_missing_header(monkeypatch):
    monkeypatch.setenv("MCP_SSE_AUTH_TOKEN", "s3cret-token-value")
    monkeypatch.setattr(
        "fastmcp.server.dependencies.get_http_headers", lambda: {}
    )
    middleware = AuthMiddleware()
    ctx = _Ctx()
    with pytest.raises(PermissionError):
        await middleware.on_call_tool(ctx, _call_next)


# --- H-4: audit PII summarization ------------------------------------------

def test_sanitize_redacts_sensitive_keys():
    assert _sanitize({"client_secret": "abc"})["client_secret"] == "[REDACTED]"


def test_sanitize_summarizes_risky_values():
    out = _sanitize({"query": "John Smith salary details"})
    assert out["query"] == "<str len=25>"
    assert "John" not in out["query"]


def test_sanitize_passes_through_benign_keys():
    assert _sanitize({"table": "incident"})["table"] == "incident"


# --- H-5: write-path error detail suppression ------------------------------

def _status_error(status: int, body: str) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://x.test/api")
    response = httpx.Response(status, text=body, request=request)
    return httpx.HTTPStatusError("err", request=request, response=response)


def test_map_http_error_does_not_leak_body_on_default():
    err = _status_error(500, "Traceback: internal ACL failure at sys_id=abc")
    msg = map_http_error(err, {}, "Server error.", detail_on_default=True)["error"]["message"]
    assert msg == "Server error."
    assert "sys_id" not in msg
    assert "Traceback" not in msg


def test_map_http_error_does_not_leak_body_on_detail_code():
    err = _status_error(400, "invalid field xyz")
    msg = map_http_error(err, {400: "Bad request."}, "Server error.", detail_codes={400})["error"]["message"]
    assert msg == "Bad request."
    assert "xyz" not in msg


# --- M-5: config-file -> env hydration -------------------------------------

def test_hydrate_env_from_config_fills_missing(monkeypatch):
    import oauth.singleton as singleton

    for env_var in ("SERVICENOW_INSTANCE", "SERVICENOW_CLIENT_ID", "SERVICENOW_CLIENT_SECRET"):
        monkeypatch.delenv(env_var, raising=False)
    monkeypatch.setattr(
        "config_loader.load_config_from_file",
        lambda: {"instance": "https://cfg.test", "client_id": "cfgid", "client_secret": "cfgsecret"},
    )
    singleton._hydrate_env_from_config()
    assert os.environ["SERVICENOW_INSTANCE"] == "https://cfg.test"
    assert os.environ["SERVICENOW_CLIENT_ID"] == "cfgid"


def test_hydrate_env_does_not_override_existing(monkeypatch):
    import oauth.singleton as singleton

    monkeypatch.setenv("SERVICENOW_INSTANCE", "https://env.test")
    monkeypatch.setattr(
        "config_loader.load_config_from_file",
        lambda: {"instance": "https://cfg.test"},
    )
    singleton._hydrate_env_from_config()
    assert os.environ["SERVICENOW_INSTANCE"] == "https://env.test"
