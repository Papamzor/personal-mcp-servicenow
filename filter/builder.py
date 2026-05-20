"""ServiceNow query-string builder.

Static helpers that emit syntactically-correct fragments (OR filters,
date ranges, exclusion clauses) for the ServiceNow REST API.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple


class ServiceNowQueryBuilder:
    """Helper class for building ServiceNow queries with proper syntax."""

    @staticmethod
    def build_priority_or_filter(priorities: List[str]) -> str:
        """Build OR filter for multiple priorities."""
        if len(priorities) == 1:
            return priorities[0]

        # Correct ServiceNow OR syntax: priority=1^ORpriority=2
        priority_conditions = [f"priority={p}" for p in priorities]
        return "^OR".join(priority_conditions)

    @staticmethod
    def build_date_range_filter(start_date: str, end_date: str) -> str:
        """Build date range filter for ServiceNow using proper BETWEEN syntax."""
        return (
            f"sys_created_onBETWEENjavascript:gs.dateGenerate('{start_date}','00:00:00')"
            f"@javascript:gs.dateGenerate('{end_date}','23:59:59')"
        )

    @staticmethod
    def build_relative_date_filter(period: str = "Last week") -> str:
        """Build ServiceNow relative date filter with proper BETWEEN syntax."""
        period_lower = period.lower()
        if period_lower == "last week":
            return "sys_created_onBETWEENjavascript:gs.beginningOfLastWeek()@javascript:gs.endOfLastWeek()"
        if period_lower == "today":
            return "sys_created_onBETWEENjavascript:gs.beginningOfToday()@javascript:gs.endOfToday()"
        if period_lower == "last 7 days":
            return "sys_created_onBETWEENjavascript:gs.daysAgoStart(7)@javascript:gs.daysAgoEnd(1)"
        if period_lower == "this week":
            return "sys_created_onBETWEENjavascript:gs.beginningOfThisWeek()@javascript:gs.endOfThisWeek()"
        # Fallback to standard range
        return f"sys_created_on>={period}"

    @staticmethod
    def build_exclusion_filter(field: str, exclude_ids: List[str]) -> str:
        """Build exclusion filter for multiple IDs using NOT EQUALS."""
        return "^".join(f"{field}!={exc_id}" for exc_id in exclude_ids)

    @staticmethod
    def build_complete_filter(
        priorities: Optional[List[str]] = None,
        date_period: Optional[str] = None,
        date_range: Optional[Tuple[str, str]] = None,
        exclude_callers: Optional[List[str]] = None,
        additional_filters: Optional[Dict[str, str]] = None,
    ) -> str:
        """Build a complete ServiceNow filter string with proper syntax.

        Args:
            priorities: List of priorities (e.g., ['1', '2'])
            date_period: Relative period (e.g., 'last week', 'today')
            date_range: Tuple of (start_date, end_date) for specific range
            exclude_callers: List of caller sys_ids to exclude
            additional_filters: Additional field-value pairs
        """
        filter_parts: List[str] = []

        # Add date filter (specific range takes precedence)
        if date_range and len(date_range) == 2:
            start_date, end_date = date_range
            filter_parts.append(
                ServiceNowQueryBuilder.build_date_range_filter(start_date, end_date)
            )
        elif date_period:
            filter_parts.append(
                ServiceNowQueryBuilder.build_relative_date_filter(date_period)
            )

        # Add priority filter if specified
        if priorities:
            filter_parts.append(
                ServiceNowQueryBuilder.build_priority_or_filter(priorities)
            )

        # Add caller exclusion filter
        if exclude_callers:
            filter_parts.append(
                ServiceNowQueryBuilder.build_exclusion_filter("caller_id", exclude_callers)
            )

        # Add any additional filters
        if additional_filters:
            for field, value in additional_filters.items():
                if field not in ("sys_created_on", "priority", "caller_id"):
                    filter_parts.append(f"{field}={value}")

        return "^".join(filter_parts)
