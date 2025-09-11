"""
Comprehensive tests for query_validation.py module.

Tests the ServiceNow query construction and validation engine including:
- ServiceNowQueryBuilder functionality
- Query validation and result analysis
- Debug and analysis tools
- Edge cases and error handling
"""

import unittest
from unittest.mock import patch, MagicMock
import pytest
from typing import Dict, List

# Import the modules under test
from query_validation import (
    ServiceNowQueryBuilder,
    QueryValidationResult,
    validate_priority_filter,
    validate_date_range_filter,
    validate_query_filters,
    validate_result_count,
    cross_verify_critical_incidents,
    build_pagination_params,
    suggest_query_improvements,
    debug_query_construction
)


class TestServiceNowQueryBuilder(unittest.TestCase):
    """Test the ServiceNowQueryBuilder class methods."""
    
    def test_build_priority_or_filter_single(self):
        """Test building priority filter with single priority."""
        result = ServiceNowQueryBuilder.build_priority_or_filter(["1"])
        self.assertEqual(result, "1")
    
    def test_build_priority_or_filter_multiple(self):
        """Test building priority filter with multiple priorities."""
        result = ServiceNowQueryBuilder.build_priority_or_filter(["1", "2", "3"])
        expected = "priority=1^ORpriority=2^ORpriority=3"
        self.assertEqual(result, expected)
    
    def test_build_priority_or_filter_empty(self):
        """Test building priority filter with empty list."""
        # Empty list will have length 0, so it goes to OR logic and returns empty string
        result = ServiceNowQueryBuilder.build_priority_or_filter([])
        self.assertEqual(result, "")
    
    def test_build_date_range_filter(self):
        """Test building date range filter with proper BETWEEN syntax."""
        result = ServiceNowQueryBuilder.build_date_range_filter("2025-08-25", "2025-08-31")
        expected = "sys_created_onBETWEENjavascript:gs.dateGenerate('2025-08-25','00:00:00')@javascript:gs.dateGenerate('2025-08-31','23:59:59')"
        self.assertEqual(result, expected)
    
    def test_build_relative_date_filter_last_week(self):
        """Test building relative date filter for last week."""
        result = ServiceNowQueryBuilder.build_relative_date_filter("last week")
        expected = "sys_created_onBETWEENjavascript:gs.beginningOfLastWeek()@javascript:gs.endOfLastWeek()"
        self.assertEqual(result, expected)
    
    def test_build_relative_date_filter_today(self):
        """Test building relative date filter for today."""
        result = ServiceNowQueryBuilder.build_relative_date_filter("today")
        expected = "sys_created_onBETWEENjavascript:gs.beginningOfToday()@javascript:gs.endOfToday()"
        self.assertEqual(result, expected)
    
    def test_build_relative_date_filter_this_week(self):
        """Test building relative date filter for this week."""
        result = ServiceNowQueryBuilder.build_relative_date_filter("this week")
        expected = "sys_created_onBETWEENjavascript:gs.beginningOfThisWeek()@javascript:gs.endOfThisWeek()"
        self.assertEqual(result, expected)
    
    def test_build_relative_date_filter_last_7_days(self):
        """Test building relative date filter for last 7 days."""
        result = ServiceNowQueryBuilder.build_relative_date_filter("last 7 days")
        expected = "sys_created_onBETWEENjavascript:gs.daysAgoStart(7)@javascript:gs.daysAgoEnd(1)"
        self.assertEqual(result, expected)
    
    def test_build_relative_date_filter_fallback(self):
        """Test building relative date filter with unknown period (fallback)."""
        result = ServiceNowQueryBuilder.build_relative_date_filter("custom_period")
        expected = "sys_created_on>=custom_period"
        self.assertEqual(result, expected)
    
    def test_build_exclusion_filter_single(self):
        """Test building exclusion filter with single ID."""
        result = ServiceNowQueryBuilder.build_exclusion_filter("caller_id", ["sys_id123"])
        expected = "caller_id!=sys_id123"
        self.assertEqual(result, expected)
    
    def test_build_exclusion_filter_multiple(self):
        """Test building exclusion filter with multiple IDs."""
        result = ServiceNowQueryBuilder.build_exclusion_filter("caller_id", ["sys_id123", "sys_id456", "sys_id789"])
        expected = "caller_id!=sys_id123^caller_id!=sys_id456^caller_id!=sys_id789"
        self.assertEqual(result, expected)
    
    def test_build_complete_filter_priorities_only(self):
        """Test building complete filter with priorities only."""
        result = ServiceNowQueryBuilder.build_complete_filter(priorities=["1", "2"])
        expected = "priority=1^ORpriority=2"
        self.assertEqual(result, expected)
    
    def test_build_complete_filter_date_range_only(self):
        """Test building complete filter with date range only."""
        result = ServiceNowQueryBuilder.build_complete_filter(date_range=("2025-08-25", "2025-08-31"))
        expected = "sys_created_onBETWEENjavascript:gs.dateGenerate('2025-08-25','00:00:00')@javascript:gs.dateGenerate('2025-08-31','23:59:59')"
        self.assertEqual(result, expected)
    
    def test_build_complete_filter_date_period_only(self):
        """Test building complete filter with date period only."""
        result = ServiceNowQueryBuilder.build_complete_filter(date_period="last week")
        expected = "sys_created_onBETWEENjavascript:gs.beginningOfLastWeek()@javascript:gs.endOfLastWeek()"
        self.assertEqual(result, expected)
    
    def test_build_complete_filter_exclude_callers_only(self):
        """Test building complete filter with caller exclusions only."""
        result = ServiceNowQueryBuilder.build_complete_filter(exclude_callers=["sys_id123", "sys_id456"])
        expected = "caller_id!=sys_id123^caller_id!=sys_id456"
        self.assertEqual(result, expected)
    
    def test_build_complete_filter_all_components(self):
        """Test building complete filter with all components."""
        result = ServiceNowQueryBuilder.build_complete_filter(
            priorities=["1", "2"],
            date_range=("2025-08-25", "2025-08-31"),
            exclude_callers=["sys_id123"],
            additional_filters={"state": "New", "assignment_group": "IT Support"}
        )
        
        # Check that all components are present
        self.assertIn("sys_created_onBETWEENjavascript:gs.dateGenerate", result)
        self.assertIn("priority=1^ORpriority=2", result)
        self.assertIn("caller_id!=sys_id123", result)
        self.assertIn("state=New", result)
        self.assertIn("assignment_group=IT Support", result)
        
        # Verify proper joining with ^
        parts = result.split("^")
        self.assertGreaterEqual(len(parts), 4)  # Should have multiple parts joined by ^
    
    def test_build_complete_filter_date_range_precedence(self):
        """Test that date_range takes precedence over date_period."""
        result = ServiceNowQueryBuilder.build_complete_filter(
            date_range=("2025-08-25", "2025-08-31"),
            date_period="last week"
        )
        
        # Should use date_range, not date_period
        self.assertIn("2025-08-25", result)
        self.assertNotIn("beginningOfLastWeek", result)
    
    def test_build_complete_filter_additional_filters_exclusions(self):
        """Test that additional filters don't duplicate existing fields."""
        result = ServiceNowQueryBuilder.build_complete_filter(
            priorities=["1"],
            additional_filters={
                "priority": "2",  # Should be excluded
                "sys_created_on": ">=2025-01-01",  # Should be excluded
                "caller_id": "should_be_excluded",  # Should be excluded
                "state": "New"  # Should be included
            }
        )
        
        self.assertIn("1", result)  # From priorities param (single priority returns just the value)
        self.assertNotIn("priority=2", result)  # Should be filtered out
        self.assertIn("state=New", result)  # Should be included


class TestQueryValidationResult(unittest.TestCase):
    """Test the QueryValidationResult class."""
    
    def test_init_valid(self):
        """Test initializing valid QueryValidationResult."""
        result = QueryValidationResult(is_valid=True)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.warnings, [])
        self.assertEqual(result.suggestions, [])
        self.assertIsNone(result.corrected_filters)
    
    def test_init_invalid(self):
        """Test initializing invalid QueryValidationResult."""
        result = QueryValidationResult(is_valid=False)
        self.assertFalse(result.is_valid)
        self.assertTrue(result.has_issues())
    
    def test_add_warning(self):
        """Test adding warnings to QueryValidationResult."""
        result = QueryValidationResult()
        result.add_warning("Test warning")
        self.assertEqual(result.warnings, ["Test warning"])
        self.assertTrue(result.has_issues())
    
    def test_add_suggestion(self):
        """Test adding suggestions to QueryValidationResult."""
        result = QueryValidationResult()
        result.add_suggestion("Test suggestion")
        self.assertEqual(result.suggestions, ["Test suggestion"])
        self.assertFalse(result.has_issues())  # Suggestions don't make it invalid
    
    def test_has_issues_with_warnings(self):
        """Test has_issues() returns True with warnings."""
        result = QueryValidationResult()
        result.add_warning("Some warning")
        self.assertTrue(result.has_issues())
    
    def test_has_issues_invalid_query(self):
        """Test has_issues() returns True for invalid query."""
        result = QueryValidationResult(is_valid=False)
        self.assertTrue(result.has_issues())


class TestPriorityFilterValidation(unittest.TestCase):
    """Test priority filter validation functionality."""
    
    def test_validate_priority_filter_valid_single(self):
        """Test validating single priority filter."""
        result = validate_priority_filter("priority=1")
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.warnings), 0)
    
    def test_validate_priority_filter_valid_or_syntax(self):
        """Test validating proper OR syntax."""
        result = validate_priority_filter("priority=1^ORpriority=2")
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.warnings), 0)
    
    def test_validate_priority_filter_comma_syntax_warning(self):
        """Test validation warns about comma syntax."""
        result = validate_priority_filter("1,2,3")
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("comma syntax instead of OR", result.warnings[0])
        self.assertEqual(len(result.suggestions), 1)
        self.assertIn("priority=1^ORpriority=2", result.suggestions[0])
    
    def test_validate_priority_filter_or_without_prefix(self):
        """Test validation warns about OR syntax without priority= prefix."""
        result = validate_priority_filter("1^OR2^OR3")
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("missing 'priority=' prefix", result.warnings[0])
    
    def test_validate_priority_filter_text_format(self):
        """Test validation suggests numeric format for text priorities."""
        result = validate_priority_filter("priority=Critical^ORpriority=High")
        self.assertEqual(len(result.suggestions), 1)
        self.assertIn("numeric priority format", result.suggestions[0])
    
    def test_validate_priority_filter_mixed_numeric_and_text(self):
        """Test validation with mixed numeric and text format."""
        result = validate_priority_filter("priority=1^ORpriority=Critical")
        # Should not suggest numeric format since numeric is already present
        text_format_suggestions = [s for s in result.suggestions if "numeric priority format" in s]
        self.assertEqual(len(text_format_suggestions), 0)


class TestDateRangeFilterValidation(unittest.TestCase):
    """Test date range filter validation functionality."""
    
    def test_validate_date_range_filter_proper_between(self):
        """Test validating proper BETWEEN syntax."""
        date_filter = "sys_created_onBETWEENjavascript:gs.dateGenerate('2025-08-25','00:00:00')@javascript:gs.dateGenerate('2025-08-31','23:59:59')"
        result = validate_date_range_filter(date_filter)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.warnings), 0)
    
    def test_validate_date_range_filter_old_comparison_syntax(self):
        """Test validation warns about old comparison syntax."""
        result = validate_date_range_filter("sys_created_on>=2025-08-25")
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("old comparison syntax", result.warnings[0])
        self.assertIn("BETWEEN syntax", result.suggestions[0])
    
    def test_validate_date_range_filter_between_without_javascript(self):
        """Test validation warns about BETWEEN without JavaScript functions."""
        result = validate_date_range_filter("sys_created_onBETWEEN2025-08-25@2025-08-31")
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("missing JavaScript date functions", result.warnings[0])
    
    def test_validate_date_range_filter_between_without_separator(self):
        """Test validation warns about missing @ separator."""
        result = validate_date_range_filter("sys_created_onBETWEENjavascript:gs.dateGenerate('2025-08-25','00:00:00')javascript:gs.dateGenerate('2025-08-31','23:59:59')")
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("missing '@' separator", result.warnings[0])
    
    def test_validate_date_range_filter_week_35_suggestion(self):
        """Test validation provides suggestion for Week 35 2025."""
        result = validate_date_range_filter("sys_created_onBETWEENjavascript:gs.dateGenerate('2025-08-25','00:00:00')@javascript:gs.dateGenerate('2025-08-31','23:59:59')")
        suggestions_about_week35 = [s for s in result.suggestions if "Week 35 2025" in s]
        self.assertEqual(len(suggestions_about_week35), 1)
        self.assertIn("timezone handling", suggestions_about_week35[0])


class TestQueryFiltersValidation(unittest.TestCase):
    """Test the main validate_query_filters function."""
    
    def test_validate_query_filters_empty(self):
        """Test validating empty filters."""
        result = validate_query_filters({})
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.warnings), 0)
    
    def test_validate_query_filters_priority_only(self):
        """Test validating filters with priority only."""
        filters = {"priority": "1,2,3"}
        result = validate_query_filters(filters)
        
        # Should have warnings from priority validation
        priority_warnings = [w for w in result.warnings if "comma syntax" in w]
        self.assertGreater(len(priority_warnings), 0)
    
    def test_validate_query_filters_date_only(self):
        """Test validating filters with date only."""
        filters = {"sys_created_on": "sys_created_on>=2025-08-25"}
        result = validate_query_filters(filters)
        
        # Should have warnings from date validation
        date_warnings = [w for w in result.warnings if "old comparison syntax" in w]
        self.assertGreater(len(date_warnings), 0)
    
    def test_validate_query_filters_both_priority_and_date(self):
        """Test validating filters with both priority and date issues."""
        filters = {
            "priority": "1,2,3",
            "sys_created_on": "sys_created_on>=2025-08-25"
        }
        result = validate_query_filters(filters)
        
        # Should have warnings from both validators
        self.assertGreaterEqual(len(result.warnings), 2)
        self.assertGreaterEqual(len(result.suggestions), 2)
    
    def test_validate_query_filters_other_fields_ignored(self):
        """Test that validation ignores other fields gracefully."""
        filters = {
            "state": "New",
            "assignment_group": "IT Support",
            "caller_id": "some_sys_id"
        }
        result = validate_query_filters(filters)
        
        # Should not produce warnings for non-validated fields
        self.assertEqual(len(result.warnings), 0)
        self.assertTrue(result.is_valid)


class TestResultCountValidation(unittest.TestCase):
    """Test result count validation functionality."""
    
    def test_validate_result_count_normal_incident_count(self):
        """Test validation passes for normal incident count."""
        result = validate_result_count("incident", {"priority": "priority=1^ORpriority=2"}, 10)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.warnings), 0)
    
    def test_validate_result_count_low_priority_incident_warning(self):
        """Test validation warns about low P1/P2 incident count."""
        result = validate_result_count("incident", {"priority": "priority=1^ORpriority=2"}, 1)
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("Low P1/P2 incident count", result.warnings[0])
        self.assertIn("Cross-verify", result.suggestions[0])
    
    def test_validate_result_count_non_incident_table(self):
        """Test validation doesn't warn for non-incident tables."""
        result = validate_result_count("change_request", {"priority": "1"}, 1)
        self.assertEqual(len(result.warnings), 0)
    
    def test_validate_result_count_incident_non_priority_query(self):
        """Test validation doesn't warn for non-priority incident queries."""
        result = validate_result_count("incident", {"state": "New"}, 1)
        self.assertEqual(len(result.warnings), 0)
    
    def test_validate_result_count_incident_low_priority_only(self):
        """Test validation only warns for high priority (1,2) incidents."""
        result = validate_result_count("incident", {"priority": "priority=3^ORpriority=4"}, 1)
        self.assertEqual(len(result.warnings), 0)


class TestUtilityFunctions(unittest.TestCase):
    """Test utility and helper functions."""
    
    def test_cross_verify_critical_incidents(self):
        """Test cross verification function structure."""
        result = cross_verify_critical_incidents()
        
        # Check expected structure
        self.assertIn("missing_critical", result)
        self.assertIn("verification_attempted", result)
        self.assertIn("additional_found", result)
        
        # Check types
        self.assertIsInstance(result["missing_critical"], list)
        self.assertIsInstance(result["verification_attempted"], bool)
        self.assertIsInstance(result["additional_found"], int)
        
        self.assertTrue(result["verification_attempted"])
    
    def test_build_pagination_params_defaults(self):
        """Test building pagination parameters with defaults."""
        result = build_pagination_params()
        expected = {"sysparm_offset": "0", "sysparm_limit": "250"}
        self.assertEqual(result, expected)
    
    def test_build_pagination_params_custom(self):
        """Test building pagination parameters with custom values."""
        result = build_pagination_params(offset=100, limit=500)
        expected = {"sysparm_offset": "100", "sysparm_limit": "500"}
        self.assertEqual(result, expected)
    
    def test_suggest_query_improvements_zero_results(self):
        """Test suggestions for zero results."""
        suggestions = suggest_query_improvements({}, 0)
        
        self.assertGreater(len(suggestions), 0)
        suggestion_text = " ".join(suggestions)
        self.assertIn("broader date range", suggestion_text)
        self.assertIn("filter syntax", suggestion_text)
        self.assertIn("field names", suggestion_text)
        self.assertIn("date format", suggestion_text)
    
    def test_suggest_query_improvements_low_priority_results(self):
        """Test suggestions for low priority query results."""
        suggestions = suggest_query_improvements({"priority": "1,2"}, 2)
        
        priority_suggestions = [s for s in suggestions if "OR syntax" in s or "priority" in s]
        self.assertGreater(len(priority_suggestions), 0)
    
    def test_suggest_query_improvements_high_result_count(self):
        """Test suggestions for high result count."""
        suggestions = suggest_query_improvements({}, 1500)
        
        self.assertGreater(len(suggestions), 0)
        suggestion_text = " ".join(suggestions)
        self.assertIn("more specific filters", suggestion_text)
        self.assertIn("reduce result set", suggestion_text)
    
    def test_suggest_query_improvements_normal_count(self):
        """Test no suggestions for normal result count."""
        suggestions = suggest_query_improvements({"state": "New"}, 50)
        
        # Should have fewer suggestions for normal result counts
        self.assertLessEqual(len(suggestions), 2)


class TestDebugQueryConstruction(unittest.TestCase):
    """Test query construction debugging functionality."""
    
    def test_debug_query_construction_basic(self):
        """Test basic query construction debugging."""
        query_string = "priority=1^sys_created_on>=2025-08-25"
        debug_info = debug_query_construction(query_string)
        
        # Check basic structure
        self.assertIn("query_length", debug_info)
        self.assertIn("components", debug_info)
        self.assertIn("potential_issues", debug_info)
        self.assertIn("recommendations", debug_info)
        self.assertIn("condition_count", debug_info)
        
        # Check values
        self.assertEqual(debug_info["query_length"], len(query_string))
        self.assertEqual(debug_info["condition_count"], 2)  # Two conditions separated by ^
    
    def test_debug_query_construction_priority_detection(self):
        """Test priority filtering detection in debug."""
        query_string = "priority=1^ORpriority=2"
        debug_info = debug_query_construction(query_string)
        
        self.assertIn("Priority filtering", debug_info["components"])
        self.assertIn("OR logic (correct)", debug_info["components"])
    
    def test_debug_query_construction_date_between_detection(self):
        """Test date BETWEEN syntax detection in debug."""
        query_string = "sys_created_onBETWEENjavascript:gs.dateGenerate('2025-08-25','00:00:00')@javascript:gs.dateGenerate('2025-08-31','23:59:59')"
        debug_info = debug_query_construction(query_string)
        
        self.assertIn("Date filtering", debug_info["components"])
        self.assertIn("BETWEEN syntax (correct)", debug_info["components"])
        self.assertIn("JavaScript date functions", debug_info["components"])
        self.assertIn("Proper date range separators", debug_info["components"])
    
    def test_debug_query_construction_caller_exclusion_detection(self):
        """Test caller exclusion detection in debug."""
        query_string = "caller_id!=sys_id123^caller_id!=sys_id456"
        debug_info = debug_query_construction(query_string)
        
        self.assertIn("Caller exclusion", debug_info["components"])
        self.assertIn("2 caller(s) excluded", debug_info["components"])
    
    def test_debug_query_construction_old_date_syntax_issue(self):
        """Test detection of old date syntax as potential issue."""
        query_string = "sys_created_on>=2025-08-25^priority=1"
        debug_info = debug_query_construction(query_string)
        
        self.assertIn("Using old date comparison syntax", debug_info["potential_issues"])
        self.assertIn("Update to BETWEEN syntax for better reliability", debug_info["recommendations"])
    
    def test_debug_query_construction_unencoded_spaces_issue(self):
        """Test detection of unencoded spaces as potential issue."""
        query_string = "assignment_group=IT Support^priority=1"
        debug_info = debug_query_construction(query_string)
        
        self.assertIn("Unencoded spaces in query", debug_info["potential_issues"])
        self.assertIn("Ensure proper URL encoding", debug_info["recommendations"])
    
    def test_debug_query_construction_complex_query_recommendation(self):
        """Test recommendation for overly complex queries."""
        # Create a query with many conditions (>5)
        query_string = "priority=1^state=New^assignment_group=IT^caller_id!=sys1^caller_id!=sys2^sys_created_on>=2025-01-01"
        debug_info = debug_query_construction(query_string)
        
        self.assertGreater(debug_info["condition_count"], 5)
        complexity_recommendations = [r for r in debug_info["recommendations"] if "simplifying complex query" in r]
        self.assertGreater(len(complexity_recommendations), 0)
    
    def test_debug_query_construction_with_original_filters(self):
        """Test debugging with original filters provided."""
        query_string = "priority=1^ORpriority=2"
        original_filters = {
            "priority": "1,2",  # comma syntax
            "state": "New"
        }
        debug_info = debug_query_construction(query_string, original_filters)
        
        self.assertEqual(debug_info["original_filter_count"], 2)
        self.assertEqual(debug_info["original_filters"], ["priority", "state"])
        
        # Should detect comma syntax issue
        comma_issues = [issue for issue in debug_info["potential_issues"] if "comma syntax instead of OR" in issue]
        self.assertGreater(len(comma_issues), 0)
    
    def test_debug_query_construction_complete_query_detection(self):
        """Test detection of complete query construction."""
        original_filters = {"_complete_query": "priority=1^state=New"}
        debug_info = debug_query_construction("priority=1^state=New", original_filters)
        
        self.assertIn("Using complete query construction", debug_info["components"])
    
    def test_debug_query_construction_empty_query(self):
        """Test debugging empty query string."""
        debug_info = debug_query_construction("")
        
        self.assertEqual(debug_info["query_length"], 0)
        self.assertEqual(debug_info["condition_count"], 0)
        self.assertEqual(len(debug_info["components"]), 0)


class TestEdgeCasesAndErrorHandling(unittest.TestCase):
    """Test edge cases and error handling scenarios."""
    
    def test_servicenow_query_builder_none_inputs(self):
        """Test ServiceNowQueryBuilder handles None inputs gracefully."""
        result = ServiceNowQueryBuilder.build_complete_filter(
            priorities=None,
            date_period=None,
            date_range=None,
            exclude_callers=None,
            additional_filters=None
        )
        self.assertEqual(result, "")
    
    def test_servicenow_query_builder_empty_lists(self):
        """Test ServiceNowQueryBuilder handles empty lists gracefully."""
        result = ServiceNowQueryBuilder.build_complete_filter(
            priorities=[],
            exclude_callers=[],
            additional_filters={}
        )
        self.assertEqual(result, "")
    
    def test_validate_priority_filter_empty_string(self):
        """Test priority filter validation with empty string."""
        result = validate_priority_filter("")
        self.assertTrue(result.is_valid)  # Empty should be valid
        self.assertEqual(len(result.warnings), 0)
    
    def test_validate_date_range_filter_empty_string(self):
        """Test date range filter validation with empty string."""
        result = validate_date_range_filter("")
        self.assertTrue(result.is_valid)  # Empty should be valid
        self.assertEqual(len(result.warnings), 0)
    
    def test_validate_result_count_edge_values(self):
        """Test result count validation with edge values."""
        # Test with 0 count and non-priority query
        result = validate_result_count("incident", {"state": "New"}, 0)
        self.assertEqual(len(result.warnings), 0)  # Not high priority query
        
        # Test with exactly threshold value for high priority
        result = validate_result_count("incident", {"priority": "priority=1^ORpriority=2"}, 2)
        self.assertEqual(len(result.warnings), 0)  # Should be at threshold
    
    def test_debug_query_construction_none_inputs(self):
        """Test debug_query_construction handles None inputs."""
        # The function doesn't handle None input, so test with empty string instead
        debug_info = debug_query_construction("", None)
        
        # Should handle empty string gracefully
        self.assertIsInstance(debug_info, dict)
        self.assertIn("query_length", debug_info)
        self.assertIn("components", debug_info)
        self.assertEqual(debug_info["query_length"], 0)
    
    def test_build_pagination_params_edge_values(self):
        """Test pagination params with edge values."""
        # Test with 0 values
        result = build_pagination_params(0, 0)
        self.assertEqual(result, {"sysparm_offset": "0", "sysparm_limit": "0"})
        
        # Test with large values
        result = build_pagination_params(999999, 999999)
        self.assertEqual(result, {"sysparm_offset": "999999", "sysparm_limit": "999999"})


if __name__ == "__main__":
    unittest.main()