"""Pydantic models and result containers for the filter pipeline."""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class TableFilterParams(BaseModel):
    """Generic filter parameters for table queries."""

    filters: Optional[Dict[str, str]] = Field(
        None, description="Field-value pairs for filtering"
    )
    fields: Optional[List[str]] = Field(None, description="Fields to return")
    max_results: int = Field(
        100,
        description="Hard cap on rows returned. Response includes truncated=true when this cap is hit.",
        ge=1,
        le=1000,
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
