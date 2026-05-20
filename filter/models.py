"""Pydantic models and result containers for the filter pipeline."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TableFilterParams(BaseModel):
    """Generic filter parameters for table queries."""

    filters: Optional[Dict[str, str]] = Field(
        None, description="Field-value pairs for filtering"
    )
    fields: Optional[List[str]] = Field(None, description="Fields to return")


class SmartQueryParams(BaseModel):
    """Parameters for intelligent (NL-parsed) queries."""

    natural_language: str = Field(
        description="Natural language description of what to find"
    )
    table_name: str = Field(description="ServiceNow table to search")
    context: Optional[Dict[str, Any]] = Field(
        None, description="Additional context for the query"
    )
    include_explanation: bool = Field(
        True, description="Whether to include explanation in results"
    )


class QueryValidationResult:
    """Container for query validation results."""

    def __init__(self, is_valid: bool = True) -> None:
        self.is_valid = is_valid
        self.warnings: List[str] = []
        self.suggestions: List[str] = []
        self.corrected_filters: Optional[Dict[str, str]] = None

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)

    def add_suggestion(self, suggestion: str) -> None:
        """Add a suggestion for improvement."""
        self.suggestions.append(suggestion)

    def has_issues(self) -> bool:
        """True if the query is invalid or has warnings."""
        return not self.is_valid or len(self.warnings) > 0
