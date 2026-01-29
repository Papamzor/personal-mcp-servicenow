"""
Date utilities for ServiceNow MCP incident queries.
Provides date validation, normalization, and helper functions for building
reliable date filters using simple comparison operators.

This module replaces JavaScript-based date filters (javascript:gs.dateGenerate())
with simple >= and <= operators that work reliably with the ServiceNow API.
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Date format patterns
DATE_FORMAT_SIMPLE = "%Y-%m-%d"
DATE_FORMAT_FULL = "%Y-%m-%d %H:%M:%S"
DATE_PATTERN_SIMPLE = r"^\d{4}-\d{2}-\d{2}$"
DATE_PATTERN_FULL = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"


def validate_date_format(date_string: str) -> Tuple[bool, Optional[str]]:
    """
    Validate date format is either "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS".

    Args:
        date_string: The date string to validate

    Returns:
        Tuple of (is_valid, error_message). error_message is None if valid.

    Examples:
        >>> validate_date_format("2026-01-28")
        (True, None)
        >>> validate_date_format("2026-01-28 14:30:00")
        (True, None)
        >>> validate_date_format("01-28-2026")
        (False, "Invalid date format. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS")
    """
    if not date_string:
        return False, "Date string cannot be empty"

    if not isinstance(date_string, str):
        return False, f"Date must be a string, got {type(date_string).__name__}"

    # Try simple format first (YYYY-MM-DD)
    if re.match(DATE_PATTERN_SIMPLE, date_string):
        try:
            datetime.strptime(date_string, DATE_FORMAT_SIMPLE)
            return True, None
        except ValueError as e:
            return False, f"Invalid date values: {e}"

    # Try full format (YYYY-MM-DD HH:MM:SS)
    if re.match(DATE_PATTERN_FULL, date_string):
        try:
            datetime.strptime(date_string, DATE_FORMAT_FULL)
            return True, None
        except ValueError as e:
            return False, f"Invalid datetime values: {e}"

    return False, "Invalid date format. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"


def normalize_date_to_full_format(date_string: str, is_end_date: bool = False) -> str:
    """
    Normalize date string to full format with time component.

    Args:
        date_string: Date in "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
        is_end_date: If True, adds 23:59:59; if False, adds 00:00:00

    Returns:
        Full datetime string "YYYY-MM-DD HH:MM:SS"

    Examples:
        >>> normalize_date_to_full_format("2026-01-28", is_end_date=False)
        '2026-01-28 00:00:00'
        >>> normalize_date_to_full_format("2026-01-28", is_end_date=True)
        '2026-01-28 23:59:59'
        >>> normalize_date_to_full_format("2026-01-28 14:30:00", is_end_date=True)
        '2026-01-28 14:30:00'
    """
    # If already in full format, return as-is
    if re.match(DATE_PATTERN_FULL, date_string):
        return date_string

    # Add appropriate time component
    time_component = "23:59:59" if is_end_date else "00:00:00"
    return f"{date_string} {time_component}"


def build_date_filter(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    date_field: str = "sys_created_on"
) -> Optional[str]:
    """
    Build ServiceNow date filter using simple >= and <= operators.

    This replaces the JavaScript-based gs.dateGenerate() approach with
    simple comparison operators that work reliably with ServiceNow API.

    Args:
        start_date: Start date in "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
        end_date: End date in "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
        date_field: The ServiceNow date field to filter on (default: sys_created_on)

    Returns:
        ServiceNow filter string or None if no dates provided

    Examples:
        >>> build_date_filter("2026-01-01", "2026-01-28")
        'sys_created_on>=2026-01-01 00:00:00^sys_created_on<=2026-01-28 23:59:59'
        >>> build_date_filter(start_date="2026-01-01")
        'sys_created_on>=2026-01-01 00:00:00'
        >>> build_date_filter(end_date="2026-01-28")
        'sys_created_on<=2026-01-28 23:59:59'
        >>> build_date_filter()
        None
    """
    if not start_date and not end_date:
        return None

    filters = []

    if start_date:
        normalized = normalize_date_to_full_format(start_date, is_end_date=False)
        filters.append(f"{date_field}>={normalized}")
        logger.debug("Built start date filter: %s>=%s", date_field, normalized)

    if end_date:
        normalized = normalize_date_to_full_format(end_date, is_end_date=True)
        filters.append(f"{date_field}<={normalized}")
        logger.debug("Built end date filter: %s<=%s", date_field, normalized)

    return "^".join(filters)


# Convenience date range calculators

def get_current_month_range() -> Tuple[str, str]:
    """
    Get start and end dates for the current calendar month.

    Returns:
        Tuple of (start_date, end_date) in "YYYY-MM-DD" format

    Example:
        >>> get_current_month_range()  # Called on Jan 15, 2026
        ('2026-01-01', '2026-01-31')
    """
    today = datetime.now()
    start = today.replace(day=1)

    # Calculate last day of current month
    if today.month == 12:
        end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

    return start.strftime(DATE_FORMAT_SIMPLE), end.strftime(DATE_FORMAT_SIMPLE)


def get_last_n_days_range(days: int) -> Tuple[str, str]:
    """
    Get start and end dates for the last N days (including today).

    Args:
        days: Number of days to look back

    Returns:
        Tuple of (start_date, end_date) in "YYYY-MM-DD" format

    Example:
        >>> get_last_n_days_range(7)  # Called on Jan 28, 2026
        ('2026-01-21', '2026-01-28')
    """
    today = datetime.now()
    start = today - timedelta(days=days)
    return start.strftime(DATE_FORMAT_SIMPLE), today.strftime(DATE_FORMAT_SIMPLE)


def get_this_week_range() -> Tuple[str, str]:
    """
    Get start (Monday) and end (Sunday) of the current week.

    Returns:
        Tuple of (start_date, end_date) in "YYYY-MM-DD" format

    Example:
        >>> get_this_week_range()  # Called on Wednesday Jan 28, 2026
        ('2026-01-26', '2026-02-01')  # Monday to Sunday
    """
    today = datetime.now()
    # weekday(): Monday = 0, Sunday = 6
    start = today - timedelta(days=today.weekday())  # Go to Monday
    end = start + timedelta(days=6)  # Go to Sunday
    return start.strftime(DATE_FORMAT_SIMPLE), end.strftime(DATE_FORMAT_SIMPLE)


def get_today_range() -> Tuple[str, str]:
    """
    Get start and end of today (same date for both).

    Returns:
        Tuple of (start_date, end_date) in "YYYY-MM-DD" format

    Example:
        >>> get_today_range()  # Called on Jan 28, 2026
        ('2026-01-28', '2026-01-28')
    """
    today = datetime.now().strftime(DATE_FORMAT_SIMPLE)
    return today, today


def get_yesterday_range() -> Tuple[str, str]:
    """
    Get start and end of yesterday (same date for both).

    Returns:
        Tuple of (start_date, end_date) in "YYYY-MM-DD" format

    Example:
        >>> get_yesterday_range()  # Called on Jan 28, 2026
        ('2026-01-27', '2026-01-27')
    """
    yesterday = (datetime.now() - timedelta(days=1)).strftime(DATE_FORMAT_SIMPLE)
    return yesterday, yesterday


def build_last_n_days_filter(
    days: int,
    date_field: str = "sys_created_on"
) -> str:
    """
    Build ServiceNow filter for records from the last N days.

    This replaces the JavaScript-based gs.daysAgo() approach with
    simple >= operators that work reliably with ServiceNow API.

    Args:
        days: Number of days to look back
        date_field: The ServiceNow date field to filter on (default: sys_created_on)

    Returns:
        ServiceNow filter string

    Examples:
        >>> build_last_n_days_filter(7)
        'sys_created_on>=2026-01-21 00:00:00'  # If today is Jan 28, 2026
        >>> build_last_n_days_filter(30, "opened_at")
        'opened_at>=2025-12-29 00:00:00'  # If today is Jan 28, 2026
    """
    start_date = (datetime.now() - timedelta(days=days)).strftime(DATE_FORMAT_SIMPLE)
    normalized = normalize_date_to_full_format(start_date, is_end_date=False)
    logger.debug("Built last %d days filter: %s>=%s", days, date_field, normalized)
    return f"{date_field}>={normalized}"
