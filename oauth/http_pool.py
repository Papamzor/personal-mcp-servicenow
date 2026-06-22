"""Process-wide pooled ``httpx.AsyncClient`` for all ServiceNow traffic.

Before v4.2 every API call and every OAuth token request opened its own
``async with httpx.AsyncClient(...)`` — a fresh TCP + TLS handshake per
request with zero connection reuse. This module keeps a single keep-alive
client alive for the process lifetime so reads, writes, and token refreshes
all share pooled connections; only the first request to ServiceNow pays the
handshake cost.

``httpx`` is imported here (not aliased) on purpose: tests patch
``oauth.singleton.httpx.AsyncClient``, which mutates the attribute on the
shared ``httpx`` module object, so the patch also intercepts the
construction below. Cross-test isolation is handled by an autouse fixture
in ``tests/conftest.py`` that resets ``_pooled_client``.

Timeouts are controlled via ``anyio.fail_after()`` at each call site;
the client-level timeout is set to ``None`` so anyio cancel scopes
govern all deadlines.
"""
from __future__ import annotations

import atexit
import asyncio
from typing import Optional

import httpx

# ServiceNow is a single host; a modest keep-alive pool covers our concurrent
# gather() fan-outs (CMDB probe, KB batch) without exhausting the instance.
#
# ``keepalive_expiry`` caps how long an idle pooled connection may be reused.
# ServiceNow (and the load-balancer/proxy in front of it) silently drops idle
# sockets; reusing a half-open one stalls the next request — classically the
# first WRITE fired after a burst of READs. With the client running at
# ``timeout=None`` (deadlines come from anyio cancel scopes) there is no
# transport-level timeout to catch such a socket, so expiring idle connections
# after 15s forces a fresh socket instead of inheriting a dead one.
_LIMITS = httpx.Limits(
    max_connections=100,
    max_keepalive_connections=20,
    keepalive_expiry=15.0,
)

_pooled_client: Optional[httpx.AsyncClient] = None


def get_pooled_client() -> httpx.AsyncClient:
    """Return the shared keep-alive client, creating it on first use."""
    global _pooled_client
    if _pooled_client is None or getattr(_pooled_client, "is_closed", False):
        _pooled_client = httpx.AsyncClient(verify=True, limits=_LIMITS, timeout=httpx.Timeout(None))
    return _pooled_client


async def shutdown_http_client() -> None:
    """Close the pooled client and drop the reference. Idempotent."""
    global _pooled_client
    client = _pooled_client
    _pooled_client = None
    if client is not None and not getattr(client, "is_closed", True):
        await client.aclose()


def _close_pool_atexit() -> None:
    """Best-effort close on interpreter exit to avoid unclosed-client warnings."""
    client = _pooled_client
    if client is None or getattr(client, "is_closed", True):
        return
    try:
        asyncio.run(client.aclose())
    except RuntimeError:
        # Loop already running or closed at exit — sockets are reclaimed by
        # the OS anyway; this is purely to silence httpx's ResourceWarning.
        pass


atexit.register(_close_pool_atexit)
