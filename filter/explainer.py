"""Filter explanation + result-size estimation.

Wraps QueryIntelligence's explanation generators with additional issue
analysis suitable for surfacing to end-users.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from filter.intelligence import QueryIntelligence


class QueryExplainer:
    """Explains existing filters and suggests improvements."""

    @classmethod
    def _check_priority_filter_issue(
        cls, field: str, value: str
    ) -> Optional[Tuple[str, str]]:
        """Return (issue, suggestion) if the priority filter has comma syntax."""
        if field == "priority" and "," in value and "^OR" not in value:
            return (
                "Priority filter may not work - comma separation doesn't work in ServiceNow",
                f"Use OR syntax: {QueryIntelligence.PRIORITY_P1_P2_OR}",
            )
        return None

    @classmethod
    def _check_date_filter_issue(
        cls, field: str, value: str
    ) -> Optional[Tuple[str, str]]:
        """Return (issue, suggestion) if the date filter is open-ended."""
        if field == "sys_created_on" and ">=" in value and "<=" not in value:
            return (
                "Date range incomplete - may return more results than expected",
                "Add end date for complete range",
            )
        return None

    @classmethod
    def _analyze_filter_issues(
        cls, filters: Dict[str, str]
    ) -> Tuple[List[str], List[str]]:
        """Return (issues, suggestions) for the given filter dict."""
        issues: List[str] = []
        suggestions: List[str] = []

        for field, value in filters.items():
            priority_issue = cls._check_priority_filter_issue(field, value)
            if priority_issue:
                issues.append(priority_issue[0])
                suggestions.append(priority_issue[1])

            date_issue = cls._check_date_filter_issue(field, value)
            if date_issue:
                issues.append(date_issue[0])
                suggestions.append(date_issue[1])

        return (issues, suggestions)

    @classmethod
    def explain_filter(cls, filters: Dict[str, str], table_name: str) -> Dict[str, Any]:
        """Explain what an existing filter does and suggest improvements."""
        explanation = QueryIntelligence._generate_filter_explanation(filters, table_name)
        sql_equivalent = QueryIntelligence._generate_sql_equivalent(filters, table_name)

        issues, suggestions = cls._analyze_filter_issues(filters)

        return {
            "explanation": explanation,
            "sql_equivalent": sql_equivalent,
            "potential_issues": issues,
            "suggestions": suggestions,
            "estimated_result_size": cls._estimate_result_size(filters, table_name),
        }

    @classmethod
    def _calculate_priority_factor(cls, filters: Dict[str, str]) -> float:
        """Calculate priority contribution to size factor."""
        if "priority" not in filters:
            return 0.0

        factor = 0.0
        if "1" in filters["priority"]:
            factor += 1  # P1 incidents are rare

        if "^OR" in filters.get("priority", ""):
            factor -= 0.5  # OR expands results

        return factor

    @classmethod
    def _calculate_date_factor(cls, filters: Dict[str, str]) -> float:
        """Calculate date contribution to size factor."""
        if "sys_created_on" not in filters:
            return 0.0

        if "daysAgoStart(1)" in filters["sys_created_on"]:
            return 2  # Today only - very small
        if "daysAgoStart(7)" in filters["sys_created_on"]:
            return 1  # Last week - small

        return 0.0

    @classmethod
    def _determine_size_category(cls, size_factors: float) -> str:
        """Determine size category from factors."""
        if size_factors >= 2:
            return "Small (< 50 records)"
        if size_factors >= 1:
            return "Medium (50-200 records)"
        return "Large (> 200 records)"

    @classmethod
    def _estimate_result_size(
        cls, filters: Dict[str, str], table_name: str
    ) -> str:
        """Provide rough estimate of expected result size."""
        if not filters:
            return "Large (all records)"

        priority_factor = cls._calculate_priority_factor(filters)
        date_factor = cls._calculate_date_factor(filters)
        total_factors = priority_factor + date_factor

        return cls._determine_size_category(total_factors)


def explain_existing_filter(
    filters: Dict[str, str], table: str = "incident"
) -> Dict[str, Any]:
    """Explain what an existing filter does."""
    return QueryExplainer.explain_filter(filters, table)
