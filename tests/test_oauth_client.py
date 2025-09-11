import unittest
import sys
import os
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import httpx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestOAuthClientExtended(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        try:
            from oauth_client import ServiceNowOAuthClient, ServiceNowAuthenticationError, ServiceNowConnectionError
            self.oauth_available = True
            self.ServiceNowOAuthClient = ServiceNowOAuthClient
            self.ServiceNowAuthenticationError = ServiceNowAuthenticationError
            self.ServiceNowConnectionError = ServiceNowConnectionError
        except ImportError as e:
            self.oauth_available = False
            self.import_error = str(e)

    @patch.dict("os.environ", {"SERVICENOW_INSTANCE": "https://test.service-now.com", "SERVICENOW_CLIENT_ID": "test_id", "SERVICENOW_CLIENT_SECRET": "test_secret"})
    def test_basic_init(self):
        if not self.oauth_available:
            self.skipTest(f"OAuth client not available: {self.import_error}")
        client = self.ServiceNowOAuthClient()
        self.assertEqual(client.instance_url, "https://test.service-now.com")

    @patch.dict("os.environ", {"SERVICENOW_INSTANCE": "https://test.service-now.com", "SERVICENOW_CLIENT_ID": "test_id", "SERVICENOW_CLIENT_SECRET": "test_secret"})
    @patch("oauth_client.httpx.AsyncClient")
    async def test_token_request_with_errors(self, mock_client_class):
        if not self.oauth_available:
            self.skipTest(f"OAuth client not available: {self.import_error}")
        
        # Test 401 error
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_error = httpx.HTTPStatusError("401 Unauthorized", request=MagicMock(), response=mock_response)
        mock_client = MagicMock()
        mock_client.post = AsyncMock(side_effect=mock_error)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        client = self.ServiceNowOAuthClient()
        with self.assertRaises(self.ServiceNowAuthenticationError):
            await client._request_access_token()

    @patch.dict("os.environ", {"SERVICENOW_INSTANCE": "https://test.service-now.com", "SERVICENOW_CLIENT_ID": "test_id", "SERVICENOW_CLIENT_SECRET": "test_secret"})
    @patch("oauth_client.httpx.AsyncClient")
    async def test_connection_error(self, mock_client_class):
        if not self.oauth_available:
            self.skipTest(f"OAuth client not available: {self.import_error}")
        
        mock_client = MagicMock()
        mock_client.post = AsyncMock(side_effect=httpx.RequestError("Connection failed"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        client = self.ServiceNowOAuthClient()
        with self.assertRaises(self.ServiceNowConnectionError):
            await client._request_access_token()

    @patch.dict("os.environ", {"SERVICENOW_INSTANCE": "https://test.service-now.com", "SERVICENOW_CLIENT_ID": "test_id", "SERVICENOW_CLIENT_SECRET": "test_secret"})
    async def test_expired_token_refresh(self):
        if not self.oauth_available:
            self.skipTest(f"OAuth client not available: {self.import_error}")
        
        client = self.ServiceNowOAuthClient()
        client._access_token = "expired_token"
        client._token_expires_at = datetime.now() - timedelta(minutes=5)
        
        with patch.object(client, "_request_access_token", return_value={"access_token": "new_token", "expires_in": 1800}) as mock_request:
            token = await client._get_valid_token()
            mock_request.assert_called_once()
            self.assertEqual(token, "new_token")
            self.assertEqual(client._access_token, "new_token")

if __name__ == "__main__":
    unittest.main()
