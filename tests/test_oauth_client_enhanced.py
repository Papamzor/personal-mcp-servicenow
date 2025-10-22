"""
Comprehensive tests for oauth_client.py
Target: 90%+ line coverage, 75%+ branch coverage
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import httpx
import json

# Import classes and functions to test
from oauth_client import (
    ServiceNowOAuthClient,
    ServiceNowOAuthError,
    ServiceNowAuthenticationError,
    ServiceNowConnectionError,
    ServiceNowAuthorizationError,
    get_oauth_client,
    make_oauth_request,
    _oauth_client
)


class TestServiceNowOAuthExceptions:
    """Test custom exception classes."""

    def test_oauth_error_inheritance(self):
        """Test that OAuth error inherits from Exception."""
        error = ServiceNowOAuthError("test error")
        assert isinstance(error, Exception)
        assert str(error) == "test error"

    def test_authentication_error_inheritance(self):
        """Test that AuthenticationError inherits from OAuthError."""
        error = ServiceNowAuthenticationError("auth failed")
        assert isinstance(error, ServiceNowOAuthError)
        assert isinstance(error, Exception)

    def test_connection_error_inheritance(self):
        """Test that ConnectionError inherits from OAuthError."""
        error = ServiceNowConnectionError("connection failed")
        assert isinstance(error, ServiceNowOAuthError)

    def test_authorization_error_inheritance(self):
        """Test that AuthorizationError inherits from OAuthError."""
        error = ServiceNowAuthorizationError("access denied")
        assert isinstance(error, ServiceNowOAuthError)


class TestServiceNowOAuthClientInit:
    """Test OAuth client initialization."""

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    def test_init_with_valid_config(self):
        """Test initialization with valid configuration."""
        client = ServiceNowOAuthClient()
        assert client.instance_url == "https://test.service-now.com"
        assert client.client_id == "test_id"
        assert client.client_secret == "test_secret"
        assert client.token_endpoint == "https://test.service-now.com/oauth_token.do"
        assert client._access_token is None
        assert client._token_expires_at is None

    @patch.dict("os.environ", {}, clear=True)
    def test_init_missing_instance(self):
        """Test initialization fails when SERVICENOW_INSTANCE is missing."""
        with pytest.raises(ValueError) as exc_info:
            ServiceNowOAuthClient()
        assert "Missing OAuth configuration" in str(exc_info.value)

    @patch.dict("os.environ", {"SERVICENOW_INSTANCE": "https://test.service-now.com"}, clear=True)
    def test_init_missing_client_id(self):
        """Test initialization fails when CLIENT_ID is missing."""
        with pytest.raises(ValueError) as exc_info:
            ServiceNowOAuthClient()
        assert "Missing OAuth configuration" in str(exc_info.value)

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id"
    }, clear=True)
    def test_init_missing_client_secret(self):
        """Test initialization fails when CLIENT_SECRET is missing."""
        with pytest.raises(ValueError) as exc_info:
            ServiceNowOAuthClient()
        assert "Missing OAuth configuration" in str(exc_info.value)


class TestBasicAuthHeader:
    """Test Basic Auth header generation."""

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    def test_get_basic_auth_header(self):
        """Test Basic Auth header generation."""
        client = ServiceNowOAuthClient()
        header = client._get_basic_auth_header()

        assert header.startswith("Basic ")
        # Verify it's base64 encoded
        import base64
        encoded_part = header.replace("Basic ", "")
        decoded = base64.b64decode(encoded_part).decode()
        assert decoded == "test_id:test_secret"


class TestTokenRequest:
    """Test access token request functionality."""

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    @pytest.mark.asyncio
    async def test_request_access_token_success(self):
        """Test successful token request."""
        with patch("oauth_client.httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "test_token_123",
                "expires_in": 1800
            }

            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = ServiceNowOAuthClient()
            result = await client._request_access_token()

            assert result["access_token"] == "test_token_123"
            assert result["expires_in"] == 1800

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    @pytest.mark.asyncio
    async def test_request_access_token_401_error(self):
        """Test token request with 401 authentication error."""
        with patch("oauth_client.httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 401

            mock_error = httpx.HTTPStatusError(
                "401 Unauthorized",
                request=MagicMock(),
                response=mock_response
            )

            mock_client = MagicMock()
            mock_client.post = AsyncMock(side_effect=mock_error)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = ServiceNowOAuthClient()
            with pytest.raises(ServiceNowAuthenticationError) as exc_info:
                await client._request_access_token()
            assert "Invalid client credentials" in str(exc_info.value)

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    @pytest.mark.asyncio
    async def test_request_access_token_403_error(self):
        """Test token request with 403 authorization error."""
        with patch("oauth_client.httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 403

            mock_error = httpx.HTTPStatusError(
                "403 Forbidden",
                request=MagicMock(),
                response=mock_response
            )

            mock_client = MagicMock()
            mock_client.post = AsyncMock(side_effect=mock_error)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = ServiceNowOAuthClient()
            with pytest.raises(ServiceNowAuthorizationError) as exc_info:
                await client._request_access_token()
            assert "Access denied" in str(exc_info.value)

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    @pytest.mark.asyncio
    async def test_request_access_token_500_error(self):
        """Test token request with 500 server error."""
        with patch("oauth_client.httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 500

            mock_error = httpx.HTTPStatusError(
                "500 Server Error",
                request=MagicMock(),
                response=mock_response
            )

            mock_client = MagicMock()
            mock_client.post = AsyncMock(side_effect=mock_error)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = ServiceNowOAuthClient()
            with pytest.raises(ServiceNowOAuthError) as exc_info:
                await client._request_access_token()
            assert "Server error" in str(exc_info.value)
            assert "500" in str(exc_info.value)

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    @pytest.mark.asyncio
    async def test_request_access_token_connection_error(self):
        """Test token request with connection error."""
        with patch("oauth_client.httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(side_effect=httpx.RequestError("Connection failed"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = ServiceNowOAuthClient()
            with pytest.raises(ServiceNowConnectionError) as exc_info:
                await client._request_access_token()
            assert "Connection failed" in str(exc_info.value)

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    @pytest.mark.asyncio
    async def test_request_access_token_timeout_error(self):
        """Test token request with timeout error."""
        with patch("oauth_client.httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = ServiceNowOAuthClient()
            with pytest.raises(ServiceNowConnectionError) as exc_info:
                await client._request_access_token()
            assert "Connection failed" in str(exc_info.value)

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    @pytest.mark.asyncio
    async def test_request_access_token_json_decode_error(self):
        """Test token request with JSON decode error."""
        with patch("oauth_client.httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = ServiceNowOAuthClient()
            with pytest.raises(ServiceNowOAuthError) as exc_info:
                await client._request_access_token()
            assert "response parsing failed" in str(exc_info.value)


class TestTokenManagement:
    """Test token caching and refresh functionality."""

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    @pytest.mark.asyncio
    async def test_get_valid_token_when_none_exists(self):
        """Test getting token when none exists."""
        with patch.object(ServiceNowOAuthClient, "_request_access_token") as mock_request:
            mock_request.return_value = {"access_token": "new_token", "expires_in": 1800}

            client = ServiceNowOAuthClient()
            token = await client._get_valid_token()

            assert token == "new_token"
            assert client._access_token == "new_token"
            assert client._token_expires_at is not None
            mock_request.assert_called_once()

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    @pytest.mark.asyncio
    async def test_get_valid_token_when_valid_exists(self):
        """Test using cached token when still valid."""
        client = ServiceNowOAuthClient()
        client._access_token = "cached_token"
        client._token_expires_at = datetime.now() + timedelta(minutes=10)

        with patch.object(client, "_request_access_token") as mock_request:
            token = await client._get_valid_token()

            assert token == "cached_token"
            mock_request.assert_not_called()

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    @pytest.mark.asyncio
    async def test_get_valid_token_when_expired(self):
        """Test refreshing token when expired."""
        client = ServiceNowOAuthClient()
        client._access_token = "expired_token"
        client._token_expires_at = datetime.now() - timedelta(minutes=5)

        with patch.object(client, "_request_access_token") as mock_request:
            mock_request.return_value = {"access_token": "refreshed_token", "expires_in": 1800}

            token = await client._get_valid_token()

            assert token == "refreshed_token"
            assert client._access_token == "refreshed_token"
            mock_request.assert_called_once()

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    @pytest.mark.asyncio
    async def test_get_auth_headers(self):
        """Test getting authorization headers."""
        client = ServiceNowOAuthClient()

        with patch.object(client, "_get_valid_token") as mock_get_token:
            mock_get_token.return_value = "test_token_abc"

            headers = await client.get_auth_headers()

            assert headers["Authorization"] == "Bearer test_token_abc"
            assert "Content-Type" in headers
            assert "Accept" in headers

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    @pytest.mark.asyncio
    async def test_clear_token_cache(self):
        """Test clearing token cache."""
        client = ServiceNowOAuthClient()
        client._access_token = "test_token"
        client._token_expires_at = datetime.now()

        await client._clear_token_cache()

        assert client._access_token is None
        assert client._token_expires_at is None


class TestAuthenticatedRequests:
    """Test making authenticated API requests."""

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    @pytest.mark.asyncio
    async def test_make_authenticated_request_success(self):
        """Test successful authenticated request."""
        with patch("oauth_client.httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"result": "success"}

            mock_client = MagicMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = ServiceNowOAuthClient()
            with patch.object(client, "get_auth_headers") as mock_headers:
                mock_headers.return_value = {"Authorization": "Bearer test_token"}

                result = await client.make_authenticated_request("GET", "https://test.service-now.com/api/test")

                assert result == {"result": "success"}

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    @pytest.mark.asyncio
    async def test_make_authenticated_request_with_retry_success(self):
        """Test authenticated request with 401 and successful retry."""
        with patch("oauth_client.httpx.AsyncClient") as mock_client_class:
            # First response: 401
            mock_response_401 = MagicMock()
            mock_response_401.status_code = 401
            mock_error = httpx.HTTPStatusError("401", request=MagicMock(), response=mock_response_401)

            # Second response: Success
            mock_response_200 = MagicMock()
            mock_response_200.status_code = 200
            mock_response_200.json.return_value = {"result": "success after retry"}

            mock_client = MagicMock()
            mock_client.request = AsyncMock(side_effect=[mock_error, mock_response_200])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = ServiceNowOAuthClient()
            with patch.object(client, "get_auth_headers") as mock_headers:
                mock_headers.return_value = {"Authorization": "Bearer test_token"}

                result = await client.make_authenticated_request("GET", "https://test.service-now.com/api/test")

                assert result == {"result": "success after retry"}
                assert mock_client.request.call_count == 2  # Initial + retry

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    @pytest.mark.asyncio
    async def test_make_authenticated_request_non_401_error(self):
        """Test authenticated request with non-401 HTTP error."""
        with patch("oauth_client.httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_error = httpx.HTTPStatusError("500", request=MagicMock(), response=mock_response)

            mock_client = MagicMock()
            mock_client.request = AsyncMock(side_effect=mock_error)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = ServiceNowOAuthClient()
            with patch.object(client, "get_auth_headers") as mock_headers:
                mock_headers.return_value = {"Authorization": "Bearer test_token"}

                result = await client.make_authenticated_request("GET", "https://test.service-now.com/api/test")

                assert result is None

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    @pytest.mark.asyncio
    async def test_make_authenticated_request_connection_error(self):
        """Test authenticated request with connection error."""
        with patch("oauth_client.httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.request = AsyncMock(side_effect=httpx.RequestError("Connection failed"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = ServiceNowOAuthClient()
            with patch.object(client, "get_auth_headers") as mock_headers:
                mock_headers.return_value = {"Authorization": "Bearer test_token"}

                result = await client.make_authenticated_request("GET", "https://test.service-now.com/api/test")

                assert result is None

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    @pytest.mark.asyncio
    async def test_make_authenticated_request_timeout_error(self):
        """Test authenticated request with timeout."""
        with patch("oauth_client.httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.request = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = ServiceNowOAuthClient()
            with patch.object(client, "get_auth_headers") as mock_headers:
                mock_headers.return_value = {"Authorization": "Bearer test_token"}

                result = await client.make_authenticated_request("GET", "https://test.service-now.com/api/test")

                assert result is None

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    @pytest.mark.asyncio
    async def test_make_authenticated_request_json_decode_error(self):
        """Test authenticated request with JSON decode error."""
        with patch("oauth_client.httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

            mock_client = MagicMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = ServiceNowOAuthClient()
            with patch.object(client, "get_auth_headers") as mock_headers:
                mock_headers.return_value = {"Authorization": "Bearer test_token"}

                result = await client.make_authenticated_request("GET", "https://test.service-now.com/api/test")

                assert result is None


class TestConnectionTesting:
    """Test connection testing functionality."""

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    @pytest.mark.asyncio
    async def test_test_connection_success(self):
        """Test successful connection test."""
        client = ServiceNowOAuthClient()
        client._token_expires_at = datetime.now() + timedelta(minutes=30)

        with patch.object(client, "make_authenticated_request") as mock_request:
            mock_request.return_value = {"result": [{"sys_id": "test"}]}

            result = await client.test_connection()

            assert result["status"] == "success"
            assert result["token_valid"] is True
            assert "expires_at" in result

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    @pytest.mark.asyncio
    async def test_test_connection_failure(self):
        """Test failed connection test."""
        client = ServiceNowOAuthClient()

        with patch.object(client, "make_authenticated_request") as mock_request:
            mock_request.return_value = None

            result = await client.test_connection()

            assert result["status"] == "error"
            assert result["token_valid"] is False


class TestGlobalClientInstance:
    """Test global client instance management."""

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    def test_get_oauth_client_creates_instance(self):
        """Test that get_oauth_client creates instance."""
        # Reset global client
        import oauth_client
        oauth_client._oauth_client = None

        client = get_oauth_client()
        assert client is not None
        assert isinstance(client, ServiceNowOAuthClient)

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    def test_get_oauth_client_returns_same_instance(self):
        """Test that get_oauth_client returns same instance."""
        import oauth_client
        oauth_client._oauth_client = None

        client1 = get_oauth_client()
        client2 = get_oauth_client()
        assert client1 is client2

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    @pytest.mark.asyncio
    async def test_make_oauth_request(self):
        """Test convenience make_oauth_request function."""
        import oauth_client
        oauth_client._oauth_client = None

        with patch("oauth_client.ServiceNowOAuthClient.make_authenticated_request") as mock_request:
            mock_request.return_value = {"result": "success"}

            result = await make_oauth_request("https://test.service-now.com/api/test")

            assert result == {"result": "success"}
            mock_request.assert_called_once()


class TestRetryWithFreshToken:
    """Test retry with fresh token functionality."""

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    @pytest.mark.asyncio
    async def test_retry_with_fresh_token_success(self):
        """Test successful retry with fresh token."""
        with patch("oauth_client.httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"result": "success"}

            mock_client = MagicMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = ServiceNowOAuthClient()

            with patch.object(client, "get_auth_headers") as mock_headers:
                mock_headers.return_value = {"Authorization": "Bearer new_token"}

                result = await client._retry_with_fresh_token(
                    mock_client,
                    "GET",
                    "https://test.service-now.com/api/test"
                )

                assert result == {"result": "success"}

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    @pytest.mark.asyncio
    async def test_retry_with_fresh_token_failure(self):
        """Test retry with fresh token that fails."""
        with patch("oauth_client.httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_error = httpx.HTTPStatusError("401", request=MagicMock(), response=mock_response)

            mock_client = MagicMock()
            mock_client.request = AsyncMock(side_effect=mock_error)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = ServiceNowOAuthClient()

            with patch.object(client, "get_auth_headers") as mock_headers:
                mock_headers.return_value = {"Authorization": "Bearer new_token"}

                result = await client._retry_with_fresh_token(
                    mock_client,
                    "GET",
                    "https://test.service-now.com/api/test"
                )

                assert result is None


class TestProcessResponse:
    """Test response processing."""

    @patch.dict("os.environ", {
        "SERVICENOW_INSTANCE": "https://test.service-now.com",
        "SERVICENOW_CLIENT_ID": "test_id",
        "SERVICENOW_CLIENT_SECRET": "test_secret"
    })
    def test_process_response(self):
        """Test processing successful response."""
        client = ServiceNowOAuthClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "test"}

        result = client._process_response(mock_response)

        assert result == {"data": "test"}
