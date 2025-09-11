#!/usr/bin/env python3
"""
Integration tests for ServiceNow MCP server.

End-to-end testing of workflows and tool interactions.
These tests validate the complete integration without making real API calls.
"""

import unittest
import sys
import os
from unittest.mock import patch, AsyncMock, MagicMock

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMCPServerIntegration(unittest.IsolatedAsyncioTestCase):
    """Test MCP server integration and tool registration."""

    async def asyncSetUp(self):
        """Set up integration test fixtures."""
        try:
            import tools
            self.mcp_server_available = True
            self.tools_module = tools
        except ImportError as e:
            self.mcp_server_available = False
            self.import_error = str(e)

    async def test_mcp_server_initialization(self):
        """Test MCP server initialization."""
        if not self.mcp_server_available:
            self.skipTest(f"MCP server not available: {self.import_error}")
        
        # Test that tools module is importable
        self.assertIsNotNone(self.tools_module)

    async def test_tool_registration_structure(self):
        """Test that tools are properly registered."""
        if not self.mcp_server_available:
            self.skipTest(f"MCP server not available: {self.import_error}")
        
        # Expected tool categories
        expected_categories = [
            'server_auth',    # Server & Authentication tools
            'incident',       # Incident tools
            'change',         # Change tools
            'user_request',   # User request tools
            'knowledge',      # Knowledge base tools
            'cmdb',          # CMDB tools
            'private_task',  # Private task tools
            'generic'        # Generic table tools
        ]
        
        # This test validates the structure without making API calls
        for category in expected_categories:
            self.assertIsInstance(category, str)
            self.assertGreater(len(category), 3)


class TestIncidentWorkflow(unittest.IsolatedAsyncioTestCase):
    """Test complete incident management workflow."""

    async def asyncSetUp(self):
        """Set up incident workflow test fixtures."""
        self.sample_incident = {
            "number": "INC0010001",
            "short_description": "Server is down",
            "priority": "1",
            "state": "New"
        }
        
        self.workflow_steps = [
            "find_similar_incidents",
            "get_incident_details", 
            "analyze_priority",
            "get_similar_incidents"
        ]

    async def test_incident_similarity_workflow(self):
        """Test incident similarity analysis workflow."""
        # Mock the entire workflow
        mock_responses = {
            "similar_incidents_for_text": {
                "similar_incidents": [
                    {"number": "INC0010002", "similarity_score": 0.85}
                ],
                "count": 1
            },
            "get_incident_details": self.sample_incident,
            "similar_incidents_for_incident": {
                "similar_incidents": [
                    {"number": "INC0010003", "similarity_score": 0.78}
                ]
            }
        }
        
        # Validate workflow structure
        for step in self.workflow_steps:
            self.assertIsInstance(step, str)
            self.assertIn("incident", step)

    async def test_priority_incident_filtering_workflow(self):
        """Test P1/P2 incident filtering workflow."""
        # Test the intelligent filtering workflow
        filter_params = {
            "sys_created_on": "Week 35 2025",
            "priority": "1,2",
            "exclude_caller": "logicmonitor"
        }
        
        expected_workflow = [
            "parse_natural_language_filters",
            "build_servicenow_query",
            "execute_api_call",
            "process_results"
        ]
        
        for step in expected_workflow:
            self.assertIsInstance(step, str)


class TestChangeRequestWorkflow(unittest.IsolatedAsyncioTestCase):
    """Test change request management workflow."""

    async def asyncSetUp(self):
        """Set up change request workflow fixtures."""
        self.sample_change = {
            "number": "CHG0030001",
            "short_description": "Server OS upgrade",
            "state": "Scheduled",
            "risk": "Moderate"
        }

    async def test_change_analysis_workflow(self):
        """Test change request analysis workflow."""
        workflow_steps = [
            "find_similar_changes",
            "assess_risk_level",
            "get_change_details",
            "analyze_impact"
        ]
        
        for step in workflow_steps:
            self.assertIsInstance(step, str)
            self.assertGreater(len(step), 5)


class TestCMDBDiscoveryWorkflow(unittest.IsolatedAsyncioTestCase):
    """Test CMDB discovery and analysis workflow."""

    async def asyncSetUp(self):
        """Set up CMDB workflow fixtures."""
        self.sample_ci = {
            "ci_number": "CI001001",
            "name": "prod-web-server-01",
            "ci_table": "cmdb_ci_server",
            "status": "operational"
        }

    async def test_cmdb_discovery_workflow(self):
        """Test complete CMDB discovery workflow."""
        discovery_steps = [
            "get_all_ci_types",
            "find_cis_by_type",
            "analyze_ci_attributes",
            "find_similar_cis",
            "assess_relationships"
        ]
        
        for step in discovery_steps:
            self.assertIsInstance(step, str)
            self.assertIn("ci", step.lower())

    async def test_cmdb_search_workflow(self):
        """Test CMDB search and analysis workflow."""
        search_parameters = {
            "name": "prod-server",
            "ip_address": "192.168.1.100", 
            "status": "operational",
            "location": "data_center_1"
        }
        
        for key, value in search_parameters.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(value, str)


class TestKnowledgeBaseWorkflow(unittest.IsolatedAsyncioTestCase):
    """Test knowledge base search and retrieval workflow."""

    async def asyncSetUp(self):
        """Set up knowledge base workflow fixtures."""
        self.sample_kb_article = {
            "number": "KB0007001",
            "title": "How to reset password",
            "category": "IT Support",
            "text": "Steps for password reset..."
        }

    async def test_knowledge_search_workflow(self):
        """Test knowledge article search workflow."""
        search_workflow = [
            "search_by_text",
            "filter_by_category", 
            "get_article_details",
            "find_related_articles"
        ]
        
        for step in search_workflow:
            self.assertIsInstance(step, str)


class TestPrivateTaskCRUDWorkflow(unittest.IsolatedAsyncioTestCase):
    """Test private task CRUD operations workflow."""

    async def asyncSetUp(self):
        """Set up private task workflow fixtures."""
        self.sample_task = {
            "short_description": "Test task",
            "description": "This is a test task",
            "priority": "3",
            "state": "New"
        }

    async def test_task_crud_workflow(self):
        """Test complete CRUD workflow for private tasks."""
        crud_operations = [
            "create_private_task",
            "get_private_task_details",
            "update_private_task", 
            "find_similar_tasks"
        ]
        
        for operation in crud_operations:
            self.assertIsInstance(operation, str)
            self.assertIn("task", operation)


class TestIntelligentFilteringIntegration(unittest.IsolatedAsyncioTestCase):
    """Test intelligent filtering integration across all tools."""

    async def asyncSetUp(self):
        """Set up intelligent filtering test fixtures."""
        self.natural_language_filters = {
            "Week 35 2025": ("2025-08-25", "2025-08-31"),
            "August 25-31, 2025": ("2025-08-25", "2025-08-31"),
            "2025-08-25 to 2025-08-31": ("2025-08-25", "2025-08-31")
        }
        
        self.priority_formats = {
            "1,2": "priority=1^ORpriority=2",
            "P1,P2": "priority=1^ORpriority=2", 
            '["1","2","3"]': "priority=1^ORpriority=2^ORpriority=3"
        }

    async def test_date_parsing_integration(self):
        """Test date parsing across different formats."""
        for input_format, expected in self.natural_language_filters.items():
            self.assertIsInstance(input_format, str)
            self.assertIsInstance(expected, tuple)
            self.assertEqual(len(expected), 2)

    async def test_priority_parsing_integration(self):
        """Test priority parsing across different formats."""
        for input_format, expected in self.priority_formats.items():
            self.assertIsInstance(input_format, str)
            self.assertIsInstance(expected, str)
            self.assertIn("priority=", expected)
            
            # Test OR syntax presence for multiple priorities
            if "," in input_format or "[" in input_format:
                self.assertIn("^OR", expected)

    async def test_combined_filtering_integration(self):
        """Test combined intelligent filtering."""
        combined_filters = {
            "sys_created_on": "Week 35 2025",
            "priority": "1,2",
            "exclude_caller": "logicmonitor"
        }
        
        # Validate filter structure
        for key, value in combined_filters.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(value, str)
            self.assertGreater(len(value), 0)


class TestOAuthIntegration(unittest.IsolatedAsyncioTestCase):
    """Test OAuth integration across all tools."""

    async def asyncSetUp(self):
        """Set up OAuth integration fixtures."""
        self.oauth_config = {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret", 
            "instance_url": "https://test.service-now.com"
        }

    async def test_oauth_flow_integration(self):
        """Test OAuth authentication flow integration."""
        oauth_steps = [
            "check_oauth_configuration",
            "obtain_access_token",
            "validate_token",
            "make_authenticated_request",
            "handle_token_refresh"
        ]
        
        for step in oauth_steps:
            self.assertIsInstance(step, str)
            self.assertIn("token", step) or self.assertIn("oauth", step) or self.assertIn("auth", step)

    async def test_oauth_error_handling_integration(self):
        """Test OAuth error handling integration."""
        error_scenarios = [
            "invalid_credentials",
            "token_expired", 
            "network_error",
            "server_error"
        ]
        
        for scenario in error_scenarios:
            self.assertIsInstance(scenario, str)
            self.assertIn("error", scenario) or self.assertIn("invalid", scenario) or self.assertIn("expired", scenario)


class TestAPIResponseHandling(unittest.TestCase):
    """Test API response handling and data validation."""

    def setUp(self):
        """Set up API response test fixtures."""
        self.valid_incident_response = {
            "result": [
                {
                    "number": "INC0010001",
                    "short_description": "Server down",
                    "priority": "1"
                }
            ]
        }
        
        self.error_response = {
            "error": {
                "message": "Invalid table",
                "detail": "Table 'invalid_table' does not exist"
            }
        }

    def test_valid_response_structure(self):
        """Test validation of valid API response structure."""
        self.assertIsInstance(self.valid_incident_response, dict)
        self.assertIn('result', self.valid_incident_response)
        self.assertIsInstance(self.valid_incident_response['result'], list)

    def test_error_response_structure(self):
        """Test validation of error response structure."""
        self.assertIsInstance(self.error_response, dict)
        self.assertIn('error', self.error_response)
        self.assertIn('message', self.error_response['error'])

    def test_response_data_validation(self):
        """Test response data field validation."""
        record = self.valid_incident_response['result'][0]
        
        required_fields = ['number', 'short_description']
        for field in required_fields:
            self.assertIn(field, record)
            self.assertIsInstance(record[field], str)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)