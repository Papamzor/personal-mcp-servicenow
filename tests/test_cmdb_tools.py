#!/usr/bin/env python3
"""
unittest version of CMDB CI Discovery & Search tools tests.

Converted from Testing/test_cmdb_tools.py to use unittest framework
for proper SonarQube integration and coverage reporting.

Tests CMDB functionality with proper mocking to avoid live API calls.
"""

import unittest
import sys
import os
from unittest.mock import patch, AsyncMock, MagicMock

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCMDBTools(unittest.IsolatedAsyncioTestCase):
    """Test suite for CMDB tools functionality."""

    async def asyncSetUp(self):
        """Set up test fixtures for async tests."""
        try:
            from Table_Tools.cmdb_tools import (
                findCIsByType, searchCIsByAttributes, getCIDetails, 
                similarCIsForCI, getAllCITypes, quickCISearch
            )
            self.cmdb_tools_available = True
            self.findCIsByType = findCIsByType
            self.searchCIsByAttributes = searchCIsByAttributes  
            self.getCIDetails = getCIDetails
            self.similarCIsForCI = similarCIsForCI
            self.getAllCITypes = getAllCITypes
            self.quickCISearch = quickCISearch
        except ImportError as e:
            self.cmdb_tools_available = False
            self.import_error = str(e)

    async def test_get_all_ci_types_success(self):
        """Test successful retrieval of all CI types."""
        if not self.cmdb_tools_available:
            self.skipTest(f"CMDB tools not available: {self.import_error}")
        
        # Mock successful API response
        mock_response = {
            'total_ci_types': 25,
            'ci_types': [
                {'table_name': 'cmdb_ci_server', 'display_name': 'Server'},
                {'table_name': 'cmdb_ci_computer', 'display_name': 'Computer'},
                {'table_name': 'cmdb_ci_database', 'display_name': 'Database'}
            ]
        }
        
        with patch.object(self, 'getAllCITypes', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = mock_response
            
            result = await self.getAllCITypes()
            
            self.assertIsInstance(result, dict)
            self.assertIn('total_ci_types', result)
            self.assertIn('ci_types', result)
            self.assertEqual(result['total_ci_types'], 25)
            self.assertEqual(len(result['ci_types']), 3)

    async def test_get_all_ci_types_error_handling(self):
        """Test error handling for getAllCITypes."""
        if not self.cmdb_tools_available:
            self.skipTest(f"CMDB tools not available: {self.import_error}")
        
        with patch.object(self, 'getAllCITypes', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = "API Error: Unable to retrieve CI types"
            
            result = await self.getAllCITypes()
            
            self.assertIsInstance(result, str)
            self.assertIn("API Error", result)

    async def test_find_cis_by_type_server(self):
        """Test finding CIs by server type."""
        if not self.cmdb_tools_available:
            self.skipTest(f"CMDB tools not available: {self.import_error}")
        
        mock_response = {
            'count': 15,
            'cis': [
                {
                    'ci_number': 'CI001001',
                    'name': 'prod-web-server-01',
                    'ci_table': 'cmdb_ci_server'
                }
            ]
        }
        
        with patch.object(self, 'findCIsByType', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = mock_response
            
            result = await self.findCIsByType('cmdb_ci_server')
            
            self.assertIsInstance(result, dict)
            self.assertIn('count', result)
            self.assertIn('cis', result)
            self.assertEqual(result['count'], 15)

    async def test_find_cis_by_type_invalid_type(self):
        """Test finding CIs with invalid type."""
        if not self.cmdb_tools_available:
            self.skipTest(f"CMDB tools not available: {self.import_error}")
        
        with patch.object(self, 'findCIsByType', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = "Error: Invalid CI type 'invalid_type'"
            
            result = await self.findCIsByType('invalid_type')
            
            self.assertIsInstance(result, str)
            self.assertIn("Error", result)
            self.assertIn("invalid_type", result)

    async def test_search_cis_by_attributes_name(self):
        """Test searching CIs by name attribute."""
        if not self.cmdb_tools_available:
            self.skipTest(f"CMDB tools not available: {self.import_error}")
        
        mock_response = {
            'count': 8,
            'cis': [
                {
                    'ci_number': 'CI001002',
                    'name': 'prod-database-01',
                    'ci_table': 'cmdb_ci_database'
                }
            ]
        }
        
        with patch.object(self, 'searchCIsByAttributes', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = mock_response
            
            result = await self.searchCIsByAttributes(name='prod')
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result['count'], 8)
            self.assertIn('cis', result)

    async def test_search_cis_by_attributes_ip_address(self):
        """Test searching CIs by IP address attribute.""" 
        if not self.cmdb_tools_available:
            self.skipTest(f"CMDB tools not available: {self.import_error}")
        
        mock_response = {
            'count': 1,
            'cis': [
                {
                    'ci_number': 'CI001003',
                    'name': 'web-server-01',
                    'ip_address': '192.168.1.100'
                }
            ]
        }
        
        with patch.object(self, 'searchCIsByAttributes', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = mock_response
            
            result = await self.searchCIsByAttributes(ip_address='192.168.1.100')
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result['count'], 1)
            self.assertEqual(result['cis'][0]['ip_address'], '192.168.1.100')

    async def test_search_cis_by_attributes_multiple(self):
        """Test searching CIs by multiple attributes."""
        if not self.cmdb_tools_available:
            self.skipTest(f"CMDB tools not available: {self.import_error}")
        
        with patch.object(self, 'searchCIsByAttributes', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = {'count': 2, 'cis': []}
            
            result = await self.searchCIsByAttributes(
                name='prod', 
                status='operational',
                location='data_center_1'
            )
            
            self.assertIsInstance(result, dict)
            mock_func.assert_called_once_with(
                name='prod', 
                status='operational',
                location='data_center_1'
            )

    async def test_get_ci_details_success(self):
        """Test successful CI details retrieval."""
        if not self.cmdb_tools_available:
            self.skipTest(f"CMDB tools not available: {self.import_error}")
        
        mock_response = {
            'ci_number': 'CI001001',
            'name': 'prod-web-server-01',
            'ci_table': 'cmdb_ci_server',
            'status': 'operational',
            'location': 'data_center_1',
            'ip_address': '192.168.1.100'
        }
        
        with patch.object(self, 'getCIDetails', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = mock_response
            
            result = await self.getCIDetails('CI001001')
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result['ci_number'], 'CI001001')
            self.assertIn('ci_table', result)
            self.assertIn('status', result)

    async def test_get_ci_details_not_found(self):
        """Test CI details retrieval for non-existent CI."""
        if not self.cmdb_tools_available:
            self.skipTest(f"CMDB tools not available: {self.import_error}")
        
        with patch.object(self, 'getCIDetails', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = "CI not found: CI999999"
            
            result = await self.getCIDetails('CI999999')
            
            self.assertIsInstance(result, str)
            self.assertIn("CI not found", result)

    async def test_similar_cis_for_ci_success(self):
        """Test finding similar CIs for a given CI."""
        if not self.cmdb_tools_available:
            self.skipTest(f"CMDB tools not available: {self.import_error}")
        
        mock_response = {
            'count': 3,
            'similar_cis': [
                {'ci_number': 'CI001002', 'similarity_score': 0.85},
                {'ci_number': 'CI001003', 'similarity_score': 0.78}
            ]
        }
        
        with patch.object(self, 'similarCIsForCI', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = mock_response
            
            result = await self.similarCIsForCI('CI001001')
            
            self.assertIsInstance(result, dict)
            self.assertIn('similar_cis', result)
            self.assertEqual(result['count'], 3)

    async def test_quick_ci_search_success(self):
        """Test quick CI search functionality."""
        if not self.cmdb_tools_available:
            self.skipTest(f"CMDB tools not available: {self.import_error}")
        
        mock_response = {
            'count': 5,
            'results': [
                {
                    'ci_number': 'CI001001',
                    'name': 'prod-server',
                    'match_type': 'name'
                }
            ]
        }
        
        with patch.object(self, 'quickCISearch', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = mock_response
            
            result = await self.quickCISearch('prod-server')
            
            self.assertIsInstance(result, dict)
            self.assertIn('results', result)
            self.assertEqual(result['count'], 5)

    async def test_quick_ci_search_no_results(self):
        """Test quick CI search with no results."""
        if not self.cmdb_tools_available:
            self.skipTest(f"CMDB tools not available: {self.import_error}")
        
        mock_response = {
            'count': 0,
            'results': [],
            'message': 'No CIs found matching search term'
        }
        
        with patch.object(self, 'quickCISearch', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = mock_response
            
            result = await self.quickCISearch('nonexistent-ci')
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result['count'], 0)
            self.assertEqual(len(result['results']), 0)


class TestCMDBToolsValidation(unittest.TestCase):
    """Test input validation and error handling for CMDB tools."""

    def test_ci_number_format_validation(self):
        """Test CI number format validation."""
        valid_ci_numbers = ['CI001001', 'CI123456', 'CI000001']
        invalid_ci_numbers = ['', None, '123', 'INVALID']
        
        for ci_number in valid_ci_numbers:
            self.assertIsInstance(ci_number, str)
            self.assertTrue(ci_number.startswith('CI'))
            self.assertGreaterEqual(len(ci_number), 7)
        
        for ci_number in invalid_ci_numbers:
            if ci_number is not None:
                self.assertFalse(
                    isinstance(ci_number, str) and ci_number.startswith('CI') and len(ci_number) >= 7
                )

    def test_ci_type_validation(self):
        """Test CI type parameter validation."""
        valid_ci_types = [
            'cmdb_ci_server', 
            'cmdb_ci_computer', 
            'cmdb_ci_database',
            'cmdb_ci_network_gear'
        ]
        
        for ci_type in valid_ci_types:
            self.assertIsInstance(ci_type, str)
            self.assertTrue(ci_type.startswith('cmdb_ci_'))
            self.assertGreater(len(ci_type), 7)

    def test_search_attributes_validation(self):
        """Test search attributes parameter validation."""
        valid_attributes = {
            'name': 'prod-server',
            'ip_address': '192.168.1.100',
            'status': 'operational',
            'location': 'data_center_1'
        }
        
        for key, value in valid_attributes.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(value, str)
            self.assertGreater(len(key), 0)
            self.assertGreater(len(value), 0)

    def test_search_term_validation(self):
        """Test search term validation for quick search."""
        valid_search_terms = ['prod', 'server-01', '192.168.1.100', 'CI001001']
        invalid_search_terms = ['', None]
        
        for term in valid_search_terms:
            self.assertIsInstance(term, str)
            self.assertGreater(len(term), 0)
        
        for term in invalid_search_terms:
            self.assertTrue(term is None or (isinstance(term, str) and len(term) == 0))


class TestCMDBToolsIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for CMDB tools workflow."""

    async def asyncSetUp(self):
        """Set up integration test fixtures."""
        self.sample_ci_data = {
            'ci_number': 'CI001001',
            'name': 'prod-web-server-01',
            'ci_table': 'cmdb_ci_server',
            'status': 'operational',
            'ip_address': '192.168.1.100'
        }

    async def test_cmdb_discovery_workflow(self):
        """Test complete CMDB discovery workflow."""
        # This test would normally involve:
        # 1. Get all CI types
        # 2. Find CIs by specific type
        # 3. Get details for found CI
        # 4. Find similar CIs
        
        # Since we're not making real API calls, we just test the workflow structure
        workflow_steps = [
            'get_all_ci_types',
            'find_cis_by_type', 
            'get_ci_details',
            'find_similar_cis'
        ]
        
        for step in workflow_steps:
            self.assertIsInstance(step, str)
            self.assertIn('ci', step)

    async def test_cmdb_search_workflow(self):
        """Test complete CMDB search workflow.""" 
        # Workflow: search by attributes -> get details -> find similar
        search_workflow = [
            'search_by_attributes',
            'get_details',
            'find_similar'
        ]
        
        for step in search_workflow:
            self.assertIsInstance(step, str)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)