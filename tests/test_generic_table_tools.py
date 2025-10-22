"""
Comprehensive tests for generic_table_tools.py
Target: 85%+ line coverage, 70%+ branch coverage
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from typing import Dict, List, Any

from Table_Tools.generic_table_tools import (
    _validate_regex_input,
    _parse_week_format,
    _parse_month_range_format,
    _parse_iso_date_range,
    _parse_cross_month_range,
    _parse_between_format,
    _parse_year_at_end_format,
    _parse_date_range_from_text,
    _normalize_priority_value,
    _clean_priority_input,
    _process_comma_separated_priorities,
    _format_single_priority,
    _parse_priority_list,
    _parse_caller_exclusions,
    _has_operator_in_value,
    _is_complete_servicenow_filter,
    _build_query_condition,
    _build_query_string,
    _encode_query_string,
    _build_priority_filter,
    query_table_by_text,
    get_record_description,
    get_record_details,
    find_similar_records,
    query_table_with_filters,
    query_table_intelligently,
    explain_filter_query,
    build_and_validate_smart_filter,
    get_records_by_priority,
    query_table_with_generic_filters,
    TableFilterParams
)


class TestReDoSProtection:
    """Test ReDoS (Regular Expression Denial of Service) protection."""

    def test_validate_regex_input_valid_string(self):
        """Test validation accepts valid strings."""
        assert _validate_regex_input("Week 35 2025") is True
        assert _validate_regex_input("August 25-31, 2025") is True

    def test_validate_regex_input_non_string(self):
        """Test validation rejects non-strings."""
        assert _validate_regex_input(None) is False
        assert _validate_regex_input(123) is False
        assert _validate_regex_input([]) is False

    def test_validate_regex_input_too_long(self):
        """Test validation rejects overly long strings."""
        long_string = "a" * 201
        assert _validate_regex_input(long_string) is False

    def test_validate_regex_input_too_many_spaces(self):
        """Test validation rejects strings with too many spaces."""
        spaced_string = "a " * 51
        assert _validate_regex_input(spaced_string) is False

    def test_validate_regex_input_too_many_dashes(self):
        """Test validation rejects strings with too many dashes."""
        dashed_string = "a-" * 21
        assert _validate_regex_input(dashed_string) is False

    def test_validate_regex_input_edge_cases(self):
        """Test validation with edge case strings."""
        assert _validate_regex_input("") is True  # Empty is valid
        assert _validate_regex_input("a" * 200) is True  # Exactly 200 is valid
        assert _validate_regex_input("a " * 50) is True  # Exactly 50 spaces is valid


class TestDateParsing:
    """Test date parsing functions."""

    def test_parse_week_format_valid(self):
        """Test parsing valid week format."""
        result = _parse_week_format("week 35 2025")
        assert result is not None
        assert len(result) == 2
        assert result[0].startswith("2025")
        assert result[1].startswith("2025")

    def test_parse_week_format_with_of(self):
        """Test parsing 'week X of YYYY' format."""
        result = _parse_week_format("week 35 of 2025")
        assert result is not None

    def test_parse_week_format_invalid(self):
        """Test parsing invalid week format returns None."""
        assert _parse_week_format("random text") is None
        assert _parse_week_format("week") is None

    def test_parse_month_range_format_valid(self):
        """Test parsing valid month range format."""
        result = _parse_month_range_format("August 25-31, 2025")
        assert result == ("2025-08-25", "2025-08-31")

    def test_parse_month_range_format_different_months(self):
        """Test parsing month range with different month names."""
        result = _parse_month_range_format("January 1-15, 2025")
        assert result == ("2025-01-01", "2025-01-15")

    def test_parse_month_range_format_invalid_month(self):
        """Test parsing invalid month name returns None."""
        result = _parse_month_range_format("Invalidmonth 1-15, 2025")
        assert result is None

    def test_parse_iso_date_range_valid(self):
        """Test parsing ISO date range."""
        result = _parse_iso_date_range("2025-08-25 to 2025-08-31")
        assert result == ("2025-08-25", "2025-08-31")

    def test_parse_iso_date_range_invalid(self):
        """Test parsing invalid ISO format returns None."""
        assert _parse_iso_date_range("random text") is None

    def test_parse_cross_month_range_valid(self):
        """Test parsing cross-month range."""
        result = _parse_cross_month_range("August 25, 2025 to September 5, 2025")
        assert result == ("2025-08-25", "2025-09-05")

    def test_parse_cross_month_range_with_from(self):
        """Test parsing with 'from' prefix."""
        result = _parse_cross_month_range("from August 25 2025 to September 5 2025")
        assert result is not None

    def test_parse_cross_month_range_invalid_month(self):
        """Test parsing with invalid month name."""
        result = _parse_cross_month_range("Invalid 25, 2025 to September 5, 2025")
        assert result is None

    def test_parse_between_format_valid(self):
        """Test parsing 'between...and' format."""
        result = _parse_between_format("between August 25, 2025 and August 31, 2025")
        assert result == ("2025-08-25", "2025-08-31")

    def test_parse_between_format_invalid(self):
        """Test parsing invalid between format."""
        assert _parse_between_format("random text") is None

    def test_parse_year_at_end_format_valid(self):
        """Test parsing 'Month DD to Month DD YYYY' format."""
        result = _parse_year_at_end_format("August 25 to August 31, 2025")
        assert result == ("2025-08-25", "2025-08-31")

    def test_parse_year_at_end_format_with_from(self):
        """Test parsing with 'from' prefix."""
        result = _parse_year_at_end_format("from August 25 to August 31 2025")
        assert result is not None

    def test_parse_date_range_from_text_week(self):
        """Test main parser with week format."""
        result = _parse_date_range_from_text("Week 35 2025")
        assert result is not None

    def test_parse_date_range_from_text_month_range(self):
        """Test main parser with month range."""
        result = _parse_date_range_from_text("August 25-31, 2025")
        assert result == ("2025-08-25", "2025-08-31")

    def test_parse_date_range_from_text_iso(self):
        """Test main parser with ISO format."""
        result = _parse_date_range_from_text("2025-08-25 to 2025-08-31")
        assert result == ("2025-08-25", "2025-08-31")

    def test_parse_date_range_from_text_invalid_input(self):
        """Test main parser rejects invalid input."""
        assert _parse_date_range_from_text("a" * 201) is None  # Too long
        assert _parse_date_range_from_text(None) is None  # Wrong type

    def test_parse_date_range_from_text_no_match(self):
        """Test main parser returns None for non-matching text."""
        result = _parse_date_range_from_text("random text with no date")
        assert result is None


class TestPriorityParsing:
    """Test priority parsing functions."""

    def test_normalize_priority_value_p_notation(self):
        """Test normalizing P-notation."""
        assert _normalize_priority_value("P1") == "1"
        assert _normalize_priority_value("p2") == "2"
        assert _normalize_priority_value("P3") == "3"

    def test_normalize_priority_value_number(self):
        """Test normalizing plain numbers."""
        assert _normalize_priority_value("1") == "1"
        assert _normalize_priority_value("2") == "2"

    def test_clean_priority_input(self):
        """Test cleaning priority input."""
        assert _clean_priority_input('["1","2"]') == '1","2'
        assert _clean_priority_input("[1,2]") == "1,2"
        assert _clean_priority_input('"1,2"') == "1,2"

    def test_process_comma_separated_priorities(self):
        """Test processing comma-separated priorities."""
        result = _process_comma_separated_priorities("1,2,3")
        assert result == "priority=1^ORpriority=2^ORpriority=3"

    def test_process_comma_separated_priorities_p_notation(self):
        """Test processing P-notation priorities."""
        result = _process_comma_separated_priorities("P1,P2")
        assert result == "priority=1^ORpriority=2"

    def test_format_single_priority(self):
        """Test formatting single priority."""
        assert _format_single_priority("1") == "priority=1"
        assert _format_single_priority("P2") == "priority=2"

    def test_parse_priority_list_single(self):
        """Test parsing single priority."""
        assert _parse_priority_list("1") == "priority=1"

    def test_parse_priority_list_comma_separated(self):
        """Test parsing comma-separated priorities."""
        result = _parse_priority_list("1,2")
        assert "priority=1" in result
        assert "priority=2" in result
        assert "^OR" in result

    def test_parse_priority_list_already_formatted(self):
        """Test parsing already formatted priority."""
        formatted = "priority=1^ORpriority=2"
        assert _parse_priority_list(formatted) == formatted

    def test_parse_priority_list_empty(self):
        """Test parsing empty priority."""
        assert _parse_priority_list("") == ""
        assert _parse_priority_list(None) == ""


class TestCallerExclusions:
    """Test caller exclusion parsing."""

    def test_parse_caller_exclusions_known_caller(self):
        """Test parsing known caller (logicmonitor)."""
        result = _parse_caller_exclusions("logicmonitor")
        assert result == "caller_id!=1727339e47d99190c43d3171e36d43ad"

    def test_parse_caller_exclusions_single_sys_id(self):
        """Test parsing single sys_id."""
        result = _parse_caller_exclusions("test_sys_id")
        assert result == "caller_id!=test_sys_id"

    def test_parse_caller_exclusions_comma_separated(self):
        """Test parsing comma-separated sys_ids."""
        result = _parse_caller_exclusions("sys_id1,sys_id2")
        assert "caller_id!=sys_id1" in result
        assert "caller_id!=sys_id2" in result

    def test_parse_caller_exclusions_already_formatted(self):
        """Test parsing already formatted exclusion."""
        formatted = "caller_id!=test_sys_id"
        assert _parse_caller_exclusions(formatted) == formatted

    def test_parse_caller_exclusions_empty(self):
        """Test parsing empty input."""
        assert _parse_caller_exclusions("") == ""
        assert _parse_caller_exclusions(None) == ""


class TestQueryBuilding:
    """Test query building functions."""

    def test_has_operator_in_value_true(self):
        """Test detecting operators in value."""
        assert _has_operator_in_value(">=2024-01-01") is True
        assert _has_operator_in_value("<=2024-12-31") is True
        assert _has_operator_in_value(">100") is True

    def test_has_operator_in_value_false(self):
        """Test non-operator values."""
        assert _has_operator_in_value("2024-01-01") is False
        assert _has_operator_in_value("100") is False

    def test_is_complete_servicenow_filter_true(self):
        """Test detecting complete ServiceNow filters."""
        assert _is_complete_servicenow_filter("priority=1^ORpriority=2") is True
        assert _is_complete_servicenow_filter("sys_created_onONLast week") is True

    def test_is_complete_servicenow_filter_false(self):
        """Test non-complete filters."""
        assert _is_complete_servicenow_filter("priority=1") is False
        assert _is_complete_servicenow_filter("1,2") is False

    def test_build_query_condition_complete_query(self):
        """Test building complete query condition."""
        result = _build_query_condition("_complete_query", "priority=1^state=2")
        assert result == "priority=1^state=2"

    def test_build_query_condition_priority(self):
        """Test building priority condition."""
        result = _build_query_condition("priority", "1,2")
        assert "priority=1" in result
        assert "^OR" in result

    def test_build_query_condition_date_range(self):
        """Test building date range condition."""
        result = _build_query_condition("sys_created_on", "Week 35 2025")
        assert "BETWEEN" in result
        assert "javascript" in result

    def test_build_query_condition_exact_match(self):
        """Test building exact match condition."""
        result = _build_query_condition("state", "New")
        assert result == "state=New"

    def test_build_query_string_multiple_filters(self):
        """Test building complete query string."""
        filters = {"priority": "1", "state": "New"}
        result = _build_query_string(filters)
        assert "priority=1" in result
        assert "state=New" in result
        assert "^" in result

    def test_build_query_string_empty(self):
        """Test building query from empty filters."""
        assert _build_query_string({}) == ""

    def test_encode_query_string(self):
        """Test URL encoding while preserving ServiceNow syntax."""
        query = "priority=1^ORpriority=2"
        encoded = _encode_query_string(query)
        # Should preserve =, ^, and OR characters
        assert "=" in encoded
        assert "^" in encoded

    def test_build_priority_filter_single(self):
        """Test building priority filter with single priority."""
        result = _build_priority_filter(["1"])
        assert result == "priority=1"

    def test_build_priority_filter_multiple(self):
        """Test building priority filter with multiple priorities."""
        result = _build_priority_filter(["1", "2", "3"])
        assert result == "priority=1^ORpriority=2^ORpriority=3"

    def test_build_priority_filter_empty(self):
        """Test building priority filter with empty list."""
        assert _build_priority_filter([]) == ""


class TestTableFilterParams:
    """Test TableFilterParams model."""

    def test_table_filter_params_with_filters(self):
        """Test creating params with filters."""
        params = TableFilterParams(filters={"priority": "1"})
        assert params.filters == {"priority": "1"}
        assert params.fields is None

    def test_table_filter_params_with_fields(self):
        """Test creating params with fields."""
        params = TableFilterParams(fields=["number", "short_description"])
        assert params.fields == ["number", "short_description"]
        assert params.filters is None

    def test_table_filter_params_empty(self):
        """Test creating empty params."""
        params = TableFilterParams()
        assert params.filters is None
        assert params.fields is None


class TestAsyncTableOperations:
    """Test async table operation functions."""

    @pytest.mark.asyncio
    async def test_query_table_by_text_with_results(self):
        """Test querying table by text with results."""
        with patch("Table_Tools.generic_table_tools.extract_keywords") as mock_keywords, \
             patch("Table_Tools.generic_table_tools._make_paginated_request") as mock_request:

            mock_keywords.return_value = ["database"]
            mock_request.return_value = [{"number": "INC001", "short_description": "Database issue"}]

            result = await query_table_by_text("incident", "database server issue")

            assert result["result"] is not None
            assert len(result["result"]) > 0
            assert "Found" in result["message"]

    @pytest.mark.asyncio
    async def test_query_table_by_text_no_results(self):
        """Test querying table by text with no results."""
        with patch("Table_Tools.generic_table_tools.extract_keywords") as mock_keywords, \
             patch("Table_Tools.generic_table_tools._make_paginated_request") as mock_request:

            mock_keywords.return_value = ["nonexistent"]
            mock_request.return_value = []

            result = await query_table_by_text("incident", "nonexistent keyword")

            assert result["result"] == []
            assert "message" in result

    @pytest.mark.asyncio
    async def test_get_record_description_success(self):
        """Test getting record description successfully."""
        with patch("Table_Tools.generic_table_tools.make_nws_request") as mock_request:
            mock_request.return_value = {
                "result": [{"short_description": "Test description"}]
            }

            result = await get_record_description("incident", "INC001")

            assert result is not None
            assert "result" in result

    @pytest.mark.asyncio
    async def test_get_record_description_not_found(self):
        """Test getting record description when not found."""
        with patch("Table_Tools.generic_table_tools.make_nws_request") as mock_request:
            mock_request.return_value = None

            result = await get_record_description("incident", "INC999")

            assert result["result"] == []
            assert "message" in result

    @pytest.mark.asyncio
    async def test_get_record_details_success(self):
        """Test getting record details successfully."""
        with patch("Table_Tools.generic_table_tools.make_nws_request") as mock_request:
            mock_request.return_value = {
                "result": [{"number": "INC001", "short_description": "Test"}]
            }

            result = await get_record_details("incident", "INC001")

            assert result is not None
            assert "result" in result

    @pytest.mark.asyncio
    async def test_find_similar_records_success(self):
        """Test finding similar records successfully."""
        with patch("Table_Tools.generic_table_tools.get_record_description") as mock_desc, \
             patch("Table_Tools.generic_table_tools.query_table_by_text") as mock_query:

            mock_desc.return_value = {"result": [{"short_description": "Database issue"}]}
            mock_query.return_value = {
                "result": [
                    {"number": "INC001", "short_description": "Database issue"},
                    {"number": "INC002", "short_description": "Database problem"}
                ]
            }

            result = await find_similar_records("incident", "INC001")

            assert "result" in result
            # Should filter out the original record
            assert all(r["number"] != "INC001" for r in result["result"])

    @pytest.mark.asyncio
    async def test_find_similar_records_no_description(self):
        """Test finding similar records when no description found."""
        with patch("Table_Tools.generic_table_tools.get_record_description") as mock_desc:
            mock_desc.return_value = {"result": []}

            result = await find_similar_records("incident", "INC999")

            assert result["result"] == []
            assert "message" in result

    @pytest.mark.asyncio
    async def test_query_table_with_filters_success(self):
        """Test querying table with filters."""
        with patch("Table_Tools.generic_table_tools._make_paginated_request") as mock_request, \
             patch("Table_Tools.generic_table_tools.validate_query_filters") as mock_validate, \
             patch("Table_Tools.generic_table_tools.validate_result_count") as mock_count:

            mock_request.return_value = [{"number": "INC001"}]
            mock_validate.return_value = MagicMock(has_issues=lambda: False)
            mock_count.return_value = MagicMock(has_issues=lambda: False)

            params = TableFilterParams(filters={"priority": "1"})
            result = await query_table_with_filters("incident", params)

            assert "result" in result
            assert len(result["result"]) > 0

    @pytest.mark.asyncio
    async def test_query_table_with_filters_no_results(self):
        """Test querying table with filters returning no results."""
        with patch("Table_Tools.generic_table_tools._make_paginated_request") as mock_request:
            mock_request.return_value = []

            params = TableFilterParams(filters={"priority": "99"})
            result = await query_table_with_filters("incident", params)

            assert result["result"] == []
            assert "message" in result

    @pytest.mark.asyncio
    async def test_get_records_by_priority_success(self):
        """Test getting records by priority."""
        with patch("Table_Tools.generic_table_tools._make_paginated_request") as mock_request:
            mock_request.return_value = [{"number": "INC001", "priority": "1"}]

            result = await get_records_by_priority("incident", ["1", "2"])

            assert "result" in result
            assert len(result["result"]) > 0

    @pytest.mark.asyncio
    async def test_get_records_by_priority_unsupported_table(self):
        """Test getting records by priority for unsupported table."""
        result = await get_records_by_priority("unknown_table", ["1"])

        assert "error" in result

    @pytest.mark.asyncio
    async def test_query_table_with_generic_filters_success(self):
        """Test generic filter querying."""
        with patch("Table_Tools.generic_table_tools._make_paginated_request") as mock_request:
            mock_request.return_value = [{"number": "INC001"}]

            result = await query_table_with_generic_filters(
                "incident",
                {"state": "New", "priority": "1"}
            )

            assert "result" in result
            assert len(result["result"]) > 0


class TestIntelligentQueries:
    """Test intelligent query functions."""

    @pytest.mark.asyncio
    async def test_query_table_intelligently_with_results(self):
        """Test intelligent querying with results."""
        with patch("Table_Tools.generic_table_tools.build_smart_filter") as mock_smart, \
             patch("Table_Tools.generic_table_tools.query_table_with_filters") as mock_query:

            mock_smart.return_value = {
                "filters": {"priority": "priority=1"},
                "explanation": "Test",
                "confidence": 0.8,
                "suggestions": []
            }
            mock_query.return_value = {"result": [{"number": "INC001"}]}

            result = await query_table_intelligently(
                "incident",
                "critical incidents from yesterday"
            )

            assert "result" in result
            assert "intelligence" in result

    @pytest.mark.asyncio
    async def test_query_table_intelligently_fallback(self):
        """Test intelligent querying with fallback to text search."""
        with patch("Table_Tools.generic_table_tools.build_smart_filter") as mock_smart, \
             patch("Table_Tools.generic_table_tools.query_table_by_text") as mock_text:

            mock_smart.return_value = {
                "filters": {},
                "explanation": "Test",
                "confidence": 0.3,
                "suggestions": []
            }
            mock_text.return_value = {"result": [{"number": "INC001"}]}

            result = await query_table_intelligently(
                "incident",
                "database issues"
            )

            assert "intelligence" in result
            assert "fallback" in result["intelligence"]["explanation"].lower()

    def test_explain_filter_query(self):
        """Test explaining filter query."""
        with patch("Table_Tools.generic_table_tools.explain_existing_filter") as mock_explain:
            mock_explain.return_value = {
                "explanation": "Test explanation",
                "sql_equivalent": "SELECT * FROM incident",
                "potential_issues": [],
                "suggestions": [],
                "estimated_result_size": "Medium"
            }

            result = explain_filter_query("incident", {"priority": "1"})

            assert "explanation" in result
            assert "filter_analysis" in result

    def test_build_and_validate_smart_filter_with_filters(self):
        """Test building and validating smart filter."""
        with patch("Table_Tools.generic_table_tools.build_smart_filter") as mock_smart, \
             patch("Table_Tools.generic_table_tools.validate_query_filters") as mock_validate:

            mock_smart.return_value = {
                "filters": {"priority": "1"},
                "explanation": "Test",
                "confidence": 0.8,
                "suggestions": []
            }
            mock_validate.return_value = MagicMock(
                is_valid=True,
                warnings=[],
                suggestions=[]
            )

            result = build_and_validate_smart_filter(
                "critical incidents",
                "incident"
            )

            assert "filters" in result
            assert "validation" in result

    def test_build_and_validate_smart_filter_no_filters(self):
        """Test building smart filter when no filters generated."""
        with patch("Table_Tools.generic_table_tools.build_smart_filter") as mock_smart:
            mock_smart.return_value = {
                "filters": {},
                "explanation": "Test",
                "confidence": 0.1,
                "suggestions": []
            }

            result = build_and_validate_smart_filter(
                "random text",
                "incident"
            )

            assert result["filters"] == {}
            assert result["validation"]["is_valid"] is False


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_parse_priority_list_special_characters(self):
        """Test priority parsing with special characters."""
        result = _parse_priority_list('["1", "2", "3"]')
        assert "priority=1" in result
        assert "^OR" in result

    def test_build_query_condition_suffix_operators(self):
        """Test building query with suffix operators."""
        result = _build_query_condition("sys_created_on_gte", "2024-01-01")
        assert ">=" in result
        assert "sys_created_on" in result

    def test_encode_query_string_preserves_servicenow_syntax(self):
        """Test that encoding preserves important ServiceNow characters."""
        query = "priority=1^ORpriority=2@javascript:gs.dateGenerate()"
        encoded = _encode_query_string(query)

        # These characters must be preserved
        assert "=" in encoded
        assert "^" in encoded
        assert "@" in encoded
        assert "(" in encoded
        assert ")" in encoded

    @pytest.mark.asyncio
    async def test_find_similar_records_exception_handling(self):
        """Test exception handling in find_similar_records."""
        with patch("Table_Tools.generic_table_tools.get_record_description") as mock_desc:
            mock_desc.side_effect = Exception("Test error")

            result = await find_similar_records("incident", "INC001")

            assert result["result"] == []
            assert "message" in result

    @pytest.mark.asyncio
    async def test_get_records_by_priority_with_additional_filters(self):
        """Test getting records by priority with additional filters."""
        with patch("Table_Tools.generic_table_tools._make_paginated_request") as mock_request:
            mock_request.return_value = [{"number": "INC001", "priority": "1", "state": "New"}]

            result = await get_records_by_priority(
                "incident",
                ["1"],
                additional_filters={"state": "New"}
            )

            assert "result" in result

    @pytest.mark.asyncio
    async def test_get_records_by_priority_exception_handling(self):
        """Test exception handling in get_records_by_priority."""
        with patch("Table_Tools.generic_table_tools._make_paginated_request") as mock_request:
            mock_request.side_effect = Exception("Test error")

            result = await get_records_by_priority("incident", ["1"])

            assert "error" in result

    @pytest.mark.asyncio
    async def test_query_table_with_generic_filters_exception_handling(self):
        """Test exception handling in query_table_with_generic_filters."""
        with patch("Table_Tools.generic_table_tools._make_paginated_request") as mock_request:
            mock_request.side_effect = Exception("Test error")

            result = await query_table_with_generic_filters("incident", {"priority": "1"})

            assert "error" in result
