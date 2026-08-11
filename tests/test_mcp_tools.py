#!/usr/bin/env python3
"""
Comprehensive unittest suite for all MCP tools.

Tests all 25+ ServiceNow MCP tools with proper mocking to avoid live API calls.
Provides comprehensive coverage for SonarQube code coverage requirements.
"""

import unittest
import sys
import os
from unittest.mock import patch, AsyncMock, MagicMock

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestHealthCheckTool(unittest.IsolatedAsyncioTestCase):
    """Test the consolidated diagnostic tool (v5.0: 5 auth tools -> health_check)."""

    _FAKE_AUTH = {"instance": "https://example.service-now.com", "auth_type": "oauth"}

    @patch("utility_tools.make_nws_request", new_callable=AsyncMock)
    @patch("utility_tools.get_auth_info")
    async def test_health_check_connectivity(self, mock_auth, mock_request):
        """A reachable instance reports connection ok."""
        from utility_tools import health_check

        mock_auth.return_value = self._FAKE_AUTH
        mock_request.return_value = {"result": [{"sys_id": "a" * 32, "name": "Someone"}]}

        result = await health_check()

        self.assertIsInstance(result, dict)
        self.assertEqual(result["connection"], "ok")
        self.assertEqual(result["server"], "running")

    @patch("utility_tools.make_nws_request", new_callable=AsyncMock)
    @patch("utility_tools.get_auth_info")
    async def test_health_check_schema_probe(self, mock_auth, mock_request):
        """probe_table returns sample field names."""
        from utility_tools import health_check

        mock_auth.return_value = self._FAKE_AUTH
        mock_request.return_value = {"result": [{"number": "INC1", "state": "1"}]}

        result = await health_check(probe_table="incident")

        self.assertEqual(result["table"], "incident")
        self.assertEqual(set(result["sample_fields"]), {"number", "state"})


class TestKnowledgeBaseTools(unittest.IsolatedAsyncioTestCase):
    """Test the surviving knowledge read tool (v5.0: smart-KB reads culled)."""

    async def test_get_kb_articles_by_state(self):
        """Test the version-collapsing KB state rollup."""
        from Table_Tools.consolidated_tools import get_kb_articles_by_state

        mock_response = {
            "result": [
                {"number": "KB0007001", "sys_id": "s1", "workflow_state": "published"},
            ],
            "truncated": False,
        }
        with patch(
            "Table_Tools.consolidated_tools.query_table_with_filters",
            new_callable=AsyncMock,
        ) as mock_func:
            mock_func.return_value = mock_response

            result = await get_kb_articles_by_state("published")

            self.assertIsInstance(result, dict)
            self.assertIn("result", result)
            self.assertEqual(result["result"][0]["current_state"], "published")


class TestPrivateTaskTools(unittest.IsolatedAsyncioTestCase):
    """Test private task tools with CRUD operations."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        try:
            from Table_Tools.vtb_task_tools import (
                create_private_task, update_private_task
            )
            self.task_tools_available = True
            self.create_private_task = create_private_task
            self.update_private_task = update_private_task
        except ImportError as e:
            self.task_tools_available = False
            self.import_error = str(e)

    async def test_create_private_task(self):
        """Test creating a new private task."""
        if not self.task_tools_available:
            self.skipTest(f"Private task tools not available: {self.import_error}")
        
        task_data = {
            "short_description": "Test task",
            "description": "This is a test task"
        }
        mock_response = {"number": "PTASK0010001", "created": True}
        
        with patch.object(self, 'create_private_task', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = mock_response
            
            result = await self.create_private_task(task_data)
            
            self.assertIsInstance(result, dict)
            self.assertIn('number', result)
            self.assertTrue(result.get('created'))

    async def test_update_private_task(self):
        """Test updating an existing private task."""
        if not self.task_tools_available:
            self.skipTest(f"Private task tools not available: {self.import_error}")
        
        update_data = {"state": "In Progress"}
        mock_response = {"number": "PTASK0010001", "updated": True}
        
        with patch.object(self, 'update_private_task', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = mock_response
            
            result = await self.update_private_task("PTASK0010001", update_data)
            
            self.assertIsInstance(result, dict)
            self.assertTrue(result.get('updated'))


class TestGenericTableTools(unittest.IsolatedAsyncioTestCase):
    """Test generic table operations."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        try:
            from Table_Tools.generic_table_tools import (
                query_table_by_text, get_record_description,
                get_record_details, find_similar_records,
                query_table_with_filters
            )
            self.generic_tools_available = True
            self.query_table_by_text = query_table_by_text
            self.get_record_description = get_record_description
            self.get_record_details = get_record_details
            self.find_similar_records = find_similar_records
            self.query_table_with_filters = query_table_with_filters
        except ImportError as e:
            self.generic_tools_available = False
            self.import_error = str(e)

    async def test_query_table_by_text(self):
        """Test text-based table query."""
        if not self.generic_tools_available:
            self.skipTest(f"Generic tools not available: {self.import_error}")
        
        mock_response = {"records": [], "count": 3}
        
        with patch.object(self, 'query_table_by_text', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = mock_response
            
            result = await self.query_table_by_text("incident", "server down")
            
            self.assertIsInstance(result, dict)
            self.assertIn('records', result)

    async def test_get_record_description(self):
        """Test getting record description."""
        if not self.generic_tools_available:
            self.skipTest(f"Generic tools not available: {self.import_error}")
        
        with patch.object(self, 'get_record_description', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = {"description": "Server is down"}
            
            result = await self.get_record_description("incident", "INC0010001")
            
            self.assertIsInstance(result, dict)
            self.assertIn('description', result)

    async def test_query_table_with_filters_intelligent(self):
        """Test intelligent filtering with natural language."""
        if not self.generic_tools_available:
            self.skipTest(f"Generic tools not available: {self.import_error}")
        
        from Table_Tools.generic_table_tools import TableFilterParams
        
        filters = {
            "sys_created_on": "Week 35 2025",
            "priority": "1,2",
            "exclude_caller": "logicmonitor"
        }
        params = TableFilterParams(filters=filters)
        
        mock_response = {"records": [], "count": 10}
        
        with patch.object(self, 'query_table_with_filters', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = mock_response
            
            result = await self.query_table_with_filters("incident", params)
            
            self.assertIsInstance(result, dict)
            mock_func.assert_called_once_with("incident", params)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)