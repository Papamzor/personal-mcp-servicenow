"""Backwards-compat shim — v4.0 moved this module's contents into ``filter/``.

Delete in v4.1 once external callers have migrated to ``from filter import ...``.
"""
# Re-export `extract_keywords` so test fixtures that patch
# `query_intelligence.extract_keywords` continue to work without
# rewriting every test against the new module path.
from utils import extract_keywords
from filter.explainer import QueryExplainer, explain_existing_filter
from filter.intelligence import (
    PRIORITY_P1_P2_OR,
    STATE_EXCLUDE_RESOLVED,
    QueryIntelligence,
    build_smart_filter,
    get_filter_templates,
)

__all__ = [
    "PRIORITY_P1_P2_OR",
    "STATE_EXCLUDE_RESOLVED",
    "QueryIntelligence",
    "QueryExplainer",
    "build_smart_filter",
    "explain_existing_filter",
    "extract_keywords",
    "get_filter_templates",
]
