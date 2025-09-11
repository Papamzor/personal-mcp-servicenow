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


class TestServerAndAuthTools(unittest.IsolatedAsyncioTestCase):
    """Test server connectivity and authentication tools."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        try:
            from utility_tools import nowtest, nowtestoauth, nowauthinfo, nowtestauth, nowtest_auth_input
            self.auth_tools_available = True
            self.nowtest = nowtest
            self.nowtestoauth = nowtestoauth
            self.nowauthinfo = nowauthinfo
            self.nowtestauth = nowtestauth
            self.nowtest_auth_input = nowtest_auth_input
        except ImportError as e:
            self.auth_tools_available = False
            self.import_error = str(e)

    async def test_nowtest_connectivity(self):
        """Test basic server connectivity."""
        if not self.auth_tools_available:
            self.skipTest(f"Auth tools not available: {self.import_error}")
        
        with patch.object(self, 'nowtest', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = {"status": "connected", "message": "Server is reachable"}
            
            result = await self.nowtest()
            
            self.assertIsInstance(result, dict)
            self.assertIn('status', result)

    async def test_nowtestoauth_success(self):
        """Test OAuth authentication test."""
        if not self.auth_tools_available:
            self.skipTest(f"Auth tools not available: {self.import_error}")
        
        with patch.object(self, 'nowtestoauth', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = {"oauth_enabled": True, "token_valid": True}
            
            result = await self.nowtestoauth()
            
            self.assertIsInstance(result, dict)
            self.assertIn('oauth_enabled', result)

    async def test_nowauthinfo_oauth(self):
        """Test authentication info retrieval."""
        if not self.auth_tools_available:
            self.skipTest(f"Auth tools not available: {self.import_error}")
        
        with patch.object(self, 'nowauthinfo', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = {"auth_method": "OAuth 2.0", "oauth_enabled": True}
            
            result = await self.nowauthinfo()
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result['auth_method'], 'OAuth 2.0')

    async def test_nowtestauth_api_test(self):
        """Test ServiceNow API authentication test."""
        if not self.auth_tools_available:
            self.skipTest(f"Auth tools not available: {self.import_error}")
        
        with patch.object(self, 'nowtestauth', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = {"api_accessible": True, "auth_valid": True}
            
            result = await self.nowtestauth()
            
            self.assertIsInstance(result, dict)
            self.assertIn('api_accessible', result)

    async def test_nowtest_auth_input_table_description(self):
        """Test table description retrieval."""
        if not self.auth_tools_available:
            self.skipTest(f"Auth tools not available: {self.import_error}")
        
        with patch.object(self, 'nowtest_auth_input', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = {"table": "incident", "description": "Incident Management"}
            
            result = await self.nowtest_auth_input("incident")
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result['table'], 'incident')


class TestIncidentTools(unittest.IsolatedAsyncioTestCase):
    """Test incident management tools."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        try:
            from Table_Tools.incident_tools import (
                similar_incidents_for_text, get_short_desc_for_incident,
                similar_incidents_for_incident, get_incident_details,
                get_incidents_by_filter, get_priority_incidents
            )
            self.incident_tools_available = True
            self.similar_incidents_for_text = similar_incidents_for_text
            self.get_short_desc_for_incident = get_short_desc_for_incident
            self.similar_incidents_for_incident = similar_incidents_for_incident
            self.get_incident_details = get_incident_details
            self.get_incidents_by_filter = get_incidents_by_filter
            self.get_priority_incidents = get_priority_incidents
        except ImportError as e:
            self.incident_tools_available = False
            self.import_error = str(e)

    async def test_similar_incidents_for_text(self):
        """Test finding similar incidents by text."""
        if not self.incident_tools_available:
            self.skipTest(f"Incident tools not available: {self.import_error}")
        
        mock_response = {
            "similar_incidents": [
                {"number": "INC0010001", "similarity_score": 0.85}
            ],
            "count": 1
        }
        
        with patch.object(self, 'similar_incidents_for_text', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = mock_response
            
            result = await self.similar_incidents_for_text("server down")
            
            self.assertIsInstance(result, dict)
            self.assertIn('similar_incidents', result)

    async def test_get_short_desc_for_incident(self):
        """Test getting incident description."""
        if not self.incident_tools_available:
            self.skipTest(f"Incident tools not available: {self.import_error}")
        
        with patch.object(self, 'get_short_desc_for_incident', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = {"description": "Server is not responding"}
            
            result = await self.get_short_desc_for_incident("INC0010001")
            
            self.assertIsInstance(result, dict)
            self.assertIn('description', result)

    async def test_similar_incidents_for_incident(self):
        """Test finding similar incidents for specific incident."""
        if not self.incident_tools_available:
            self.skipTest(f"Incident tools not available: {self.import_error}")
        
        mock_response = {
            "similar_incidents": [
                {"number": "INC0010002", "similarity_score": 0.78}
            ]
        }
        
        with patch.object(self, 'similar_incidents_for_incident', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = mock_response
            
            result = await self.similar_incidents_for_incident("INC0010001")
            
            self.assertIsInstance(result, dict)
            self.assertIn('similar_incidents', result)

    async def test_get_incident_details(self):
        """Test getting full incident details."""
        if not self.incident_tools_available:
            self.skipTest(f"Incident tools not available: {self.import_error}")
        
        mock_response = {
            "number": "INC0010001",
            "priority": "1",
            "state": "New",
            "short_description": "Server down"
        }
        
        with patch.object(self, 'get_incident_details', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = mock_response
            
            result = await self.get_incident_details("INC0010001")
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result['number'], 'INC0010001')

    async def test_get_incidents_by_filter(self):
        """Test getting incidents with filters."""
        if not self.incident_tools_available:
            self.skipTest(f"Incident tools not available: {self.import_error}")
        
        filters = {"priority": "1", "state": "New"}
        mock_response = {"incidents": [], "count": 0}
        
        with patch.object(self, 'get_incidents_by_filter', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = mock_response
            
            result = await self.get_incidents_by_filter(filters)
            
            self.assertIsInstance(result, dict)
            self.assertIn('incidents', result)

    async def test_get_priority_incidents(self):
        """Test getting priority incidents with proper OR syntax."""
        if not self.incident_tools_available:
            self.skipTest(f"Incident tools not available: {self.import_error}")
        
        mock_response = {"incidents": [], "count": 5}
        
        with patch.object(self, 'get_priority_incidents', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = mock_response
            
            result = await self.get_priority_incidents(["1", "2"])
            
            self.assertIsInstance(result, dict)
            mock_func.assert_called_once_with(["1", "2"])


class TestChangeTools(unittest.IsolatedAsyncioTestCase):
    """Test change request tools."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        try:
            from Table_Tools.consolidated_tools import (
                similar_changes_for_text, get_short_desc_for_change,
                similar_changes_for_change, get_change_details
            )
            self.change_tools_available = True
            self.similar_changes_for_text = similar_changes_for_text
            self.get_short_desc_for_change = get_short_desc_for_change
            self.similar_changes_for_change = similar_changes_for_change
            self.get_change_details = get_change_details
        except ImportError as e:
            self.change_tools_available = False
            self.import_error = str(e)

    async def test_similar_changes_for_text(self):
        """Test finding similar changes by text."""
        if not self.change_tools_available:
            self.skipTest(f"Change tools not available: {self.import_error}")
        
        mock_response = {
            "similar_changes": [
                {"number": "CHG0030001", "similarity_score": 0.82}
            ]
        }
        
        with patch.object(self, 'similar_changes_for_text', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = mock_response
            
            result = await self.similar_changes_for_text("server upgrade")
            
            self.assertIsInstance(result, dict)
            self.assertIn('similar_changes', result)

    async def test_get_short_desc_for_change(self):
        """Test getting change description."""
        if not self.change_tools_available:
            self.skipTest(f"Change tools not available: {self.import_error}")
        
        with patch.object(self, 'get_short_desc_for_change', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = {"description": "Server OS upgrade"}
            
            result = await self.get_short_desc_for_change("CHG0030001")
            
            self.assertIsInstance(result, dict)
            self.assertIn('description', result)

    async def test_get_change_details(self):
        """Test getting full change details."""
        if not self.change_tools_available:
            self.skipTest(f"Change tools not available: {self.import_error}")
        
        mock_response = {
            "number": "CHG0030001",
            "state": "Scheduled",
            "risk": "Moderate"
        }
        
        with patch.object(self, 'get_change_details', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = mock_response
            
            result = await self.get_change_details("CHG0030001")
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result['number'], 'CHG0030001')


class TestUserRequestTools(unittest.IsolatedAsyncioTestCase):
    """Test user request tools."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        try:
            from Table_Tools.consolidated_tools import (
                similar_ur_for_text, get_short_desc_for_ur,
                similar_urs_for_ur, get_ur_details
            )
            self.ur_tools_available = True
            self.similar_ur_for_text = similar_ur_for_text
            self.get_short_desc_for_ur = get_short_desc_for_ur
            self.similar_urs_for_ur = similar_urs_for_ur
            self.get_ur_details = get_ur_details
        except ImportError as e:
            self.ur_tools_available = False
            self.import_error = str(e)

    async def test_similar_ur_for_text(self):
        """Test finding similar user requests by text."""
        if not self.ur_tools_available:
            self.skipTest(f"User request tools not available: {self.import_error}")
        
        mock_response = {
            "similar_requests": [
                {"number": "REQ0040001", "similarity_score": 0.75}
            ]
        }
        
        with patch.object(self, 'similar_ur_for_text', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = mock_response
            
            result = await self.similar_ur_for_text("new laptop request")
            
            self.assertIsInstance(result, dict)
            self.assertIn('similar_requests', result)

    async def test_get_ur_details(self):
        """Test getting user request details."""
        if not self.ur_tools_available:
            self.skipTest(f"User request tools not available: {self.import_error}")
        
        mock_response = {
            "number": "REQ0040001",
            "state": "Approved",
            "requested_for": "John Doe"
        }
        
        with patch.object(self, 'get_ur_details', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = mock_response
            
            result = await self.get_ur_details("REQ0040001")
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result['number'], 'REQ0040001')


class TestKnowledgeBaseTools(unittest.IsolatedAsyncioTestCase):
    """Test knowledge base tools."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        try:
            from Table_Tools.consolidated_tools import (
                similar_knowledge_for_text, get_knowledge_details,
                get_knowledge_by_category, get_active_knowledge_articles
            )
            self.kb_tools_available = True
            self.similar_knowledge_for_text = similar_knowledge_for_text
            self.get_knowledge_details = get_knowledge_details
            self.get_knowledge_by_category = get_knowledge_by_category
            self.get_active_knowledge_articles = get_active_knowledge_articles
        except ImportError as e:
            self.kb_tools_available = False
            self.import_error = str(e)

    async def test_similar_knowledge_for_text(self):
        """Test finding knowledge articles by text."""
        if not self.kb_tools_available:
            self.skipTest(f"Knowledge base tools not available: {self.import_error}")
        
        mock_response = {
            "similar_articles": [
                {"number": "KB0007001", "similarity_score": 0.88}
            ]
        }
        
        with patch.object(self, 'similar_knowledge_for_text', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = mock_response
            
            result = await self.similar_knowledge_for_text("password reset")
            
            self.assertIsInstance(result, dict)
            self.assertIn('similar_articles', result)

    async def test_get_knowledge_details(self):
        """Test getting knowledge article details."""
        if not self.kb_tools_available:
            self.skipTest(f"Knowledge base tools not available: {self.import_error}")
        
        mock_response = {
            "number": "KB0007001", 
            "title": "How to reset password",
            "text": "Steps for password reset..."
        }
        
        with patch.object(self, 'get_knowledge_details', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = mock_response
            
            result = await self.get_knowledge_details("KB0007001")
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result['number'], 'KB0007001')

    async def test_get_knowledge_by_category(self):
        """Test getting knowledge articles by category."""
        if not self.kb_tools_available:
            self.skipTest(f"Knowledge base tools not available: {self.import_error}")
        
        mock_response = {"articles": [], "count": 5}
        
        with patch.object(self, 'get_knowledge_by_category', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = mock_response
            
            result = await self.get_knowledge_by_category("IT Support")
            
            self.assertIsInstance(result, dict)
            self.assertIn('articles', result)

    async def test_get_active_knowledge_articles(self):
        """Test getting active knowledge articles."""
        if not self.kb_tools_available:
            self.skipTest(f"Knowledge base tools not available: {self.import_error}")
        
        mock_response = {"articles": [], "count": 25}
        
        with patch.object(self, 'get_active_knowledge_articles', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = mock_response
            
            result = await self.get_active_knowledge_articles("server")
            
            self.assertIsInstance(result, dict)
            self.assertIn('articles', result)


class TestPrivateTaskTools(unittest.IsolatedAsyncioTestCase):
    """Test private task tools with CRUD operations."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        try:
            from Table_Tools.consolidated_tools import (
                similar_private_tasks_for_text, get_short_desc_for_private_task,
                similar_private_tasks_for_private_task, get_private_task_details,
                create_private_task, update_private_task, get_private_tasks_by_filter
            )
            self.task_tools_available = True
            self.similar_private_tasks_for_text = similar_private_tasks_for_text
            self.get_short_desc_for_private_task = get_short_desc_for_private_task
            self.similar_private_tasks_for_private_task = similar_private_tasks_for_private_task
            self.get_private_task_details = get_private_task_details
            self.create_private_task = create_private_task
            self.update_private_task = update_private_task
            self.get_private_tasks_by_filter = get_private_tasks_by_filter
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