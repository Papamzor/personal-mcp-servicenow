#!/usr/bin/env python3
"""
unittest version of Utility Tools tests.
"""

import unittest
import sys
import os
from unittest.mock import patch, AsyncMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestUtilityTools(unittest.IsolatedAsyncioTestCase):
    """Test suite for utility tools functionality."""

    async def asyncSetUp(self):
        """Set up test fixtures for async tests."""
        try:
            from utility_tools import nowtest, now_test_oauth, now_auth_info
            self.utility_available = True
            self.nowtest = nowtest
            self.now_test_oauth = now_test_oauth
            self.now_auth_info = now_auth_info
        except ImportError as e:
            self.utility_available = False
            self.import_error = str(e)

    def test_nowtest_success(self):
        """Test basic server status check."""
        if not self.utility_available:
            self.skipTest(f"Utility tools not available: {self.import_error}")
        
        result = self.nowtest()
        
        self.assertIsInstance(result, str)
        self.assertIn("Server is running", result)

    @patch('utility_tools.test_oauth_connection', new_callable=AsyncMock)
    async def test_now_test_oauth_success(self, mock_test_oauth):
        """Test OAuth connection test with successful result."""
        if not self.utility_available:
            self.skipTest(f"Utility tools not available: {self.import_error}")
        
        mock_test_oauth.return_value = {'status': 'success'}
        
        result = await self.now_test_oauth()
        
        mock_test_oauth.assert_called_once()
        self.assertIsInstance(result, dict)

    @patch('utility_tools.get_auth_info', new_callable=AsyncMock)
    async def test_now_auth_info_success(self, mock_get_auth_info):
        """Test getting authentication information successfully."""
        if not self.utility_available:
            self.skipTest(f"Utility tools not available: {self.import_error}")
        
        mock_get_auth_info.return_value = {
            'auth_method': 'OAuth 2.0',
            'client_configured': True
        }
        
        result = await self.now_auth_info()
        
        mock_get_auth_info.assert_called_once()
        self.assertIsInstance(result, dict)


if __name__ == '__main__':
    unittest.main()
