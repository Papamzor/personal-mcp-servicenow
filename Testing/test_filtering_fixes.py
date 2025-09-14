#!/usr/bin/env python3
"""
Comprehensive test script for ServiceNow filtering fixes.

This script tests all the filtering improvements made to address the issues
identified in the P1/P2 incident report generation problems.

Test Categories:
1. Date range filtering (Week 35, 2025)
2. Priority OR logic (P1/P2 incidents)  
3. Caller exclusion (LogicMonitor Integration)
4. Combined filtering
5. URL encoding with JavaScript functions
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from query_validation import ServiceNowQueryBuilder, QueryValidationResult
from Table_Tools.consolidated_tools import get_priority_incidents
from Table_Tools.generic_table_tools import (
    TableFilterParams, query_table_with_filters, _encode_query_string,
    _parse_date_range_from_text, _parse_priority_list, _parse_caller_exclusions
)


class FilteringTestSuite:
    """Test suite for ServiceNow filtering functionality."""
    
    def __init__(self):
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test results."""
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {test_name}")
        if message:
            print(f"    {message}")
        
        if passed:
            self.test_results["passed"] += 1
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {message}")
    
    def test_date_range_filtering(self):
        """Test generic date range parsing and filtering."""
        print("\n=== Testing Generic Date Range Parsing ===")
        
        # Test 1: Week 35 2025 parsing
        week35_range = _parse_date_range_from_text("Week 35 2025")
        expected_week35 = ("2025-08-25", "2025-08-31")
        
        self.log_test(
            "Week 35 2025 parsing",
            week35_range == expected_week35,
            f"Got: {week35_range}, Expected: {expected_week35}"
        )
        
        # Test 2: Month range parsing
        august_range = _parse_date_range_from_text("August 25-31, 2025")
        expected_august = ("2025-08-25", "2025-08-31")
        
        self.log_test(
            "August 25-31, 2025 parsing",
            august_range == expected_august,
            f"Got: {august_range}"
        )
        
        # Test 3: ISO date range parsing
        iso_range = _parse_date_range_from_text("2025-08-25 to 2025-08-31")
        expected_iso = ("2025-08-25", "2025-08-31")
        
        self.log_test(
            "ISO date range parsing",
            iso_range == expected_iso,
            f"Got: {iso_range}"
        )
        
        # Test 4: Relative date filtering (using existing builder)
        last_week_filter = ServiceNowQueryBuilder.build_relative_date_filter("last week")
        expected_last_week = "sys_created_onBETWEENjavascript:gs.beginningOfLastWeek()@javascript:gs.endOfLastWeek()"
        
        self.log_test(
            "Last week relative date filter",
            last_week_filter == expected_last_week,
            f"Got: {last_week_filter}"
        )
    
    def test_priority_or_logic(self):
        """Test generic priority parsing and OR logic."""
        print("\n=== Testing Generic Priority Parsing ===")
        
        # Test 1: Comma-separated priorities
        comma_priorities = _parse_priority_list("1,2")
        expected_comma = "priority=1^ORpriority=2"
        
        self.log_test(
            "Comma-separated priorities (1,2)",
            comma_priorities == expected_comma,
            f"Got: {comma_priorities}"
        )
        
        # Test 2: P1/P2 notation
        p_notation = _parse_priority_list("P1,P2")
        expected_p = "priority=1^ORpriority=2"
        
        self.log_test(
            "P1/P2 priority notation",
            p_notation == expected_p,
            f"Got: {p_notation}"
        )
        
        # Test 3: List-like string format
        list_format = _parse_priority_list('["1", "2", "3"]')
        expected_list = "priority=1^ORpriority=2^ORpriority=3"
        
        self.log_test(
            "List-like string format",
            list_format == expected_list,
            f"Got: {list_format}"
        )
        
        # Test 4: Single priority (no change)
        single_priority = _parse_priority_list("1")
        
        self.log_test(
            "Single priority (no change)",
            single_priority == "1",
            f"Got: {single_priority}"
        )
        
        # Test 5: ServiceNow builder (existing functionality)
        builder_priorities = ServiceNowQueryBuilder.build_priority_or_filter(["1", "2"])
        expected_builder = "priority=1^ORpriority=2"
        
        self.log_test(
            "ServiceNow builder OR logic",
            builder_priorities == expected_builder,
            f"Got: {builder_priorities}"
        )
    
    def test_caller_exclusion(self):
        """Test generic caller exclusion parsing."""
        print("\n=== Testing Generic Caller Exclusion Parsing ===")
        
        # Test 1: LogicMonitor by name
        logicmonitor_exclusion = _parse_caller_exclusions("logicmonitor")
        expected_logicmonitor = "caller_id!=1727339e47d99190c43d3171e36d43ad"
        
        self.log_test(
            "LogicMonitor exclusion by name",
            logicmonitor_exclusion == expected_logicmonitor,
            f"Got: {logicmonitor_exclusion}"
        )
        
        # Test 2: Single sys_id exclusion
        single_exclusion = _parse_caller_exclusions("abc123def456")
        expected_single = "caller_id!=abc123def456"
        
        self.log_test(
            "Single sys_id exclusion",
            single_exclusion == expected_single,
            f"Got: {single_exclusion}"
        )
        
        # Test 3: Multiple caller exclusions
        multiple_exclusions = _parse_caller_exclusions("id1,id2,id3")
        expected_multiple = "caller_id!=id1^caller_id!=id2^caller_id!=id3"
        
        self.log_test(
            "Multiple caller exclusions",
            multiple_exclusions == expected_multiple,
            f"Got: {multiple_exclusions}"
        )
        
        # Test 4: ServiceNow builder (existing functionality)
        builder_exclusion = ServiceNowQueryBuilder.build_exclusion_filter(
            "caller_id", ["1727339e47d99190c43d3171e36d43ad"]
        )
        expected_builder = "caller_id!=1727339e47d99190c43d3171e36d43ad"
        
        self.log_test(
            "ServiceNow builder exclusion",
            builder_exclusion == expected_builder,
            f"Got: {builder_exclusion}"
        )
    
    def test_complete_filter_building(self):
        """Test complete filter building with multiple conditions."""
        print("\n=== Testing Complete Filter Building ===")
        
        # Test 1: Week 35 P1/P2 incidents excluding LogicMonitor
        complete_filter = ServiceNowQueryBuilder.build_complete_filter(
            priorities=["1", "2"],
            date_range=("2025-08-25", "2025-08-31"),
            exclude_callers=["1727339e47d99190c43d3171e36d43ad"]
        )
        
        # Verify components are present
        has_date_filter = "sys_created_onBETWEENjavascript:gs.dateGenerate" in complete_filter
        has_priority_filter = "priority=1^ORpriority=2" in complete_filter
        has_exclusion_filter = "caller_id!=1727339e47d99190c43d3171e36d43ad" in complete_filter
        
        all_components_present = has_date_filter and has_priority_filter and has_exclusion_filter
        
        self.log_test(
            "Complete Week 35 P1/P2 filter with LogicMonitor exclusion",
            all_components_present,
            f"Filter: {complete_filter}"
        )
        
        # Test 2: Relative date with priorities
        relative_filter = ServiceNowQueryBuilder.build_complete_filter(
            priorities=["1", "2"],
            date_period="last week"
        )
        
        has_relative_date = "javascript:gs.beginningOfLastWeek" in relative_filter
        has_priorities = "priority=1^ORpriority=2" in relative_filter
        
        self.log_test(
            "Last week P1/P2 filter",
            has_relative_date and has_priorities,
            f"Filter: {relative_filter}"
        )
    
    def test_url_encoding(self):
        """Test URL encoding preserves JavaScript functions."""
        print("\n=== Testing URL Encoding ===")
        
        # Test 1: JavaScript date functions preserved
        query_with_js = "sys_created_onBETWEENjavascript:gs.dateGenerate('2025-08-25','00:00:00')@javascript:gs.dateGenerate('2025-08-31','23:59:59')"
        encoded_query = _encode_query_string(query_with_js)
        
        # Check that JavaScript functions are preserved
        js_preserved = "javascript:" in encoded_query and "@javascript:" in encoded_query
        
        self.log_test(
            "JavaScript functions preserved in URL encoding",
            js_preserved,
            f"Encoded: {encoded_query}"
        )
        
        # Test 2: OR operators preserved
        query_with_or = "priority=1^ORpriority=2^caller_id!=test123"
        encoded_or = _encode_query_string(query_with_or)
        
        or_preserved = "^OR" in encoded_or and "!=" in encoded_or
        
        self.log_test(
            "OR operators and NOT EQUALS preserved",
            or_preserved,
            f"Encoded: {encoded_or}"
        )
    
    async def test_live_api_calls(self):
        """Test actual API calls using generic filtering (requires valid ServiceNow connection)."""
        print("\n=== Testing Live Generic API Calls (Optional) ===")
        
        try:
            # Test 1: Generic Week 35 P1/P2 incidents using TableFilterParams
            print("Testing generic filtering for Week 35 P1/P2 incidents...")
            
            # This is a dry run - we'll catch connection errors gracefully
            try:
                # Use generic filtering with parsed values
                filters = {
                    "sys_created_on": "Week 35 2025",
                    "priority": "1,2", 
                    "exclude_caller": "logicmonitor"
                }
                
                table_params = TableFilterParams(filters=filters)
                result = await query_table_with_filters("incident", table_params)
                
                if isinstance(result, dict) and "result" in result:
                    count = len(result["result"])
                    self.log_test(
                        "Generic Week 35 P1/P2 filtering",
                        True,
                        f"Retrieved {count} incidents using generic filters"
                    )
                else:
                    self.log_test(
                        "Generic Week 35 P1/P2 filtering",
                        False,
                        f"Unexpected result format: {type(result)}"
                    )
            
            except Exception as e:
                self.log_test(
                    "Generic Week 35 P1/P2 filtering",
                    False,
                    f"Connection error (expected in test): {str(e)}"
                )
            
            # Test 2: Alternative date format
            try:
                print("Testing alternative date format parsing...")
                filters_alt = {
                    "sys_created_on": "August 25-31, 2025",
                    "priority": "P1,P2"
                }
                
                table_params_alt = TableFilterParams(filters=filters_alt)
                result_alt = await query_table_with_filters("incident", table_params_alt)
                
                if isinstance(result_alt, dict) and "result" in result_alt:
                    count_alt = len(result_alt["result"])
                    self.log_test(
                        "Alternative date format parsing",
                        True,
                        f"Retrieved {count_alt} incidents using 'August 25-31, 2025' and 'P1,P2'"
                    )
                else:
                    self.log_test(
                        "Alternative date format parsing",
                        False,
                        f"Unexpected result format: {type(result_alt)}"
                    )
            
            except Exception as e:
                self.log_test(
                    "Alternative date format parsing",
                    False,
                    f"Connection error (expected in test): {str(e)}"
                )
        
        except ImportError as e:
            print(f"Skipping live API tests - missing dependencies: {e}")
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*50)
        print("FILTERING TEST SUMMARY")
        print("="*50)
        print(f"Tests Passed: {self.test_results['passed']}")
        print(f"Tests Failed: {self.test_results['failed']}")
        print(f"Success Rate: {(self.test_results['passed'] / (self.test_results['passed'] + self.test_results['failed'])) * 100:.1f}%")
        
        if self.test_results["errors"]:
            print("\nFAILED TESTS:")
            for error in self.test_results["errors"]:
                print(f"  - {error}")
        
        print("\nKey Improvements Tested:")
        print("* Date range filtering with BETWEEN syntax")
        print("* Priority OR logic (priority=1^ORpriority=2)")
        print("* Caller exclusion with NOT EQUALS")
        print("* Complete filter building")
        print("* URL encoding preservation of JavaScript functions")


async def main():
    """Run the complete filtering test suite."""
    print("ServiceNow Filtering Fixes Test Suite")
    print("=====================================")
    print("Testing all improvements made to address P1/P2 incident filtering issues")
    
    test_suite = FilteringTestSuite()
    
    # Run all tests
    test_suite.test_date_range_filtering()
    test_suite.test_priority_or_logic()
    test_suite.test_caller_exclusion()
    test_suite.test_complete_filter_building()
    test_suite.test_url_encoding()
    
    # Optional live API tests (will gracefully handle connection errors)
    await test_suite.test_live_api_calls()
    
    # Print summary
    test_suite.print_summary()
    
    return test_suite.test_results["failed"] == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)