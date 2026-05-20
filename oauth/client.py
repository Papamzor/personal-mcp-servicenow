"""ServiceNowOAuthClient — orchestrator façade.

Composes ``TokenStore`` + ``RequestExecutor`` and owns the
``get_auth_headers`` step that builds the Bearer header from a valid
token. Preserves every public method, attribute, and private method
that v3 exposed so existing call sites and test patches continue to work:

    - public methods   : get_auth_headers, make_authenticated_request,
                         test_connection
    - private methods  : _get_basic_auth_header, _request_access_token,
                         _get_valid_token, _clear_token_cache,
                         _retry_with_fresh_token, _process_response
    - public attrs     : instance_url, client_id, client_secret,
                         token_endpoint
    - cache attrs      : _access_token, _token_expires_at, _token_lock
                         (proxied via property to the underlying TokenStore
                         so direct read/write from tests keeps working)
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx
from dotenv import load_dotenv

from constants import JSON_HEADERS
from oauth.request_executor import RequestExecutor
from oauth.token_store import TokenStore

load_dotenv()


class ServiceNowOAuthClient:
    """OAuth 2.0 Client Credentials implementation for ServiceNow.

    Composes three internal subsystems. The class itself owns no auth
    state — it delegates to TokenStore. The façade exists for
    backwards-compat and to give callers a single entry point.
    """

    def __init__(self) -> None:
        self.instance_url = os.getenv("SERVICENOW_INSTANCE")
        self.client_id = os.getenv("SERVICENOW_CLIENT_ID")
        self.client_secret = os.getenv("SERVICENOW_CLIENT_SECRET")

        if not all([self.instance_url, self.client_id, self.client_secret]):
            raise ValueError(
                "Missing OAuth configuration. Ensure SERVICENOW_INSTANCE, "
                "SERVICENOW_CLIENT_ID, and SERVICENOW_CLIENT_SECRET are set."
            )

        self.token_endpoint = f"{self.instance_url}/oauth_token.do"

        # Pass façade methods (via late-binding lambdas) into the
        # subsystems so test patches on the client surface affect every
        # internal call. Each lambda reads ``self`` attributes at call
        # time, never at construction, so ``patch.object(client, ...)``
        # takes effect even after the subsystems were built.
        self._token_store = TokenStore(
            instance_url=self.instance_url,
            client_id=self.client_id,
            client_secret=self.client_secret,
            fetch_token_fn=lambda: self._request_access_token(),
        )
        self._executor = RequestExecutor(
            get_auth_headers=lambda: self.get_auth_headers(),
            token_store=self._token_store,
        )

    # ---- v3 cache attributes proxied to TokenStore ----------------------

    @property
    def _access_token(self) -> Optional[str]:
        return self._token_store._access_token

    @_access_token.setter
    def _access_token(self, value: Optional[str]) -> None:
        self._token_store._access_token = value

    @property
    def _token_expires_at(self):
        return self._token_store._token_expires_at

    @_token_expires_at.setter
    def _token_expires_at(self, value) -> None:
        self._token_store._token_expires_at = value

    @property
    def _token_lock(self):
        return self._token_store._token_lock

    # ---- v3 private methods preserved (test patches target these) -------

    def _get_basic_auth_header(self) -> str:
        return self._token_store._get_basic_auth_header()

    async def _request_access_token(self) -> Dict[str, Any]:
        # Route through the TokenStore's "real" HTTP call. The hook on
        # the TokenStore points back at this method (see __init__), so
        # tests that patch ``client._request_access_token`` short-circuit
        # the cache-refresh loop without touching the token store.
        return await self._token_store._do_request_access_token()

    async def _get_valid_token(self) -> str:
        return await self._token_store.get_valid_token()

    async def _clear_token_cache(self) -> None:
        await self._token_store.clear()

    def _process_response(self, response: httpx.Response) -> Dict[str, Any]:
        return self._executor._process_response(response)

    async def _retry_with_fresh_token(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        raise_for_status: bool = False,
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        return await self._executor._retry_with_fresh_token(
            client, method, url, raise_for_status=raise_for_status, **kwargs
        )

    # ---- v3 public API --------------------------------------------------

    async def get_auth_headers(self) -> Dict[str, str]:
        """Return Authorization + JSON headers for an API request.

        Inlined (rather than delegated to AuthHeaderProvider) so tests
        that ``patch.object(client, "_get_valid_token")`` see their
        patch applied to every authenticated request — including those
        the RequestExecutor initiates internally.
        """
        token = await self._get_valid_token()
        return {
            "Authorization": f"Bearer {token}",
            **JSON_HEADERS,
        }

    async def make_authenticated_request(
        self,
        method: str,
        url: str,
        raise_for_status: bool = False,
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        """Make an authenticated request to ServiceNow API.

        Delegates to RequestExecutor; the 401-retry + raise_for_status
        semantics are preserved.
        """
        return await self._executor.make_authenticated_request(
            method, url, raise_for_status=raise_for_status, **kwargs
        )

    async def test_connection(self) -> Dict[str, Any]:
        """Test the OAuth connection by making a simple API call."""
        test_url = f"{self.instance_url}/api/now/table/sys_user?sysparm_limit=1"
        result = await self.make_authenticated_request("GET", test_url)

        if result:
            expires = self._token_store.expires_at
            return {
                "status": "success",
                "message": "OAuth authentication successful",
                "token_valid": True,
                "expires_at": expires.isoformat() if expires else None,
            }
        return {
            "status": "error",
            "message": "OAuth authentication failed",
            "token_valid": False,
        }
