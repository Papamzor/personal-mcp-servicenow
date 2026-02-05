#!/usr/bin/env python3
"""
unittest version of ServiceNow API tests.

Tests the service_now_api_oauth.py module functionality with proper mocking
to avoid live API calls and achieve comprehensive coverage.
"""

import unittest
import sys
import os
from unittest.mock import patch, AsyncMock

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestServiceNowAPI(unittest.IsolatedAsyncioTestCase):
    """Test suite for ServiceNow API functionality."""

    async def asyncSetUp(self):
        """Set up test fixtures for async tests."""
        try:
            from service_now_api_oauth import (
                _extract_field_value, _process_item_dict, _extract_display_values,
                _ensure_query_encoded, _add_default_params, make_nws_request, NWS_API_BASE
            )
            self.api_available = True
            self._extract_field_value = _extract_field_value
            self._process_item_dict = _process_item_dict
            self._extract_display_values = _extract_display_values
            self._ensure_query_encoded = _ensure_query_encoded
            self._add_default_params = _add_default_params
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

    # --- _ensure_query_encoded tests ---

    async def test_ensure_query_encoded_no_sysparm_query(self):
        """Test that URLs without sysparm_query pass through unchanged."""
        if not self.api_available:
            self.skipTest(f"ServiceNow API not available: {self.import_error}")

        url = "https://test.service-now.com/api/now/table/incident?sysparm_limit=10"
        result = self._ensure_query_encoded(url)
        self.assertEqual(result, url)

    async def test_ensure_query_encoded_spaces(self):
        """Test that spaces in query values are percent-encoded."""
        if not self.api_available:
            self.skipTest(f"ServiceNow API not available: {self.import_error}")

        url = "https://test.service-now.com/api/now/table/incident?sysparm_query=short_descriptionCONTAINSserver down"
        result = self._ensure_query_encoded(url)
        self.assertIn("sysparm_query=short_descriptionCONTAINSserver%20down", result)

    async def test_ensure_query_encoded_preserves_sn_operators(self):
        """Test that ServiceNow operators (=, ^, <, >, etc.) are preserved."""
        if not self.api_available:
            self.skipTest(f"ServiceNow API not available: {self.import_error}")

        url = "https://test.service-now.com/api/now/table/incident?sysparm_query=priority=1^state=2^ORstate=3"
        result = self._ensure_query_encoded(url)
        self.assertEqual(result, url)

    async def test_ensure_query_encoded_hash_character(self):
        """Test that # in query is encoded to prevent URL fragment issues."""
        if not self.api_available:
            self.skipTest(f"ServiceNow API not available: {self.import_error}")

        url = "https://test.service-now.com/api/now/table/incident?sysparm_query=short_descriptionCONTAINSissue #123"
        result = self._ensure_query_encoded(url)
        self.assertIn("sysparm_query=short_descriptionCONTAINSissue%20%23123", result)
        self.assertNotIn("#", result.split("sysparm_query=")[1].split("&")[0])

    async def test_ensure_query_encoded_idempotent(self):
        """Test that already-encoded URLs are not double-encoded."""
        if not self.api_available:
            self.skipTest(f"ServiceNow API not available: {self.import_error}")

        url = "https://test.service-now.com/api/now/table/incident?sysparm_query=short_descriptionCONTAINSserver%20down"
        result = self._ensure_query_encoded(url)
        self.assertIn("server%20down", result)
        self.assertNotIn("%2520", result)

    async def test_ensure_query_encoded_preserves_other_params(self):
        """Test that other URL parameters are not affected by encoding."""
        if not self.api_available:
            self.skipTest(f"ServiceNow API not available: {self.import_error}")

        url = "https://test.service-now.com/api/now/table/incident?sysparm_fields=number&sysparm_query=short_descriptionCONTAINSserver down&sysparm_limit=10"
        result = self._ensure_query_encoded(url)
        self.assertIn("sysparm_fields=number", result)
        self.assertIn("sysparm_query=short_descriptionCONTAINSserver%20down", result)
        self.assertIn("sysparm_limit=10", result)

    # --- _add_default_params tests ---

    async def test_add_default_params_no_query_string(self):
        """Test adding params to URL with no existing query string."""
        if not self.api_available:
            self.skipTest(f"ServiceNow API not available: {self.import_error}")

        url = "https://test.service-now.com/api/now/table/incident"
        result = self._add_default_params(url)

        self.assertIn("?", result)
        self.assertIn("sysparm_display_value=true", result)
        self.assertIn("sysparm_exclude_reference_link=true", result)
        self.assertIn("sysparm_no_count=true", result)

    async def test_add_default_params_existing_query_string(self):
        """Test adding params to URL that already has a query string."""
        if not self.api_available:
            self.skipTest(f"ServiceNow API not available: {self.import_error}")

        url = "https://test.service-now.com/api/now/table/incident?sysparm_fields=number"
        result = self._add_default_params(url)

        self.assertIn("sysparm_fields=number", result)
        self.assertIn("&sysparm_display_value=true", result)
        self.assertIn("sysparm_exclude_reference_link=true", result)
        self.assertIn("sysparm_no_count=true", result)
        self.assertEqual(result.count("?"), 1)

    async def test_add_default_params_display_value_false(self):
        """Test that display_value=False skips sysparm_display_value but adds perf params."""
        if not self.api_available:
            self.skipTest(f"ServiceNow API not available: {self.import_error}")

        url = "https://test.service-now.com/api/now/table/incident"
        result = self._add_default_params(url, display_value=False)

        self.assertNotIn("sysparm_display_value", result)
        self.assertIn("sysparm_exclude_reference_link=true", result)
        self.assertIn("sysparm_no_count=true", result)

    async def test_add_default_params_idempotent(self):
        """Test that params are not duplicated when already present."""
        if not self.api_available:
            self.skipTest(f"ServiceNow API not available: {self.import_error}")

        url = (
            "https://test.service-now.com/api/now/table/incident"
            "?sysparm_display_value=true"
            "&sysparm_exclude_reference_link=true"
            "&sysparm_no_count=true"
        )
        result = self._add_default_params(url)

        self.assertEqual(result, url)

    async def test_add_default_params_partial_existing(self):
        """Test that only missing params are added when some already present."""
        if not self.api_available:
            self.skipTest(f"ServiceNow API not available: {self.import_error}")

        url = "https://test.service-now.com/api/now/table/incident?sysparm_display_value=true"
        result = self._add_default_params(url)

        self.assertEqual(result.count("sysparm_display_value"), 1)
        self.assertIn("sysparm_exclude_reference_link=true", result)
        self.assertIn("sysparm_no_count=true", result)

    # --- make_nws_request tests ---

    @patch('service_now_api_oauth.make_oauth_request')
    async def test_make_nws_request_success(self, mock_oauth_request):
        """Test successful API request includes all default params."""
        if not self.api_available:
            self.skipTest(f"ServiceNow API not available: {self.import_error}")

        mock_oauth_request.return_value = {
            'result': [
                {'number': {'value': 'INC001', 'display_value': 'INC001'}}
            ]
        }

        url = "https://test.service-now.com/api/now/table/incident"
        result = await self.make_nws_request(url)

        # Verify the request was made with all default params
        mock_oauth_request.assert_called_once()
        called_url = mock_oauth_request.call_args[0][0]
        self.assertIn("sysparm_display_value=true", called_url)
        self.assertIn("sysparm_exclude_reference_link=true", called_url)
        self.assertIn("sysparm_no_count=true", called_url)

        # Check result is processed (display values extracted)
        expected = {
            'result': [
                {'number': 'INC001'}
            ]
        }
        self.assertEqual(result, expected)

    @patch('service_now_api_oauth.make_oauth_request')
    async def test_make_nws_request_encodes_query(self, mock_oauth_request):
        """Test that make_nws_request encodes sysparm_query before sending."""
        if not self.api_available:
            self.skipTest(f"ServiceNow API not available: {self.import_error}")

        mock_oauth_request.return_value = {'result': []}

        url = "https://test.service-now.com/api/now/table/incident?sysparm_query=short_descriptionCONTAINSserver down"
        await self.make_nws_request(url)

        called_url = mock_oauth_request.call_args[0][0]
        self.assertIn("server%20down", called_url)
        self.assertNotIn("server down", called_url)

    @patch('service_now_api_oauth.make_oauth_request')
    async def test_make_nws_request_http_error(self, mock_oauth_request):
        """Test API request with error returns None."""
        if not self.api_available:
            self.skipTest(f"ServiceNow API not available: {self.import_error}")

        mock_oauth_request.side_effect = Exception("404 Not Found")

        url = "https://test.service-now.com/api/now/table/nonexistent"
        result = await self.make_nws_request(url)

        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
