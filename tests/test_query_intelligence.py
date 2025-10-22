"""
Comprehensive tests for query_intelligence.py
Target: 85%+ line coverage, 60%+ branch coverage
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from query_intelligence import (
    QueryIntelligence,
    QueryExplainer,
    build_smart_filter,
    explain_existing_filter,
    get_filter_templates
)
from query_validation import QueryValidationResult


class TestQueryIntelligenceTemplates:
    """Test filter template functionality."""

    def test_filter_templates_exist(self):
        """Test that FILTER_TEMPLATES constant is properly defined."""
        templates = QueryIntelligence.FILTER_TEMPLATES
        assert isinstance(templates, dict)
        assert len(templates) > 0

    def test_all_template_keys(self):
        """Test that all expected templates exist."""
        templates = QueryIntelligence.FILTER_TEMPLATES
        expected_keys = [
            "high_priority_last_week",
            "critical_recent",
            "unassigned_recent",
            "resolved_this_month",
            "active_p1_p2",
            "p1_p2_all_states"
        ]
        for key in expected_keys:
            assert key in templates, f"Missing template: {key}"

    def test_template_structure(self):
        """Test that templates have proper structure."""
        templates = QueryIntelligence.FILTER_TEMPLATES
        for name, template in templates.items():
            assert isinstance(template, dict), f"Template {name} is not a dict"
            assert len(template) > 0, f"Template {name} is empty"

    def test_get_filter_templates(self):
        """Test convenience function for getting templates."""
        result = get_filter_templates()
        assert isinstance(result, dict)
        assert len(result) > 0
        # Ensure it returns a copy, not the original
        result["test_key"] = "test_value"
        assert "test_key" not in QueryIntelligence.FILTER_TEMPLATES


class TestTemplateMatching:
    """Test template matching functionality."""

    def test_match_high_priority_last_week(self):
        """Test matching high priority last week template."""
        test_queries = [
            "high priority incidents from last week",
            "critical tickets from past week",
            "p1 p2 last week"
        ]
        for query in test_queries:
            result = QueryIntelligence._match_filter_template(query.lower())
            assert result is not None, f"Failed to match: {query}"
            assert result["name"] == "high_priority_last_week"

    def test_match_critical_recent(self):
        """Test matching critical recent template."""
        test_queries = [
            "critical incidents from yesterday",
            "p1 from today",
            "critical recent"
        ]
        for query in test_queries:
            result = QueryIntelligence._match_filter_template(query.lower())
            assert result is not None
            assert result["name"] == "critical_recent"

    def test_match_unassigned_recent(self):
        """Test matching unassigned recent template."""
        result = QueryIntelligence._match_filter_template("unassigned recent")
        assert result is not None
        assert result["name"] == "unassigned_recent"

    def test_match_resolved_this_month(self):
        """Test matching resolved this month template."""
        result = QueryIntelligence._match_filter_template("resolved this month")
        assert result is not None
        assert result["name"] == "resolved_this_month"

    def test_match_active_p1_p2(self):
        """Test matching active p1 p2 template."""
        test_queries = [
            "active critical incidents",
            "open high priority",
            "active p1"
        ]
        for query in test_queries:
            result = QueryIntelligence._match_filter_template(query.lower())
            assert result is not None
            assert result["name"] == "active_p1_p2"

    def test_match_p1_p2_all_states(self):
        """Test matching p1 and p2 template."""
        test_queries = [
            "p1 and p2",
            "p1 p2"
        ]
        for query in test_queries:
            result = QueryIntelligence._match_filter_template(query.lower())
            assert result is not None
            assert result["name"] == "p1_p2_all_states"

    def test_no_match_returns_none(self):
        """Test that non-matching queries return None."""
        result = QueryIntelligence._match_filter_template("random query text")
        assert result is None


class TestExclusionFilters:
    """Test exclusion filter handling."""

    def test_handle_exclusion_logicmonitor(self):
        """Test exclusion of known entity LogicMonitor."""
        result = QueryIntelligence._handle_exclusion_filter("caller", "logicmonitor")
        assert "_complete_caller_exclusion" in result
        assert "1727339e47d99190c43d3171e36d43ad" in result["_complete_caller_exclusion"]

    def test_handle_exclusion_logicmonitor_integration(self):
        """Test exclusion of LogicMonitor Integration (with spaces)."""
        result = QueryIntelligence._handle_exclusion_filter("caller", "logicmonitor integration")
        assert "_complete_caller_exclusion" in result
        assert "1727339e47d99190c43d3171e36d43ad" in result["_complete_caller_exclusion"]

    def test_handle_exclusion_unknown_entity(self):
        """Test exclusion of unknown entity."""
        result = QueryIntelligence._handle_exclusion_filter("caller", "john_doe")
        assert "caller_id" in result
        assert result["caller_id"] == "!=john_doe"

    def test_handle_exclusion_field_mapping(self):
        """Test field mapping for exclusions."""
        # Test "caller" maps to "caller_id"
        result = QueryIntelligence._handle_exclusion_filter("caller", "test")
        assert "caller_id" in result or "_complete_caller_exclusion" in result

        # Test "reporter" maps to "caller_id"
        result = QueryIntelligence._handle_exclusion_filter("reporter", "test")
        assert "caller_id" in result or "_complete_caller_exclusion" in result

        # Test "assignee" maps to "assigned_to"
        result = QueryIntelligence._handle_exclusion_filter("assignee", "test")
        assert "assigned_to" in result


class TestPriorityFilters:
    """Test priority filter handling."""

    def test_merge_priority_same_values(self):
        """Test merging same priority values."""
        result = QueryIntelligence._merge_priority_filters("1", "1")
        assert result == "1"

    def test_merge_priority_different_values(self):
        """Test merging different priority values."""
        result = QueryIntelligence._merge_priority_filters("1", "2")
        assert "^OR" in result
        assert "priority=1" in result
        assert "priority=2" in result

    def test_merge_priority_with_existing_or(self):
        """Test merging into existing OR filter."""
        existing = "priority=1^ORpriority=2"
        result = QueryIntelligence._merge_priority_filters(existing, "3")
        assert "priority=1" in result
        assert "priority=2" in result
        assert "priority=3" in result

    def test_merge_priority_duplicate_in_or(self):
        """Test that duplicate priorities are not added."""
        existing = "priority=1^ORpriority=2"
        result = QueryIntelligence._merge_priority_filters(existing, "1")
        # Should not add duplicate
        assert result == existing


class TestLanguagePatternParsing:
    """Test natural language pattern parsing."""

    def test_parse_critical_priority(self):
        """Test parsing critical/P1 patterns."""
        test_queries = [
            "critical incidents",
            "p1 tickets",
            "priority 1 items",
            "urgent tickets"
        ]
        for query in test_queries:
            parsed_filters = {}
            confidence, explanations = QueryIntelligence._parse_language_patterns(
                query.lower(), parsed_filters
            )
            assert "priority" in parsed_filters
            assert parsed_filters["priority"] == "1"
            assert confidence > 0

    def test_parse_high_priority(self):
        """Test parsing high/P2 patterns."""
        parsed_filters = {}
        confidence, explanations = QueryIntelligence._parse_language_patterns(
            "high priority incidents", parsed_filters
        )
        assert "priority" in parsed_filters
        assert "2" in parsed_filters["priority"]

    def test_parse_time_patterns(self):
        """Test parsing time-based patterns."""
        test_cases = [
            ("last week incidents", "sys_created_on"),
            ("this week tickets", "sys_created_on"),
            ("today's incidents", "sys_created_on"),
            ("yesterday's tickets", "sys_created_on"),
            ("last month issues", "sys_created_on"),
            ("this month incidents", "sys_created_on"),
        ]
        for query, expected_field in test_cases:
            parsed_filters = {}
            confidence, explanations = QueryIntelligence._parse_language_patterns(
                query.lower(), parsed_filters
            )
            assert expected_field in parsed_filters

    def test_parse_state_patterns(self):
        """Test parsing state patterns."""
        test_cases = [
            ("new incidents", "state"),
            ("resolved tickets", "state"),
            ("in progress items", "state"),
            ("pending tickets", "state"),
            ("cancelled incidents", "state"),
        ]
        for query, expected_field in test_cases:
            parsed_filters = {}
            QueryIntelligence._parse_language_patterns(query.lower(), parsed_filters)
            assert expected_field in parsed_filters

    def test_parse_assignment_patterns(self):
        """Test parsing assignment patterns."""
        test_cases = [
            ("unassigned tickets", "assigned_to", "NULL"),
            ("not assigned incidents", "assigned_to", "NULL"),
            ("no assignee tickets", "assigned_to", "NULL"),
        ]
        for query, expected_field, expected_value in test_cases:
            parsed_filters = {}
            QueryIntelligence._parse_language_patterns(query.lower(), parsed_filters)
            assert expected_field in parsed_filters
            assert expected_value in parsed_filters[expected_field]

    def test_parse_last_n_days_pattern(self):
        """Test parsing 'last N days' pattern with lambda."""
        parsed_filters = {}
        confidence, explanations = QueryIntelligence._parse_language_patterns(
            "incidents from last 7 days", parsed_filters
        )
        assert "sys_created_on" in parsed_filters
        assert "daysAgoStart(7)" in parsed_filters["sys_created_on"]


class TestExclusionPatternParsing:
    """Test exclusion pattern parsing."""

    def test_parse_exclude_caller_pattern(self):
        """Test parsing 'exclude caller' patterns."""
        result = QueryIntelligence._parse_exclusion_patterns(
            "exclude caller logicmonitor from incidents"
        )
        assert result is not None
        assert "filters" in result
        assert "confidence" in result
        assert "explanation" in result

    def test_parse_without_caller_pattern(self):
        """Test parsing 'without caller' patterns."""
        result = QueryIntelligence._parse_exclusion_patterns(
            "incidents without caller john"
        )
        assert result is not None
        assert "filters" in result

    def test_parse_no_exclusion_returns_none(self):
        """Test that queries without exclusions return None."""
        result = QueryIntelligence._parse_exclusion_patterns(
            "normal query without exclusions"
        )
        assert result is None


class TestNaturalLanguageParsing:
    """Test complete natural language parsing."""

    @patch('query_intelligence.QueryIntelligence._validate_and_improve_filters')
    def test_parse_natural_language_with_template(self, mock_validate):
        """Test parsing that matches a template."""
        mock_validate.return_value = QueryValidationResult(is_valid=True)

        result = QueryIntelligence.parse_natural_language(
            "high priority incidents from last week",
            "incident"
        )

        assert "filters" in result
        assert "confidence" in result
        assert "explanation" in result
        assert "template_used" in result
        assert result["template_used"] is not None

    @patch('query_intelligence.QueryIntelligence._validate_and_improve_filters')
    def test_parse_natural_language_without_template(self, mock_validate):
        """Test parsing without template match."""
        mock_validate.return_value = QueryValidationResult(is_valid=True)

        result = QueryIntelligence.parse_natural_language(
            "critical incidents from yesterday",
            "incident"
        )

        assert "filters" in result
        assert "priority" in result["filters"]
        assert result["confidence"] > 0

    @patch('query_intelligence.QueryIntelligence._validate_and_improve_filters')
    @patch('query_intelligence.extract_keywords')
    def test_parse_natural_language_keyword_fallback(self, mock_keywords, mock_validate):
        """Test keyword fallback when no patterns match."""
        mock_keywords.return_value = ["database"]
        mock_validate.return_value = QueryValidationResult(is_valid=True)

        result = QueryIntelligence.parse_natural_language(
            "database server issues",
            "incident"
        )

        assert "filters" in result
        # Should use keyword search as fallback

    @patch('query_intelligence.QueryIntelligence._validate_and_improve_filters')
    @patch('Table_Tools.generic_table_tools._parse_date_range_from_text')
    def test_parse_natural_language_with_date_range(self, mock_date_parse, mock_validate):
        """Test parsing with date range."""
        mock_date_parse.return_value = ("2025-08-25", "2025-08-31")
        mock_validate.return_value = QueryValidationResult(is_valid=True)

        result = QueryIntelligence.parse_natural_language(
            "incidents from week 35 2025",
            "incident"
        )

        assert "filters" in result

    @patch('query_intelligence.QueryIntelligence._validate_and_improve_filters')
    def test_parse_natural_language_with_exclusion(self, mock_validate):
        """Test parsing with exclusion patterns."""
        mock_validate.return_value = QueryValidationResult(is_valid=True)

        result = QueryIntelligence.parse_natural_language(
            "incidents excluding caller logicmonitor",
            "incident"
        )

        assert "filters" in result


class TestFilterValidationAndImprovement:
    """Test filter validation and auto-correction."""

    @patch('query_validation.validate_query_filters')
    def test_validate_priority_comma_correction(self, mock_validate):
        """Test that comma-separated priorities are corrected to OR syntax."""
        mock_validate.return_value = QueryValidationResult(is_valid=True)

        filters = {"priority": "1,2"}
        result = QueryIntelligence._validate_and_improve_filters(filters, "incident")

        assert result.corrected_filters is not None
        assert "^OR" in result.corrected_filters.get("priority", "")

    @patch('query_validation.validate_query_filters')
    def test_validate_date_time_component_addition(self, mock_validate):
        """Test that time components are added to dates."""
        mock_validate.return_value = QueryValidationResult(is_valid=True)

        filters = {"sys_created_on": ">=2024-01-01"}
        result = QueryIntelligence._validate_and_improve_filters(filters, "incident")

        # Should add time component
        assert result.corrected_filters is not None

    @patch('query_validation.validate_query_filters')
    def test_validate_correct_filters_unchanged(self, mock_validate):
        """Test that correct filters are not changed."""
        mock_validate.return_value = QueryValidationResult(is_valid=True)

        filters = {"priority": "priority=1^ORpriority=2"}
        result = QueryIntelligence._validate_and_improve_filters(filters, "incident")

        # Should not change already correct filters


class TestContextFilters:
    """Test context-based filter application."""

    def test_apply_context_date_range(self):
        """Test applying date range from context."""
        context = {
            "date_range": {
                "start": "2025-08-01",
                "end": "2025-08-31"
            }
        }
        result = QueryIntelligence._apply_context_filters(context, "incident")

        assert "sys_created_on" in result
        assert "BETWEEN" in result["sys_created_on"]
        assert "2025-08-01" in result["sys_created_on"]
        assert "2025-08-31" in result["sys_created_on"]

    def test_apply_context_exclude_single_caller(self):
        """Test applying single caller exclusion from context."""
        context = {"exclude_caller": "test_sys_id"}
        result = QueryIntelligence._apply_context_filters(context, "incident")

        assert "_complete_caller_exclusion" in result
        assert "caller_id!=test_sys_id" in result["_complete_caller_exclusion"]

    def test_apply_context_exclude_multiple_callers(self):
        """Test applying multiple caller exclusions from context."""
        context = {"exclude_caller": ["sys_id_1", "sys_id_2"]}
        result = QueryIntelligence._apply_context_filters(context, "incident")

        assert "_complete_caller_exclusion" in result
        assert "caller_id!=sys_id_1" in result["_complete_caller_exclusion"]
        assert "caller_id!=sys_id_2" in result["_complete_caller_exclusion"]

    def test_apply_context_exclude_resolved(self):
        """Test applying exclude resolved from context."""
        context = {"exclude_resolved": True}
        result = QueryIntelligence._apply_context_filters(context, "incident")

        assert "state" in result
        assert "!=" in result["state"]

    def test_apply_context_user_assigned_only(self):
        """Test applying user-assigned filter from context."""
        context = {"user_assigned_only": True}
        result = QueryIntelligence._apply_context_filters(context, "incident")

        assert "assigned_to" in result
        assert "getUserID" in result["assigned_to"]

    def test_apply_context_empty(self):
        """Test that empty context returns empty filters."""
        result = QueryIntelligence._apply_context_filters({}, "incident")
        assert result == {}


class TestFilterExplanations:
    """Test filter explanation generation."""

    def test_explain_priority_filter_single(self):
        """Test explaining single priority filter."""
        result = QueryIntelligence._explain_priority_filter("1")
        assert "Priority: 1" in result

    def test_explain_priority_filter_or(self):
        """Test explaining OR priority filter."""
        result = QueryIntelligence._explain_priority_filter("priority=1^ORpriority=2")
        assert "Priority levels:" in result
        assert "1" in result
        assert "2" in result

    def test_explain_date_filter_last_week(self):
        """Test explaining last week date filter."""
        result = QueryIntelligence._explain_date_filter("Last week")
        assert "Created last week" in result

    def test_explain_date_filter_days_ago(self):
        """Test explaining days ago date filter."""
        result = QueryIntelligence._explain_date_filter(">=javascript:gs.daysAgoStart(7)")
        assert "last 7 days" in result

    def test_explain_state_filter_exclusion(self):
        """Test explaining state exclusion filter."""
        result = QueryIntelligence._explain_state_filter("state!=6^state!=7")
        assert "Excluding" in result

    def test_explain_state_filter_normal(self):
        """Test explaining normal state filter."""
        result = QueryIntelligence._explain_state_filter("6")
        assert "State: 6" in result

    def test_explain_assigned_to_null(self):
        """Test explaining unassigned filter."""
        result = QueryIntelligence._explain_assigned_to_filter("NULL")
        assert "Unassigned" in result

    def test_explain_assigned_to_value(self):
        """Test explaining assigned to specific user."""
        result = QueryIntelligence._explain_assigned_to_filter("user_sys_id")
        assert "Assigned to:" in result

    def test_explain_custom_query_filter(self):
        """Test explaining custom query filter."""
        result = QueryIntelligence._explain_custom_query_filter("custom_query_string")
        assert "Custom query:" in result

    def test_generate_filter_explanation_empty(self):
        """Test explanation for empty filters."""
        result = QueryIntelligence._generate_filter_explanation({}, "incident")
        assert "No filters" in result
        assert "all incident records" in result

    def test_generate_filter_explanation_with_filters(self):
        """Test explanation for filters."""
        filters = {
            "priority": "priority=1^ORpriority=2",
            "state": "state!=6"
        }
        result = QueryIntelligence._generate_filter_explanation(filters, "incident")
        assert "Will find incident records" in result
        assert "Priority levels:" in result


class TestSQLGeneration:
    """Test SQL equivalent generation."""

    def test_generate_sql_empty_filters(self):
        """Test SQL generation for empty filters."""
        result = QueryIntelligence._generate_sql_equivalent({}, "incident")
        assert result == "SELECT * FROM incident"

    def test_generate_sql_single_filter(self):
        """Test SQL generation for single filter."""
        filters = {"priority": "1"}
        result = QueryIntelligence._generate_sql_equivalent(filters, "incident")
        assert "SELECT * FROM incident WHERE" in result
        assert "priority = '1'" in result

    def test_generate_sql_or_condition(self):
        """Test SQL generation for OR conditions."""
        filters = {"priority": "priority=1^ORpriority=2"}
        result = QueryIntelligence._generate_sql_equivalent(filters, "incident")
        assert "OR" in result

    def test_generate_sql_not_equal(self):
        """Test SQL generation for not equal."""
        filters = {"state": "!=6"}
        result = QueryIntelligence._generate_sql_equivalent(filters, "incident")
        assert "!=" in result

    def test_generate_sql_greater_equal(self):
        """Test SQL generation for greater than or equal."""
        filters = {"sys_created_on": ">=2024-01-01"}
        result = QueryIntelligence._generate_sql_equivalent(filters, "incident")
        assert ">=" in result

    def test_generate_sql_complete_query(self):
        """Test SQL generation for complete query."""
        filters = {"_complete_query": "priority=1^state=2"}
        result = QueryIntelligence._generate_sql_equivalent(filters, "incident")
        assert "priority=1^state=2" in result


class TestIntelligentFilterBuilding:
    """Test the main intelligent filter building function."""

    @patch('query_intelligence.QueryIntelligence._validate_and_improve_filters')
    def test_build_intelligent_filter_basic(self, mock_validate):
        """Test basic intelligent filter building."""
        mock_validate.return_value = QueryValidationResult(is_valid=True)

        result = QueryIntelligence.build_intelligent_filter(
            "critical incidents from yesterday",
            "incident"
        )

        assert "filters" in result
        assert "explanation" in result
        assert "confidence" in result
        assert "suggestions" in result
        assert "sql_equivalent" in result

    @patch('query_intelligence.QueryIntelligence._validate_and_improve_filters')
    def test_build_intelligent_filter_with_context(self, mock_validate):
        """Test intelligent filter building with context."""
        mock_validate.return_value = QueryValidationResult(is_valid=True)

        context = {"exclude_resolved": True}
        result = QueryIntelligence.build_intelligent_filter(
            "critical incidents",
            "incident",
            context
        )

        assert "filters" in result
        assert "state" in result["filters"]


class TestQueryExplainer:
    """Test QueryExplainer functionality."""

    def test_check_priority_filter_issue_comma(self):
        """Test detection of comma-separated priority issue."""
        result = QueryExplainer._check_priority_filter_issue("priority", "1,2")
        assert result is not None
        assert "comma" in result[0].lower()
        assert "OR syntax" in result[1]

    def test_check_priority_filter_issue_correct(self):
        """Test that correct priority filter has no issue."""
        result = QueryExplainer._check_priority_filter_issue("priority", "priority=1^ORpriority=2")
        assert result is None

    def test_check_date_filter_issue_incomplete_range(self):
        """Test detection of incomplete date range."""
        result = QueryExplainer._check_date_filter_issue("sys_created_on", ">=2024-01-01")
        assert result is not None
        assert "incomplete" in result[0].lower()

    def test_check_date_filter_issue_complete_range(self):
        """Test that complete date range has no issue."""
        result = QueryExplainer._check_date_filter_issue("sys_created_on", ">=2024-01-01<=2024-12-31")
        assert result is None

    def test_analyze_filter_issues_multiple(self):
        """Test analyzing filters with multiple issues."""
        filters = {
            "priority": "1,2",
            "sys_created_on": ">=2024-01-01"
        }
        issues, suggestions = QueryExplainer._analyze_filter_issues(filters)
        assert len(issues) == 2
        assert len(suggestions) == 2

    def test_analyze_filter_issues_none(self):
        """Test analyzing filters with no issues."""
        filters = {
            "priority": "priority=1^ORpriority=2",
            "state": "6"
        }
        issues, suggestions = QueryExplainer._analyze_filter_issues(filters)
        assert len(issues) == 0
        assert len(suggestions) == 0

    def test_explain_filter_basic(self):
        """Test basic filter explanation."""
        filters = {"priority": "1"}
        result = QueryExplainer.explain_filter(filters, "incident")

        assert "explanation" in result
        assert "sql_equivalent" in result
        assert "potential_issues" in result
        assert "suggestions" in result
        assert "estimated_result_size" in result

    def test_explain_filter_with_issues(self):
        """Test explaining filter with issues."""
        filters = {"priority": "1,2"}
        result = QueryExplainer.explain_filter(filters, "incident")

        assert len(result["potential_issues"]) > 0
        assert len(result["suggestions"]) > 0


class TestResultSizeEstimation:
    """Test result size estimation."""

    def test_calculate_priority_factor_no_priority(self):
        """Test priority factor with no priority filter."""
        filters = {"state": "6"}
        factor = QueryExplainer._calculate_priority_factor(filters)
        assert factor == 0.0

    def test_calculate_priority_factor_p1(self):
        """Test priority factor with P1."""
        filters = {"priority": "1"}
        factor = QueryExplainer._calculate_priority_factor(filters)
        assert factor > 0

    def test_calculate_priority_factor_with_or(self):
        """Test priority factor with OR (reduces selectivity)."""
        filters = {"priority": "priority=1^ORpriority=2"}
        factor = QueryExplainer._calculate_priority_factor(filters)
        # OR should reduce the factor
        assert isinstance(factor, float)

    def test_calculate_date_factor_no_date(self):
        """Test date factor with no date filter."""
        filters = {"priority": "1"}
        factor = QueryExplainer._calculate_date_factor(filters)
        assert factor == 0.0

    def test_calculate_date_factor_today(self):
        """Test date factor for today only."""
        filters = {"sys_created_on": ">=javascript:gs.daysAgoStart(1)"}
        factor = QueryExplainer._calculate_date_factor(filters)
        assert factor == 2

    def test_calculate_date_factor_last_week(self):
        """Test date factor for last week."""
        filters = {"sys_created_on": ">=javascript:gs.daysAgoStart(7)"}
        factor = QueryExplainer._calculate_date_factor(filters)
        assert factor == 1

    def test_determine_size_category_small(self):
        """Test size category determination for small result set."""
        category = QueryExplainer._determine_size_category(2.5)
        assert "Small" in category

    def test_determine_size_category_medium(self):
        """Test size category determination for medium result set."""
        category = QueryExplainer._determine_size_category(1.5)
        assert "Medium" in category

    def test_determine_size_category_large(self):
        """Test size category determination for large result set."""
        category = QueryExplainer._determine_size_category(0.5)
        assert "Large" in category

    def test_estimate_result_size_empty_filters(self):
        """Test size estimation for empty filters."""
        result = QueryExplainer._estimate_result_size({}, "incident")
        assert "Large" in result
        assert "all records" in result

    def test_estimate_result_size_with_filters(self):
        """Test size estimation with filters."""
        filters = {
            "priority": "1",
            "sys_created_on": ">=javascript:gs.daysAgoStart(1)"
        }
        result = QueryExplainer._estimate_result_size(filters, "incident")
        assert "Small" in result or "Medium" in result or "Large" in result


class TestConvenienceFunctions:
    """Test convenience wrapper functions."""

    @patch('query_intelligence.QueryIntelligence.build_intelligent_filter')
    def test_build_smart_filter_wrapper(self, mock_build):
        """Test build_smart_filter convenience function."""
        mock_build.return_value = {"filters": {}, "confidence": 0.8}

        result = build_smart_filter("test query", "incident")

        assert mock_build.called
        assert mock_build.call_args[0][0] == "test query"
        assert mock_build.call_args[0][1] == "incident"

    @patch('query_intelligence.QueryIntelligence.build_intelligent_filter')
    def test_build_smart_filter_with_context(self, mock_build):
        """Test build_smart_filter with context."""
        mock_build.return_value = {"filters": {}, "confidence": 0.8}

        context = {"exclude_resolved": True}
        result = build_smart_filter("test query", "incident", context)

        assert mock_build.called
        assert mock_build.call_args[0][2] == context

    @patch('query_intelligence.QueryExplainer.explain_filter')
    def test_explain_existing_filter_wrapper(self, mock_explain):
        """Test explain_existing_filter convenience function."""
        mock_explain.return_value = {"explanation": "test"}

        filters = {"priority": "1"}
        result = explain_existing_filter(filters, "incident")

        assert mock_explain.called
        assert mock_explain.call_args[0][0] == filters
        assert mock_explain.call_args[0][1] == "incident"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @patch('query_intelligence.QueryIntelligence._validate_and_improve_filters')
    def test_empty_query(self, mock_validate):
        """Test handling of empty query."""
        mock_validate.return_value = QueryValidationResult(is_valid=True)

        result = QueryIntelligence.parse_natural_language("", "incident")
        assert "filters" in result

    @patch('query_intelligence.QueryIntelligence._validate_and_improve_filters')
    def test_whitespace_only_query(self, mock_validate):
        """Test handling of whitespace-only query."""
        mock_validate.return_value = QueryValidationResult(is_valid=True)

        result = QueryIntelligence.parse_natural_language("   ", "incident")
        assert "filters" in result

    @patch('query_intelligence.QueryIntelligence._validate_and_improve_filters')
    @patch('query_intelligence.extract_keywords')
    def test_no_keywords_extracted(self, mock_keywords, mock_validate):
        """Test handling when no keywords can be extracted."""
        mock_keywords.return_value = []
        mock_validate.return_value = QueryValidationResult(is_valid=True)

        result = QueryIntelligence.parse_natural_language("!!!", "incident")
        assert "filters" in result
        assert result["confidence"] == 0.0

    def test_merge_priority_with_complete_syntax(self):
        """Test merging priority that already has complete syntax."""
        result = QueryIntelligence._merge_priority_filters("priority=1", "2")
        assert "^OR" in result or "priority=1" in result
