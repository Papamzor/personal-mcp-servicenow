"""Natural-language to ServiceNow filter conversion.

Pure NL parsing — does not depend on the builder layer. Auto-correction
of parsed filters is delegated to `filter.validator.validate_and_correct_filters`,
which is the only module allowed to bridge into the builder.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from utils import extract_keywords
from filter.models import QueryValidationResult
from filter.validator import validate_and_correct_filters


# Constants for commonly used filter values, exposed at module scope so the
# QueryIntelligence class can reference them inside its FILTER_TEMPLATES dict
# (a class-body f-string cannot see other class attributes).
PRIORITY_P1_P2_OR = "priority=1^ORpriority=2"
STATE_EXCLUDE_RESOLVED = "state!=6^state!=7^state!=8"


class QueryIntelligence:
    """Smart query building and validation for ServiceNow filters."""

    PRIORITY_P1_P2_OR = PRIORITY_P1_P2_OR
    STATE_EXCLUDE_RESOLVED = STATE_EXCLUDE_RESOLVED

    # Common filter templates for frequent scenarios
    FILTER_TEMPLATES = {
        "high_priority_last_week": {
            "_complete_query": (
                "sys_created_onONLast week"
                "@javascript:gs.beginningOfLastWeek()"
                "@javascript:gs.endOfLastWeek()"
                f"^{PRIORITY_P1_P2_OR}"
            )
        },
        "critical_recent": {
            "priority": "1",
            "sys_created_on": ">=javascript:gs.daysAgoStart(7)",
        },
        "unassigned_recent": {
            "assigned_to": "NULL",
            "sys_created_on": ">=javascript:gs.daysAgoStart(3)",
        },
        "resolved_this_month": {
            "state": "6",
            "sys_created_on": ">=javascript:gs.beginningOfThisMonth()",
        },
        "active_p1_p2": {
            "priority": PRIORITY_P1_P2_OR,
            "state": STATE_EXCLUDE_RESOLVED,
        },
        "p1_p2_all_states": {
            "priority": PRIORITY_P1_P2_OR,
        },
    }

    # Natural language patterns and their ServiceNow equivalents
    LANGUAGE_PATTERNS = {
        # Priority patterns
        r"\b(critical|p1|priority\s*1|urgent)\b": {"priority": "1"},
        r"\b(high|p2|priority\s*2|important)\b": {"priority": "2"},
        r"\b(medium|p3|priority\s*3|normal)\b": {"priority": "3"},
        r"\b(low|p4|priority\s*4)\b": {"priority": "4"},
        r"\b(p1\s*and\s*p2|high\s*priority|critical\s*and\s*high)\b": {"priority": PRIORITY_P1_P2_OR},
        # Time patterns
        r"\b(last\s*week|past\s*week)\b": {"sys_created_on": ">=javascript:gs.beginningOfLastWeek()^<=javascript:gs.endOfLastWeek()"},
        r"\b(this\s*week|current\s*week)\b": {"sys_created_on": ">=javascript:gs.beginningOfThisWeek()"},
        r"\b(today|today's)\b": {"sys_created_on": ">=javascript:gs.beginningOfToday()"},
        r"\b(yesterday)\b": {"sys_created_on": ">=javascript:gs.yesterdayStart()^<=javascript:gs.yesterdayEnd()"},
        r"\b(last\s*(\d+)\s*days?)\b": lambda m: {"sys_created_on": f">=javascript:gs.daysAgoStart({m.group(2)})"},
        r"\b(past\s*month|last\s*month)\b": {"sys_created_on": ">=javascript:gs.beginningOfLastMonth()^<=javascript:gs.endOfLastMonth()"},
        r"\b(this\s*month|current\s*month)\b": {"sys_created_on": ">=javascript:gs.beginningOfThisMonth()"},
        # State patterns
        r"\b(new|open|active)\b": {"state": "state=1^ORstate=2^ORstate=3"},
        r"\b(resolved|closed|completed)\b": {"state": "6"},
        r"\b(in\s*progress|working)\b": {"state": "2"},
        r"\b(pending|waiting)\b": {"state": "10"},
        r"\b(cancelled|canceled)\b": {"state": "8"},
        # Assignment patterns
        r"\b(unassigned|not\s*assigned|no\s*assignee)\b": {"assigned_to": "NULL"},
        r"\b(assigned\s*to\s*me|my\s*tickets|my\s*incidents)\b": {"assigned_to": "javascript:gs.getUserID()"},
    }

    @classmethod
    def _handle_exclusion_filter(cls, field: str, value: str) -> Dict[str, str]:
        """Handle exclusion filters with intelligent name-to-ID mapping."""
        field_mapping = {
            "caller": "caller_id",
            "reporter": "caller_id",
            "assignee": "assigned_to",
            "user": "caller_id",
        }

        servicenow_field = field_mapping.get(field.lower(), field)

        known_entities = {
            "logicmonitor integration": "1727339e47d99190c43d3171e36d43ad",
            "logicmonitor": "1727339e47d99190c43d3171e36d43ad",
        }

        value_lower = value.lower().strip()
        if value_lower in known_entities:
            entity_id = known_entities[value_lower]
            return {"_complete_caller_exclusion": f"{servicenow_field}!={entity_id}"}
        return {servicenow_field: f"!={value}"}

    @classmethod
    def _try_template_match(cls, query_lower: str) -> Optional[Dict[str, Any]]:
        """Check for template match and return template data."""
        template_match = cls._match_filter_template(query_lower)
        if not template_match:
            return None

        return {
            "filters": template_match["filters"].copy(),
            "template_name": template_match["name"],
            "confidence": 0.9,
            "explanation": f"Used predefined template: {template_match['name']}",
        }

    @classmethod
    def _parse_language_patterns(
        cls, query_lower: str, parsed_filters: Dict
    ) -> Tuple[float, List[str]]:
        """Parse language patterns and update filters."""
        confidence_score = 0.0
        explanations: List[str] = []

        for pattern, filter_data in cls.LANGUAGE_PATTERNS.items():
            matches = re.finditer(pattern, query_lower, re.IGNORECASE)
            for match in matches:
                dynamic_filters = filter_data(match) if callable(filter_data) else filter_data

                for key, value in dynamic_filters.items():
                    if key == "priority" and key in parsed_filters:
                        parsed_filters[key] = cls._merge_priority_filters(
                            parsed_filters[key], value
                        )
                    else:
                        parsed_filters[key] = value

                confidence_score += 0.2
                explanations.append(f"Detected '{match.group()}' -> {filter_data}")

        return (confidence_score, explanations)

    @classmethod
    def _merge_priority_filters(cls, existing: str, new_value: str) -> str:
        """Merge two priority values with OR syntax."""
        existing_num = existing.split("=")[-1] if "=" in existing else existing
        new_num = new_value

        if existing_num == new_num:
            return existing

        if "^OR" not in existing:
            return f"priority={existing_num}^ORpriority={new_num}"
        if f"priority={new_num}" not in existing:
            return existing + f"^ORpriority={new_num}"

        return existing

    @classmethod
    def _parse_exclusion_patterns(cls, query_lower: str) -> Optional[Dict[str, Any]]:
        """Parse exclusion patterns and return exclusion filters."""
        exclusion_pattern = r"\b(exclud(?:e|ing)|not|without)\s+(caller|reporter|assignee|user)\s+([\w\s]+)"
        exclusion_match = re.search(exclusion_pattern, query_lower, re.IGNORECASE)

        if not exclusion_match:
            return None

        field = exclusion_match.group(2)
        value = exclusion_match.group(3).strip()

        stop_words = [
            "from", "in", "on", "incidents", "incident", "tickets", "ticket",
            "and", "or", "between", "created", "with",
        ]

        for stop_word in stop_words:
            if " " + stop_word + " " in " " + value.lower() + " ":
                value = value.lower().split(stop_word)[0].strip()
                break

        exclusion_filters = cls._handle_exclusion_filter(field, value)

        return {
            "filters": exclusion_filters,
            "confidence": 0.2,
            "explanation": f"Detected exclusion: {field} != {value}",
        }

    @classmethod
    def _try_date_range_parsing(
        cls, query_lower: str, existing_filters: Dict
    ) -> Optional[Dict[str, Any]]:
        """Try to parse date range from query."""
        if "sys_created_on" in existing_filters:
            return None

        # Late import to avoid a circular dependency: generic_table_tools
        # imports from filter.* during module init.
        from Table_Tools.generic_table_tools import _parse_date_range_from_text

        date_range = _parse_date_range_from_text(query_lower)
        if not date_range:
            return None

        start_date, end_date = date_range
        date_filter = (
            f"sys_created_onBETWEENjavascript:gs.dateGenerate('{start_date}','00:00:00')"
            f"@javascript:gs.dateGenerate('{end_date}','23:59:59')"
        )

        return {
            "filter": {"sys_created_on": date_filter},
            "confidence": 0.3,
            "explanation": f"Detected date range: {start_date} to {end_date}",
        }

    @classmethod
    def _build_keyword_fallback(cls, query_text: str) -> Dict[str, Any]:
        """Build keyword-based fallback filter."""
        keywords = extract_keywords(query_text)
        if not keywords:
            return {"filters": {}, "confidence": 0.0, "explanation": ""}

        return {
            "filters": {"short_description": f"short_descriptionCONTAINS{keywords[0]}"},
            "confidence": 0.5,
            "explanation": f"Using keyword search for: {keywords[0]}",
        }

    @classmethod
    def parse_natural_language(
        cls, query_text: str, table_name: str = "incident"
    ) -> Dict[str, Any]:
        """Parse natural language query into ServiceNow filters with intelligence."""
        result: Dict[str, Any] = {
            "filters": {},
            "explanation": "",
            "confidence": 0.0,
            "suggestions": [],
            "template_used": None,
        }

        query_lower = query_text.lower().strip()
        explanations: List[str] = []
        confidence_score = 0.0

        template_data = cls._try_template_match(query_lower)
        if template_data:
            parsed_filters = template_data["filters"]
            result["template_used"] = template_data["template_name"]
            confidence_score = template_data["confidence"]
            explanations.append(template_data["explanation"])
        else:
            parsed_filters = {}
            pattern_confidence, pattern_explanations = cls._parse_language_patterns(
                query_lower, parsed_filters
            )
            confidence_score += pattern_confidence
            explanations.extend(pattern_explanations)

        exclusion_data = cls._parse_exclusion_patterns(query_lower)
        if exclusion_data:
            parsed_filters.update(exclusion_data["filters"])
            confidence_score += exclusion_data["confidence"]
            explanations.append(exclusion_data["explanation"])

        date_data = cls._try_date_range_parsing(query_lower, parsed_filters)
        if date_data:
            parsed_filters.update(date_data["filter"])
            confidence_score += date_data["confidence"]
            explanations.append(date_data["explanation"])

        if not parsed_filters:
            keyword_data = cls._build_keyword_fallback(query_text)
            parsed_filters = keyword_data["filters"]
            confidence_score = keyword_data["confidence"]
            if keyword_data["explanation"]:
                explanations.append(keyword_data["explanation"])

        # Delegate validation + auto-correction to the validator module so
        # intelligence stays free of any reference to the builder layer.
        validation_result = cls._validate_and_improve_filters(parsed_filters, table_name)
        if validation_result.corrected_filters:
            parsed_filters = validation_result.corrected_filters
            explanations.extend(validation_result.suggestions)

        result["filters"] = parsed_filters
        result["confidence"] = min(confidence_score, 1.0)
        result["explanation"] = " | ".join(explanations)
        result["suggestions"] = validation_result.suggestions

        return result

    @classmethod
    def _match_filter_template(cls, query_text: str) -> Optional[Dict[str, Any]]:
        """Check if query matches a predefined template."""
        template_patterns = {
            r"(high\s*priority|critical|p1\s*p2).*(last\s*week|past\s*week)": "high_priority_last_week",
            r"(critical|p1).*(recent|today|yesterday|days?)": "critical_recent",
            r"(unassigned|no\s*assignee).*(recent|today|days?)": "unassigned_recent",
            r"(resolved|closed).*(this\s*month|month)": "resolved_this_month",
            r"(active|open).*(critical|high|p1|p2)": "active_p1_p2",
            r"\b(p1\s*and\s*p2|p1\s*p2)\b": "p1_p2_all_states",
        }

        for pattern, template_name in template_patterns.items():
            if re.search(pattern, query_text, re.IGNORECASE):
                return {
                    "name": template_name,
                    "filters": cls.FILTER_TEMPLATES[template_name].copy(),
                }

        return None

    @classmethod
    def _validate_and_improve_filters(
        cls, filters: Dict[str, str], table_name: str
    ) -> QueryValidationResult:
        """Delegate validation + auto-correction to the validator module.

        Kept as a classmethod for backwards compatibility with anything that
        patched it on `QueryIntelligence` previously. The actual logic now
        lives in `filter.validator.validate_and_correct_filters`.
        """
        return validate_and_correct_filters(filters)

    @classmethod
    def build_intelligent_filter(
        cls,
        natural_language: str,
        table_name: str,
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Main entry point for intelligent filter building."""
        parsed_result = cls.parse_natural_language(natural_language, table_name)

        if context:
            parsed_result["filters"].update(cls._apply_context_filters(context, table_name))

        explanation = cls._generate_filter_explanation(parsed_result["filters"], table_name)

        return {
            "filters": parsed_result["filters"],
            "explanation": explanation,
            "confidence": parsed_result["confidence"],
            "suggestions": parsed_result["suggestions"],
            "template_used": parsed_result.get("template_used"),
            "sql_equivalent": cls._generate_sql_equivalent(parsed_result["filters"], table_name),
        }

    @classmethod
    def _apply_context_filters(cls, context: Dict, table_name: str) -> Dict[str, str]:
        """Apply context-based filters (e.g., user preferences, previous queries)."""
        context_filters: Dict[str, str] = {}

        if context.get("date_range"):
            date_range = context["date_range"]
            if "start" in date_range and "end" in date_range:
                context_filters["sys_created_on"] = (
                    f"sys_created_onBETWEENjavascript:gs.dateGenerate('{date_range['start']}','00:00:00')"
                    f"@javascript:gs.dateGenerate('{date_range['end']}','23:59:59')"
                )

        if context.get("exclude_caller"):
            caller = context["exclude_caller"]
            if isinstance(caller, list):
                exclusions = [f"caller_id!={c}" for c in caller]
                context_filters["_complete_caller_exclusion"] = "^".join(exclusions)
            else:
                context_filters["_complete_caller_exclusion"] = f"caller_id!={caller}"

        if context.get("exclude_resolved") is True:
            context_filters["state"] = cls.STATE_EXCLUDE_RESOLVED

        if context.get("user_assigned_only"):
            context_filters["assigned_to"] = "javascript:gs.getUserID()"

        return context_filters

    @classmethod
    def _explain_priority_filter(cls, value: str) -> str:
        """Generate explanation for priority filter."""
        if "^OR" in value:
            priorities = re.findall(r"priority=(\d+)", value)
            return f"Priority levels: {', '.join(priorities)}"
        return f"Priority: {value}"

    @classmethod
    def _explain_date_filter(cls, value: str) -> str:
        """Generate explanation for date-related filters."""
        if "Last week" in value:
            return "Created last week"
        if "daysAgoStart" in value:
            days = re.search(r"daysAgoStart\((\d+)\)", value)
            if days:
                return f"Created in last {days.group(1)} days"
            return f"Created: {value}"
        return f"Created: {value}"

    @classmethod
    def _explain_state_filter(cls, value: str) -> str:
        """Generate explanation for state filter."""
        if "!=" in value:
            return "Excluding resolved/closed records"
        return f"State: {value}"

    @classmethod
    def _explain_assigned_to_filter(cls, value: str) -> str:
        """Generate explanation for assigned_to filter."""
        if value == "NULL":
            return "Unassigned records"
        return f"Assigned to: {value}"

    @classmethod
    def _explain_custom_query_filter(cls, value: str) -> str:
        """Generate explanation for complete query filter."""
        return f"Custom query: {value}"

    @classmethod
    def _generate_filter_explanation(
        cls, filters: Dict[str, str], table_name: str
    ) -> str:
        """Generate human-readable explanation of what the filter will do."""
        if not filters:
            return f"No filters applied - will return all {table_name} records"

        field_handlers = {
            "_complete_query": cls._explain_custom_query_filter,
            "priority": cls._explain_priority_filter,
            "sys_created_on": cls._explain_date_filter,
            "state": cls._explain_state_filter,
            "assigned_to": cls._explain_assigned_to_filter,
        }

        explanations: List[str] = []
        for field, value in filters.items():
            handler = field_handlers.get(field)
            explanations.append(handler(value) if handler else f"{field}: {value}")

        return f"Will find {table_name} records where: " + " AND ".join(explanations)

    @classmethod
    def _generate_sql_for_complete_query(cls, field: str, value: str) -> str:
        return f"({value})"

    @classmethod
    def _generate_sql_for_or_condition(cls, field: str, value: str) -> str:
        or_conditions = value.split("^OR")
        return f"({' OR '.join(or_conditions)})"

    @classmethod
    def _generate_sql_for_not_equal(cls, field: str, value: str) -> str:
        return f"{field} != '{value.replace('!=', '')}'"

    @classmethod
    def _generate_sql_for_greater_equal(cls, field: str, value: str) -> str:
        return f"{field} >= '{value.replace('>=', '')}'"

    @classmethod
    def _generate_sql_for_equal(cls, field: str, value: str) -> str:
        return f"{field} = '{value}'"

    @classmethod
    def _generate_sql_equivalent(
        cls, filters: Dict[str, str], table_name: str
    ) -> str:
        """Generate SQL-like representation for debugging."""
        if not filters:
            return f"SELECT * FROM {table_name}"

        conditions = [cls._determine_sql_condition(field, value) for field, value in filters.items()]
        where_clause = " AND ".join(conditions)
        return f"SELECT * FROM {table_name} WHERE {where_clause}"

    @classmethod
    def _determine_sql_condition(cls, field: str, value: str) -> str:
        """Determine appropriate SQL condition based on field and value."""
        if field == "_complete_query":
            return cls._generate_sql_for_complete_query(field, value)
        if "^OR" in value:
            return cls._generate_sql_for_or_condition(field, value)
        if "!=" in value:
            return cls._generate_sql_for_not_equal(field, value)
        if ">=" in value:
            return cls._generate_sql_for_greater_equal(field, value)
        return cls._generate_sql_for_equal(field, value)


def build_smart_filter(query: str, table: str = "incident", context: Dict = None) -> Dict[str, Any]:
    """Build intelligent filter from natural language query."""
    return QueryIntelligence.build_intelligent_filter(query, table, context)


def get_filter_templates() -> Dict[str, Dict]:
    """Get all available filter templates."""
    return QueryIntelligence.FILTER_TEMPLATES.copy()
