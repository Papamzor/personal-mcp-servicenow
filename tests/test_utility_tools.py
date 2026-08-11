#!/usr/bin/env python3
"""
unittest version of Utility Tools tests.

v5.0 "Boron" (Tier 2): the five diagnostics (nowtest / now_test_oauth /
now_auth_info / nowtestauth / nowtest_auth_input) collapsed into one
`health_check(probe_table=None)`. Typed-failure behavior lives in
test_typed_read_utility_tools.py; this file covers the happy-path shape.
"""

import unittest
import sys
import os
from unittest.mock import patch, AsyncMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_FAKE_AUTH = {"instance": "https://example.service-now.com", "auth_type": "oauth"}


class TestHealthCheck(unittest.IsolatedAsyncioTestCase):
    """Test suite for the consolidated health_check diagnostic."""

    async def asyncSetUp(self):
        try:
            from utility_tools import health_check
            self.health_check = health_check
            self.available = True
        except ImportError as e:
            self.available = False
            self.import_error = str(e)

    @patch("utility_tools.make_nws_request", new_callable=AsyncMock)
    @patch("utility_tools.get_auth_info")
    async def test_connectivity_probe_ok(self, mock_auth, mock_request):
        """A reachable instance reports server running, connection ok, and config."""
        if not self.available:
            self.skipTest(f"Utility tools not available: {self.import_error}")

        mock_auth.return_value = _FAKE_AUTH
        mock_request.return_value = {"result": [{"sys_id": "a" * 32, "name": "Someone"}]}

        result = await self.health_check()

        mock_request.assert_called_once()
        self.assertEqual(result["server"], "running")
        self.assertEqual(result["connection"], "ok")
        self.assertEqual(result["auth"], _FAKE_AUTH)

    @patch("utility_tools.make_nws_request", new_callable=AsyncMock)
    @patch("utility_tools.get_auth_info")
    async def test_schema_probe_returns_sample_fields(self, mock_auth, mock_request):
        if not self.available:
            self.skipTest(f"Utility tools not available: {self.import_error}")

        mock_auth.return_value = _FAKE_AUTH
        mock_request.return_value = {"result": [{"number": "INC1", "state": "1"}]}

        result = await self.health_check(probe_table="incident")

        self.assertEqual(result["connection"], "ok")
        self.assertEqual(result["table"], "incident")
        self.assertEqual(set(result["sample_fields"]), {"number", "state"})


if __name__ == '__main__':
    unittest.main()
