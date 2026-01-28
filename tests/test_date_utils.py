"""
Tests for date utilities module.
Tests date validation, normalization, and date range helper functions.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from Table_Tools.date_utils import (
    validate_date_format,
    normalize_date_to_full_format,
    build_date_filter,
    build_last_n_days_filter,
    get_current_month_range,
    get_last_n_days_range,
    get_this_week_range,
    get_today_range,
    get_yesterday_range,
    DATE_FORMAT_SIMPLE
)


class TestValidateDateFormat:
    """Test date format validation."""

    def test_valid_simple_date(self):
        """Test valid YYYY-MM-DD format."""
        is_valid, error = validate_date_format("2026-01-28")
        assert is_valid is True
        assert error is None

    def test_valid_full_datetime(self):
        """Test valid YYYY-MM-DD HH:MM:SS format."""
        is_valid, error = validate_date_format("2026-01-28 14:30:00")
        assert is_valid is True
        assert error is None

    def test_valid_midnight(self):
        """Test valid midnight time."""
        is_valid, error = validate_date_format("2026-01-28 00:00:00")
        assert is_valid is True
        assert error is None

    def test_valid_end_of_day(self):
        """Test valid end of day time."""
        is_valid, error = validate_date_format("2026-01-28 23:59:59")
        assert is_valid is True
        assert error is None

    def test_invalid_format_mm_dd_yyyy(self):
        """Test invalid MM-DD-YYYY format."""
        is_valid, error = validate_date_format("01-28-2026")
        assert is_valid is False
        assert "Invalid date format" in error

    def test_invalid_format_slash_separator(self):
        """Test invalid format with slash separator."""
        is_valid, error = validate_date_format("2026/01/28")
        assert is_valid is False
        assert "Invalid date format" in error

    def test_invalid_empty_string(self):
        """Test empty string."""
        is_valid, error = validate_date_format("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_invalid_none_like_string(self):
        """Test None type raises appropriate error."""
        is_valid, error = validate_date_format(None)
        assert is_valid is False
        assert "string" in error.lower()

    def test_invalid_date_values_feb_30(self):
        """Test invalid date values (Feb 30)."""
        is_valid, error = validate_date_format("2026-02-30")
        assert is_valid is False
        assert "Invalid" in error

    def test_invalid_date_values_month_13(self):
        """Test invalid month (13)."""
        is_valid, error = validate_date_format("2026-13-01")
        assert is_valid is False
        assert "Invalid" in error

    def test_invalid_time_values_hour_25(self):
        """Test invalid time values (25:00:00)."""
        is_valid, error = validate_date_format("2026-01-28 25:00:00")
        assert is_valid is False

    def test_invalid_time_values_minute_60(self):
        """Test invalid time values (14:60:00)."""
        is_valid, error = validate_date_format("2026-01-28 14:60:00")
        assert is_valid is False

    def test_invalid_partial_datetime(self):
        """Test partial datetime (missing seconds)."""
        is_valid, error = validate_date_format("2026-01-28 14:30")
        assert is_valid is False
        assert "Invalid date format" in error


class TestNormalizeDateFormat:
    """Test date normalization."""

    def test_simple_date_start(self):
        """Test normalizing simple date for start (adds 00:00:00)."""
        result = normalize_date_to_full_format("2026-01-28", is_end_date=False)
        assert result == "2026-01-28 00:00:00"

    def test_simple_date_end(self):
        """Test normalizing simple date for end (adds 23:59:59)."""
        result = normalize_date_to_full_format("2026-01-28", is_end_date=True)
        assert result == "2026-01-28 23:59:59"

    def test_full_datetime_unchanged_start(self):
        """Test full datetime is unchanged for start."""
        result = normalize_date_to_full_format("2026-01-28 14:30:00", is_end_date=False)
        assert result == "2026-01-28 14:30:00"

    def test_full_datetime_unchanged_end(self):
        """Test full datetime is unchanged for end."""
        result = normalize_date_to_full_format("2026-01-28 14:30:00", is_end_date=True)
        assert result == "2026-01-28 14:30:00"

    def test_midnight_preserved(self):
        """Test midnight datetime is preserved."""
        result = normalize_date_to_full_format("2026-01-28 00:00:00", is_end_date=True)
        assert result == "2026-01-28 00:00:00"


class TestBuildDateFilter:
    """Test date filter building."""

    def test_both_dates(self):
        """Test filter with both start and end dates."""
        result = build_date_filter("2026-01-01", "2026-01-28")
        assert "sys_created_on>=2026-01-01 00:00:00" in result
        assert "sys_created_on<=2026-01-28 23:59:59" in result
        assert "^" in result

    def test_start_date_only(self):
        """Test filter with only start date."""
        result = build_date_filter(start_date="2026-01-01")
        assert result == "sys_created_on>=2026-01-01 00:00:00"

    def test_end_date_only(self):
        """Test filter with only end date."""
        result = build_date_filter(end_date="2026-01-28")
        assert result == "sys_created_on<=2026-01-28 23:59:59"

    def test_no_dates_returns_none(self):
        """Test filter with no dates returns None."""
        result = build_date_filter()
        assert result is None

    def test_both_none_returns_none(self):
        """Test filter with both None returns None."""
        result = build_date_filter(None, None)
        assert result is None

    def test_custom_date_field(self):
        """Test filter with custom date field."""
        result = build_date_filter("2026-01-01", "2026-01-28", date_field="opened_at")
        assert "opened_at>=2026-01-01 00:00:00" in result
        assert "opened_at<=2026-01-28 23:59:59" in result

    def test_full_datetime_preserved_in_filter(self):
        """Test that full datetime is preserved in filter."""
        result = build_date_filter("2026-01-01 09:00:00", "2026-01-28 17:00:00")
        assert "sys_created_on>=2026-01-01 09:00:00" in result
        assert "sys_created_on<=2026-01-28 17:00:00" in result

    def test_same_date_for_single_day(self):
        """Test same start and end date for single day query."""
        result = build_date_filter("2026-01-15", "2026-01-15")
        assert "sys_created_on>=2026-01-15 00:00:00" in result
        assert "sys_created_on<=2026-01-15 23:59:59" in result


class TestDateRangeHelpers:
    """Test convenience date range functions."""

    def test_get_current_month_range_january(self):
        """Test current month range calculation for January."""
        with patch('Table_Tools.date_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 1, 15)
            # Need to allow timedelta operations
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

            start, end = get_current_month_range()
            assert start == "2026-01-01"
            assert end == "2026-01-31"

    def test_get_current_month_range_february_non_leap(self):
        """Test current month range for February (non-leap year)."""
        with patch('Table_Tools.date_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 2, 15)
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

            start, end = get_current_month_range()
            assert start == "2025-02-01"
            assert end == "2025-02-28"

    def test_get_current_month_range_december(self):
        """Test current month range for December (year boundary)."""
        with patch('Table_Tools.date_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 12, 15)
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

            start, end = get_current_month_range()
            assert start == "2026-12-01"
            assert end == "2026-12-31"

    def test_get_last_n_days_range_7_days(self):
        """Test last 7 days range calculation."""
        with patch('Table_Tools.date_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 1, 28)

            start, end = get_last_n_days_range(7)
            assert start == "2026-01-21"
            assert end == "2026-01-28"

    def test_get_last_n_days_range_30_days(self):
        """Test last 30 days range calculation."""
        with patch('Table_Tools.date_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 1, 28)

            start, end = get_last_n_days_range(30)
            assert start == "2025-12-29"
            assert end == "2026-01-28"

    def test_get_last_n_days_range_1_day(self):
        """Test last 1 day range (yesterday and today)."""
        with patch('Table_Tools.date_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 1, 28)

            start, end = get_last_n_days_range(1)
            assert start == "2026-01-27"
            assert end == "2026-01-28"

    def test_get_this_week_range_wednesday(self):
        """Test current week range when called on Wednesday."""
        with patch('Table_Tools.date_utils.datetime') as mock_datetime:
            # January 28, 2026 is a Wednesday
            mock_datetime.now.return_value = datetime(2026, 1, 28)

            start, end = get_this_week_range()
            # Monday Jan 26 to Sunday Feb 1
            assert start == "2026-01-26"
            assert end == "2026-02-01"

    def test_get_this_week_range_monday(self):
        """Test current week range when called on Monday."""
        with patch('Table_Tools.date_utils.datetime') as mock_datetime:
            # January 26, 2026 is a Monday
            mock_datetime.now.return_value = datetime(2026, 1, 26)

            start, end = get_this_week_range()
            assert start == "2026-01-26"
            assert end == "2026-02-01"

    def test_get_this_week_range_sunday(self):
        """Test current week range when called on Sunday."""
        with patch('Table_Tools.date_utils.datetime') as mock_datetime:
            # February 1, 2026 is a Sunday
            mock_datetime.now.return_value = datetime(2026, 2, 1)

            start, end = get_this_week_range()
            assert start == "2026-01-26"
            assert end == "2026-02-01"

    def test_get_today_range(self):
        """Test today range returns same date for both."""
        with patch('Table_Tools.date_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 1, 28)

            start, end = get_today_range()
            assert start == "2026-01-28"
            assert end == "2026-01-28"

    def test_get_yesterday_range(self):
        """Test yesterday range returns previous day for both."""
        with patch('Table_Tools.date_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 1, 28)

            start, end = get_yesterday_range()
            assert start == "2026-01-27"
            assert end == "2026-01-27"

    def test_get_yesterday_range_year_boundary(self):
        """Test yesterday range across year boundary."""
        with patch('Table_Tools.date_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 1, 1)

            start, end = get_yesterday_range()
            assert start == "2025-12-31"
            assert end == "2025-12-31"


class TestDateFilterIntegration:
    """Integration tests for date filter building with validation."""

    def test_full_workflow_valid_dates(self):
        """Test complete workflow: validate -> normalize -> build filter."""
        start = "2026-01-01"
        end = "2026-01-31"

        # Validate
        is_valid_start, _ = validate_date_format(start)
        is_valid_end, _ = validate_date_format(end)
        assert is_valid_start
        assert is_valid_end

        # Build filter
        filter_str = build_date_filter(start, end)

        # Verify filter format
        assert "sys_created_on>=" in filter_str
        assert "sys_created_on<=" in filter_str
        assert "2026-01-01 00:00:00" in filter_str
        assert "2026-01-31 23:59:59" in filter_str

    def test_filter_no_javascript_syntax(self):
        """Verify filter doesn't use JavaScript syntax."""
        result = build_date_filter("2026-01-01", "2026-01-28")

        # Should NOT contain JavaScript patterns
        assert "javascript:" not in result
        assert "gs.dateGenerate" not in result
        assert "BETWEEN" not in result

        # Should contain simple operators
        assert ">=" in result
        assert "<=" in result


class TestBuildLastNDaysFilter:
    """Test build_last_n_days_filter helper function."""

    def test_default_date_field(self):
        """Test filter uses sys_created_on by default."""
        with patch('Table_Tools.date_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 1, 28)

            result = build_last_n_days_filter(7)

            assert result.startswith("sys_created_on>=")
            assert "2026-01-21 00:00:00" in result

    def test_custom_date_field(self):
        """Test filter with custom date field."""
        with patch('Table_Tools.date_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 1, 28)

            result = build_last_n_days_filter(7, date_field="opened_at")

            assert result.startswith("opened_at>=")
            assert "2026-01-21 00:00:00" in result

    def test_1_day_filter(self):
        """Test filter for last 1 day."""
        with patch('Table_Tools.date_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 1, 28)

            result = build_last_n_days_filter(1)

            assert "sys_created_on>=2026-01-27 00:00:00" == result

    def test_30_day_filter(self):
        """Test filter for last 30 days."""
        with patch('Table_Tools.date_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 1, 28)

            result = build_last_n_days_filter(30)

            assert "sys_created_on>=2025-12-29 00:00:00" == result

    def test_no_javascript_syntax(self):
        """Verify filter doesn't use JavaScript syntax."""
        with patch('Table_Tools.date_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 1, 28)

            result = build_last_n_days_filter(7)

            assert "javascript:" not in result
            assert "gs.daysAgo" not in result
            assert "gs.dateGenerate" not in result
            assert ">=" in result
