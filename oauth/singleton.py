"""Module-level OAuth client singleton + convenience request helpers.

Canonical home (v4.1) of the process-wide ``ServiceNowOAuthClient``
instance and the ``get_oauth_client`` / ``make_oauth_request`` helpers.
Before v4.1 these lived in the ``oauth_client.py`` shim; that shim is
now deleted and this is the single source of truth.

``httpx`` is re-exported so tests can patch
``oauth.singleton.httpx.AsyncClient`` (patching the attribute on the
shared httpx module also affects the pooled-client construction in
``oauth/http_pool.py`` that the executor and token-store now share).
"""
from __future__ import annotations

import os
from typing import Any, Optional

import httpx  # re-exported for tests that patch ``oauth.singleton.httpx.AsyncClient``

from oauth.client import ServiceNowOAuthClient

__all__ = ["get_oauth_client", "make_oauth_request", "httpx"]

# Process-wide singleton. Tests reset it via ``oauth.singleton._oauth_client = None``.
_oauth_client: Optional[ServiceNowOAuthClient] = None

# config.json key -> env var the OAuth client reads. Env always wins.
_CONFIG_ENV_MAP = {
    "instance": "SERVICENOW_INSTANCE",
    "client_id": "SERVICENOW_CLIENT_ID",
    "client_secret": "SERVICENOW_CLIENT_SECRET",
}


def _hydrate_env_from_config() -> None:
    """Populate SERVICENOW_* env vars from the setup-wizard config file.

    The OAuth client reads only ``os.getenv``; without this, users who ran
    ``--setup`` (which writes ~/.config/mcp-servicenow/config.json) hit
    "Missing OAuth configuration" unless an external process exported the
    env vars. Env vars already set take precedence and are never overwritten.
    """
    try:
        from config_loader import load_config_from_file
        file_config = load_config_from_file()
    except Exception:
        return
    for config_key, env_var in _CONFIG_ENV_MAP.items():
        if not os.environ.get(env_var) and file_config.get(config_key):
            os.environ[env_var] = file_config[config_key]


def get_oauth_client() -> ServiceNowOAuthClient:
    """Get or create the global OAuth client instance."""
    global _oauth_client
    if _oauth_client is None:
        _hydrate_env_from_config()
        _oauth_client = ServiceNowOAuthClient()
    return _oauth_client


async def make_oauth_request(url: str) -> Optional[dict[str, Any]]:
    """Convenience function for making OAuth-authenticated GET requests."""
    client = get_oauth_client()
    return await client.make_authenticated_request("GET", url)
