#!/usr/bin/env python3
"""
unittest version of ServiceNow API tests.

Tests the service_now_api.py module functionality with proper mocking 
to avoid live API calls and achieve comprehensive coverage.
"""

import unittest
import sys
import os
from unittest.mock import patch, AsyncMock, MagicMock
import httpx

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestServiceNowAPI(unittest.IsolatedAsyncioTestCase):
    """Test suite for ServiceNow API functionality."""

    async def asyncSetUp(self):
        """Set up test fixtures for async tests."""
        try:
            from service_now_api import (
                _extract_field_value, _process_item_dict, _extract_display_values, 
                make_nws_request, NWS_API_BASE
            )
            self.api_available = True
            self._extract_field_value = _extract_field_value
            self._process_item_dict = _process_item_dict
            self._extract_display_values = _extract_display_values
            self.make_nws_request = make_nws_request
            self.NWS_API_BASE = NWS_API_BASE
        except ImportError as e:
            self.api_available = False
            self.import_error = str(e)

    async def test_extract_field_value_with_display_value(self):
        """Test extracting field value when display_value is available."""
        if not self.api_available:
            self.skipTest(f"ServiceNow API not available: {self.import_error}")
        
        test_value = {
            'value': 'raw_value',
            'display_value': 'Human Readable Value'
        }
        
        result = self._extract_field_value(test_value)
        self.assertEqual(result, 'Human Readable Value')

    async def test_extract_field_value_simple_value(self):
        """Test extracting simple non-dict values."""
        if not self.api_available:
            self.skipTest(f"ServiceNow API not available: {self.import_error}")
        
        result = self._extract_field_value("simple_string")
        self.assertEqual(result, "simple_string")
        
        result = self._extract_field_value(12345)
        self.assertEqual(result, 12345)

    async def test_process_item_dict_success(self):
        """Test processing a dictionary item with mixed field types."""
        if not self.api_available:
            self.skipTest(f"ServiceNow API not available: {self.import_error}")
        
        test_item = {
            'number': {'value': 'INC001001', 'display_value': 'INC001001'},
            'state': {'value': '1', 'display_value': 'New'},
            'simple_field': 'simple_value'
        }
        
        result = self._process_item_dict(test_item)
        
        expected = {
            'number': 'INC001001',
            'state': 'New',
            'simple_field': 'simple_value'
        }
        
        self.assertEqual(result, expected)

    async def test_extract_display_values_with_results(self):
        """Test extracting display values from API response with results."""
        if not self.api_available:
            self.skipTest(f"ServiceNow API not available: {self.import_error}")
        
        test_data = {
            'result': [
                {
                    'number': {'value': 'INC001001', 'display_value': 'INC001001'},
                    'state': {'value': '1', 'display_value': 'New'}
                }
            ]
        }
        
        result = self._extract_display_values(test_data)
        
        expected = {
            'result': [
                {
                    'number': 'INC001001',
                    'state': 'New'
                }
            ]
        }
        
        self.assertEqual(result, expected)

    async def test_extract_display_values_non_dict_input(self):
        """Test extracting display values from non-dict input."""
        if not self.api_available:
            self.skipTest(f"ServiceNow API not available: {self.import_error}")
        
        result = self._extract_display_values("string_input")
        self.assertEqual(result, "string_input")

    @patch('service_now_api.httpx.AsyncClient')
    async def test_make_nws_request_success(self, mock_client_class):
        """Test successful API request."""
        if not self.api_available:
            self.skipTest(f"ServiceNow API not available: {self.import_error}")
        
        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'result': [
                {'number': {'value': 'INC001', 'display_value': 'INC001'}}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        # Mock the client context manager and get method
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client
        
        url = "https://test.service-now.com/api/now/table/incident"
        result = await self.make_nws_request(url)
        
        # Verify the request was made correctly
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        
        # Check URL includes display_value parameter
        called_url = call_args[0][0]
        self.assertIn("sysparm_display_value=true", called_url)
        
        # Check result is processed
        expected = {
            'result': [
                {'number': 'INC001'}
            ]
        }
        self.assertEqual(result, expected)

    @patch('service_now_api.httpx.AsyncClient')
    async def test_make_nws_request_http_error(self, mock_client_class):
        """Test API request with HTTP error."""
        if not self.api_available:
            self.skipTest(f"ServiceNow API not available: {self.import_error}")
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=MagicMock()
        ))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client
        
        url = "https://test.service-now.com/api/now/table/nonexistent"
        result = await self.make_nws_request(url)
        
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
