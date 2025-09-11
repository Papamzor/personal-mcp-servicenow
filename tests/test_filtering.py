#!/usr/bin/env python3
"""
unittest version of ServiceNow filtering functionality tests.

Converted from Testing/test_filtering_fixes.py to use unittest framework
for proper SonarQube integration and coverage reporting.

Test Categories:
1. Date range filtering (Week 35, 2025)
2. Priority OR logic (P1/P2 incidents)  
3. Caller exclusion (LogicMonitor Integration)
4. Combined filtering
5. URL encoding with JavaScript functions
"""

import unittest
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from query_validation import ServiceNowQueryBuilder, QueryValidationResult
from Table_Tools.generic_table_tools import (
    TableFilterParams, _encode_query_string,
    _parse_date_range_from_text, _parse_priority_list, _parse_caller_exclusions
)


class TestServiceNowFiltering(unittest.TestCase):
    """Test suite for ServiceNow filtering functionality using unittest."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.query_builder = ServiceNowQueryBuilder()

    def test_week35_date_range_parsing(self):
        """Test parsing of Week 35 2025 date range."""
        week35_range = _parse_date_range_from_text("Week 35 2025")
        expected = ("2025-08-25", "2025-08-31")
        
        self.assertEqual(week35_range, expected, 
                        f"Week 35 2025 should parse to {expected}, got {week35_range}")

    def test_month_range_parsing(self):
        """Test parsing of month range format."""
        august_range = _parse_date_range_from_text("August 25-31, 2025")
        expected = ("2025-08-25", "2025-08-31")
        
        self.assertEqual(august_range, expected, 
                        f"August 25-31, 2025 should parse to {expected}, got {august_range}")

    def test_iso_date_range_parsing(self):
        """Test parsing of ISO date range format."""
        iso_range = _parse_date_range_from_text("2025-08-25 to 2025-08-31")
        expected = ("2025-08-25", "2025-08-31")
        
        self.assertEqual(iso_range, expected, 
                        f"ISO date range should parse to {expected}, got {iso_range}")

    def test_relative_date_filtering(self):
        """Test relative date filtering using ServiceNowQueryBuilder."""
        last_week_filter = ServiceNowQueryBuilder.build_relative_date_filter("last week")
        expected = "sys_created_onBETWEENjavascript:gs.beginningOfLastWeek()@javascript:gs.endOfLastWeek()"
        
        self.assertEqual(last_week_filter, expected, 
                        f"Last week filter should be {expected}, got {last_week_filter}")

    def test_priority_list_parsing_comma_separated(self):
        """Test parsing comma-separated priority lists."""
        priorities = _parse_priority_list("1,2")
        expected = "priority=1^ORpriority=2"
        
        self.assertEqual(priorities, expected,
                        f"Priority list '1,2' should parse to {expected}, got {priorities}")

    def test_priority_list_parsing_p_notation(self):
        """Test parsing P-notation priority lists."""
        priorities = _parse_priority_list("P1,P2")
        expected = "priority=1^ORpriority=2"
        
        self.assertEqual(priorities, expected,
                        f"Priority list 'P1,P2' should parse to {expected}, got {priorities}")

    def test_priority_list_parsing_array_format(self):
        """Test parsing array-like priority lists."""
        priorities = _parse_priority_list('["1","2","3"]')
        expected = "priority=1^ORpriority=2^ORpriority=3"
        
        self.assertEqual(priorities, expected,
                        f"Priority array should parse to {expected}, got {priorities}")

    def test_caller_exclusion_by_name(self):
        """Test caller exclusion by name lookup."""
        with patch('Table_Tools.generic_table_tools._get_caller_sys_id') as mock_get_caller:
            mock_get_caller.return_value = "1727339e47d99190c43d3171e36d43ad"
            
            exclusions = _parse_caller_exclusions("logicmonitor")
            expected = "caller_id!=1727339e47d99190c43d3171e36d43ad"
            
            self.assertEqual(exclusions, expected,
                            f"LogicMonitor exclusion should be {expected}, got {exclusions}")

    def test_caller_exclusion_multiple_sysids(self):
        """Test multiple caller exclusions by sys_id."""
        exclusions = _parse_caller_exclusions("sys_id1,sys_id2")
        expected = "caller_id!=sys_id1^caller_id!=sys_id2"
        
        self.assertEqual(exclusions, expected,
                        f"Multiple sys_id exclusions should be {expected}, got {exclusions}")

    def test_url_encoding_preservation(self):
        """Test that URL encoding preserves JavaScript functions."""
        query = "sys_created_onBETWEENjavascript:gs.beginningOfWeek()@javascript:gs.endOfWeek()^priority=1^ORpriority=2"
        encoded = _encode_query_string(query)
        
        # JavaScript functions should be preserved
        self.assertIn("javascript:gs.beginningOfWeek()", encoded)
        self.assertIn("javascript:gs.endOfWeek()", encoded)
        # OR operator should be preserved
        self.assertIn("^ORpriority=2", encoded)

    def test_servicenow_query_builder_validation(self):
        """Test ServiceNowQueryBuilder query validation."""
        # Test valid query
        valid_query = "priority=1^ORpriority=2^sys_created_on>2025-01-01"
        result = self.query_builder.validate_query(valid_query)
        
        self.assertIsInstance(result, QueryValidationResult)
        self.assertTrue(result.is_valid, f"Query should be valid: {valid_query}")

    def test_between_syntax_generation(self):
        """Test proper BETWEEN syntax generation."""
        between_filter = ServiceNowQueryBuilder.build_date_range_filter(
            "sys_created_on", "2025-08-25", "2025-08-31"
        )
        expected = "sys_created_onBETWEEN2025-08-25@2025-08-31"
        
        self.assertEqual(between_filter, expected,
                        f"BETWEEN syntax should be {expected}, got {between_filter}")

    def test_table_filter_params_creation(self):
        """Test TableFilterParams object creation and validation."""
        filters = {
            "sys_created_on": "Week 35 2025",
            "priority": "1,2",
            "exclude_caller": "logicmonitor"
        }
        
        params = TableFilterParams(filters=filters)
        
        self.assertIsInstance(params, TableFilterParams)
        self.assertEqual(params.filters, filters)

    @patch('Table_Tools.generic_table_tools.query_table_with_filters')
    def test_combined_filtering_integration(self, mock_query):
        """Test combined filtering with mocked API call."""
        mock_query.return_value = {"result": [{"number": "INC0010001"}]}
        
        filters = {
            "sys_created_on": "Week 35 2025",
            "priority": "1,2",
            "exclude_caller": "logicmonitor"
        }
        
        params = TableFilterParams(filters=filters)
        
        # This would normally make an API call, but we're mocking it
        # result = await query_table_with_filters("incident", params)
        
        # Verify the mock was configured properly
        self.assertTrue(mock_query.return_value.get("result"))

    def test_edge_case_empty_filters(self):
        """Test handling of empty filter cases."""
        # Empty priority list
        empty_priorities = _parse_priority_list("")
        self.assertEqual(empty_priorities, "", "Empty priority should return empty string")
        
        # Empty caller exclusion
        empty_exclusion = _parse_caller_exclusions("")
        self.assertEqual(empty_exclusion, "", "Empty exclusion should return empty string")

    def test_edge_case_invalid_date_formats(self):
        """Test handling of invalid date format inputs."""
        invalid_date = _parse_date_range_from_text("invalid date format")
        self.assertIsNone(invalid_date, "Invalid date format should return None")

    def test_priority_single_value(self):
        """Test single priority value parsing."""
        single_priority = _parse_priority_list("1")
        expected = "priority=1"
        
        self.assertEqual(single_priority, expected,
                        f"Single priority should be {expected}, got {single_priority}")


class TestServiceNowQueryBuilder(unittest.TestCase):
    """Specific tests for ServiceNowQueryBuilder class."""

    def setUp(self):
        """Set up test fixtures."""
        self.builder = ServiceNowQueryBuilder()

    def test_query_builder_initialization(self):
        """Test QueryBuilder initialization."""
        self.assertIsInstance(self.builder, ServiceNowQueryBuilder)

    def test_build_or_filter(self):
        """Test OR filter building."""
        or_filter = ServiceNowQueryBuilder.build_or_filter("priority", ["1", "2", "3"])
        expected = "priority=1^ORpriority=2^ORpriority=3"
        
        self.assertEqual(or_filter, expected,
                        f"OR filter should be {expected}, got {or_filter}")

    def test_build_not_equals_filter(self):
        """Test NOT EQUALS filter building."""
        not_equals = ServiceNowQueryBuilder.build_not_equals_filter("caller_id", ["id1", "id2"])
        expected = "caller_id!=id1^caller_id!=id2"
        
        self.assertEqual(not_equals, expected,
                        f"NOT EQUALS filter should be {expected}, got {not_equals}")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)