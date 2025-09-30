"""
Enhanced Query Intelligence for ServiceNow MCP
Provides natural language to ServiceNow filter conversion with smart validation and correction.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from utils import extract_keywords
from query_validation import ServiceNowQueryBuilder, QueryValidationResult
from constants import ESSENTIAL_FIELDS, DETAIL_FIELDS


class QueryIntelligence:
    """Smart query building and validation for ServiceNow filters."""
    
    # Common filter templates for frequent scenarios
    FILTER_TEMPLATES = {
        "high_priority_last_week": {
            "_complete_query": "sys_created_onONLast week@javascript:gs.beginningOfLastWeek()@javascript:gs.endOfLastWeek()^priority=1^ORpriority=2"
        },
        "critical_recent": {
            "priority": "1",
            "sys_created_on": ">=javascript:gs.daysAgoStart(7)"
        },
        "unassigned_recent": {
            "assigned_to": "NULL",
            "sys_created_on": ">=javascript:gs.daysAgoStart(3)"
        },
        "resolved_this_month": {
            "state": "6",
            "sys_created_on": ">=javascript:gs.beginningOfThisMonth()"
        },
        "active_p1_p2": {
            "priority": "priority=1^ORpriority=2",
            "state": "state!=6^state!=7^state!=8"
        },
        "p1_p2_all_states": {
            "priority": "priority=1^ORpriority=2"
        }
    }
    
    # Natural language patterns and their ServiceNow equivalents
    LANGUAGE_PATTERNS = {
        # Priority patterns
        r"\b(critical|p1|priority\s*1|urgent)\b": {"priority": "1"},
        r"\b(high|p2|priority\s*2|important)\b": {"priority": "2"},
        r"\b(medium|p3|priority\s*3|normal)\b": {"priority": "3"},
        r"\b(low|p4|priority\s*4)\b": {"priority": "4"},
        r"\b(p1\s*and\s*p2|high\s*priority|critical\s*and\s*high)\b": {"priority": "priority=1^ORpriority=2"},
        
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
        
        # Exclusion patterns
        r"\b(exclude|not|without)\s+(\w+)\b": lambda m: {f"{m.group(2)}": f"!={m.group(2)}"},
    }
    
    @classmethod
    def parse_natural_language(cls, query_text: str, table_name: str = "incident") -> Dict[str, Any]:
        """Parse natural language query into ServiceNow filters with intelligence."""
        result = {
            "filters": {},
            "explanation": "",
            "confidence": 0.0,
            "suggestions": [],
            "template_used": None
        }
        
        query_lower = query_text.lower().strip()
        
        # Check for template matches first
        template_match = cls._match_filter_template(query_lower)
        if template_match:
            result["filters"] = template_match["filters"]
            result["template_used"] = template_match["name"]
            result["confidence"] = 0.9
            result["explanation"] = f"Used predefined template: {template_match['name']}"
            return result
        
        # Parse using language patterns
        parsed_filters = {}
        confidence_score = 0.0
        explanations = []
        
        for pattern, filter_data in cls.LANGUAGE_PATTERNS.items():
            matches = re.finditer(pattern, query_lower, re.IGNORECASE)
            for match in matches:
                if callable(filter_data):
                    # Dynamic filter generation
                    dynamic_filters = filter_data(match)
                    parsed_filters.update(dynamic_filters)
                else:
                    parsed_filters.update(filter_data)
                
                confidence_score += 0.2
                explanations.append(f"Detected '{match.group()}' -> {filter_data}")
        
        # Handle keyword-based filters if no patterns matched
        if not parsed_filters:
            keywords = extract_keywords(query_text)
            if keywords:
                # Use keywords for text search
                parsed_filters["short_description"] = f"short_descriptionCONTAINS{keywords[0]}"
                confidence_score = 0.5
                explanations.append(f"Using keyword search for: {keywords[0]}")
        
        # Validate and improve the parsed filters
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
            r"\b(p1\s*and\s*p2|p1\s*p2)\b": "p1_p2_all_states"
        }

        for pattern, template_name in template_patterns.items():
            if re.search(pattern, query_text, re.IGNORECASE):
                return {
                    "name": template_name,
                    "filters": cls.FILTER_TEMPLATES[template_name].copy()  # Return a copy to prevent mutation
                }

        return None
    
    @classmethod
    def _validate_and_improve_filters(cls, filters: Dict[str, str], table_name: str) -> QueryValidationResult:
        """Validate and improve filter syntax using existing validation."""
        from query_validation import validate_query_filters
        
        result = validate_query_filters(filters)
        
        # Auto-correct common issues
        corrected = {}
        for field, value in filters.items():
            # Fix priority OR syntax
            if field == "priority" and "," in value and "^OR" not in value:
                priorities = value.split(",")
                corrected[field] = ServiceNowQueryBuilder.build_priority_or_filter(priorities)
                result.add_suggestion(f"Corrected priority OR syntax: {corrected[field]}")
            
            # Add time components to dates
            elif field == "sys_created_on" and ">=" in value and ":" not in value:
                if "javascript:" not in value:
                    corrected[field] = value.replace(">=", ">=") + " 00:00:00"
                    result.add_suggestion("Added time component to date filter")
                else:
                    corrected[field] = value
            
            else:
                corrected[field] = value
        
        if corrected != filters:
            result.corrected_filters = corrected
        
        return result
    
    @classmethod
    def build_intelligent_filter(
        cls,
        natural_language: str,
        table_name: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Main entry point for intelligent filter building."""
        
        # Parse the natural language query
        parsed_result = cls.parse_natural_language(natural_language, table_name)
        
        # Add context-based enhancements
        if context:
            parsed_result["filters"].update(cls._apply_context_filters(context, table_name))
        
        # Generate explanation
        explanation = cls._generate_filter_explanation(parsed_result["filters"], table_name)
        
        return {
            "filters": parsed_result["filters"],
            "explanation": explanation,
            "confidence": parsed_result["confidence"],
            "suggestions": parsed_result["suggestions"],
            "template_used": parsed_result.get("template_used"),
            "sql_equivalent": cls._generate_sql_equivalent(parsed_result["filters"], table_name)
        }
    
    @classmethod
    def _apply_context_filters(cls, context: Dict, table_name: str) -> Dict[str, str]:
        """Apply context-based filters (e.g., user preferences, previous queries)."""
        context_filters = {}

        # Handle date_range from context
        if context.get("date_range"):
            date_range = context["date_range"]
            if "start" in date_range and "end" in date_range:
                # Use BETWEEN syntax with JavaScript date functions for proper ServiceNow filtering
                context_filters["sys_created_on"] = (
                    f"sys_created_onBETWEENjavascript:gs.dateGenerate('{date_range['start']}','00:00:00')"
                    f"@javascript:gs.dateGenerate('{date_range['end']}','23:59:59')"
                )

        # Handle exclude_caller from context
        if context.get("exclude_caller"):
            caller = context["exclude_caller"]
            if isinstance(caller, list):
                # Multiple caller exclusions - use complete query format
                exclusions = [f"caller_id!={c}" for c in caller]
                context_filters["_complete_caller_exclusion"] = "^".join(exclusions)
            else:
                # Single caller exclusion - use complete query format
                context_filters["_complete_caller_exclusion"] = f"caller_id!={caller}"

        # Only apply state filters if explicitly requested via context
        if context.get("exclude_resolved") is True:
            context_filters["state"] = "state!=6^state!=7^state!=8"

        if context.get("user_assigned_only"):
            context_filters["assigned_to"] = "javascript:gs.getUserID()"

        return context_filters
    
    @classmethod
    def _explain_priority_filter(cls, value: str) -> str:
        """Generate explanation for priority filter."""
        if "^OR" in value:
            priorities = re.findall(r"priority=(\d+)", value)
            return f"Priority levels: {', '.join(priorities)}"
        else:
            return f"Priority: {value}"
    
    @classmethod
    def _explain_date_filter(cls, value: str) -> str:
        """Generate explanation for date-related filters."""
        if "Last week" in value:
            return "Created last week"
        elif "daysAgoStart" in value:
            days = re.search(r"daysAgoStart\((\d+)\)", value)
            if days:
                return f"Created in last {days.group(1)} days"
            return f"Created: {value}"
        else:
            return f"Created: {value}"
    
    @classmethod
    def _explain_state_filter(cls, value: str) -> str:
        """Generate explanation for state filter."""
        if "!=" in value:
            return "Excluding resolved/closed records"
        else:
            return f"State: {value}"
    
    @classmethod
    def _explain_assigned_to_filter(cls, value: str) -> str:
        """Generate explanation for assigned_to filter."""
        if value == "NULL":
            return "Unassigned records"
        else:
            return f"Assigned to: {value}"
    
    @classmethod
    def _explain_custom_query_filter(cls, value: str) -> str:
        """Generate explanation for complete query filter."""
        return f"Custom query: {value}"
    
    @classmethod
    def _generate_filter_explanation(cls, filters: Dict[str, str], table_name: str) -> str:
        """Generate human-readable explanation of what the filter will do."""
        if not filters:
            return f"No filters applied - will return all {table_name} records"
        
        # Field handler registry for specialized explanation logic
        field_handlers = {
            "_complete_query": cls._explain_custom_query_filter,
            "priority": cls._explain_priority_filter,
            "sys_created_on": cls._explain_date_filter,
            "state": cls._explain_state_filter,
            "assigned_to": cls._explain_assigned_to_filter
        }
        
        explanations = []
        for field, value in filters.items():
            handler = field_handlers.get(field)
            if handler:
                explanations.append(handler(value))
            else:
                explanations.append(f"{field}: {value}")
        
        return f"Will find {table_name} records where: " + " AND ".join(explanations)
    
    @classmethod
    def _generate_sql_for_complete_query(cls, field: str, value: str) -> str:
        """Generate SQL condition for complete query."""
        return f"({value})"
    
    @classmethod
    def _generate_sql_for_or_condition(cls, field: str, value: str) -> str:
        """Generate SQL condition for OR operations."""
        or_conditions = value.split("^OR")
        return f"({' OR '.join(or_conditions)})"
    
    @classmethod
    def _generate_sql_for_not_equal(cls, field: str, value: str) -> str:
        """Generate SQL condition for not equal operations."""
        return f"{field} != '{value.replace('!=', '')}'"
    
    @classmethod
    def _generate_sql_for_greater_equal(cls, field: str, value: str) -> str:
        """Generate SQL condition for greater than or equal operations."""
        return f"{field} >= '{value.replace('>=', '')}'"
    
    @classmethod
    def _generate_sql_for_equal(cls, field: str, value: str) -> str:
        """Generate SQL condition for basic equality."""
        return f"{field} = '{value}'"
    
    @classmethod
    def _generate_sql_equivalent(cls, filters: Dict[str, str], table_name: str) -> str:
        """Generate SQL-like representation for debugging."""
        if not filters:
            return f"SELECT * FROM {table_name}"
        
        conditions = []
        for field, value in filters.items():
            condition = cls._determine_sql_condition(field, value)
            conditions.append(condition)
        
        where_clause = " AND ".join(conditions)
        return f"SELECT * FROM {table_name} WHERE {where_clause}"
    
    @classmethod
    def _determine_sql_condition(cls, field: str, value: str) -> str:
        """Determine appropriate SQL condition based on field and value."""
        if field == "_complete_query":
            return cls._generate_sql_for_complete_query(field, value)
        elif "^OR" in value:
            return cls._generate_sql_for_or_condition(field, value)
        elif "!=" in value:
            return cls._generate_sql_for_not_equal(field, value)
        elif ">=" in value:
            return cls._generate_sql_for_greater_equal(field, value)
        else:
            return cls._generate_sql_for_equal(field, value)


class QueryExplainer:
    """Explains existing filters and suggests improvements."""
    
    @classmethod
    def explain_filter(cls, filters: Dict[str, str], table_name: str) -> Dict[str, Any]:
        """Explain what an existing filter does and suggest improvements."""
        explanation = QueryIntelligence._generate_filter_explanation(filters, table_name)
        sql_equivalent = QueryIntelligence._generate_sql_equivalent(filters, table_name)
        
        # Analyze for potential issues
        issues = []
        suggestions = []
        
        for field, value in filters.items():
            if field == "priority" and "," in value and "^OR" not in value:
                issues.append("Priority filter may not work - comma separation doesn't work in ServiceNow")
                suggestions.append("Use OR syntax: priority=1^ORpriority=2")
            
            if field == "sys_created_on" and ">=" in value and "<=" not in value:
                issues.append("Date range incomplete - may return more results than expected")
                suggestions.append("Add end date for complete range")
        
        return {
            "explanation": explanation,
            "sql_equivalent": sql_equivalent,
            "potential_issues": issues,
            "suggestions": suggestions,
            "estimated_result_size": cls._estimate_result_size(filters, table_name)
        }
    
    @classmethod
    def _estimate_result_size(cls, filters: Dict[str, str], table_name: str) -> str:
        """Provide rough estimate of expected result size."""
        # This is a heuristic-based estimation
        if not filters:
            return "Large (all records)"
        
        size_factors = 0
        
        if "priority" in filters:
            if "1" in filters["priority"]:
                size_factors += 1  # P1 incidents are rare
            if "^OR" in filters.get("priority", ""):
                size_factors -= 0.5  # OR expands results
        
        if "sys_created_on" in filters:
            if "daysAgoStart(1)" in filters["sys_created_on"]:
                size_factors += 2  # Today only - very small
            elif "daysAgoStart(7)" in filters["sys_created_on"]:
                size_factors += 1  # Last week - small
        
        if size_factors >= 2:
            return "Small (< 50 records)"
        elif size_factors >= 1:
            return "Medium (50-200 records)"
        else:
            return "Large (> 200 records)"


# Convenience functions for easy integration
def build_smart_filter(query: str, table: str = "incident", context: Dict = None) -> Dict[str, Any]:
    """Build intelligent filter from natural language query."""
    return QueryIntelligence.build_intelligent_filter(query, table, context)


def explain_existing_filter(filters: Dict[str, str], table: str = "incident") -> Dict[str, Any]:
    """Explain what an existing filter does."""
    return QueryExplainer.explain_filter(filters, table)


def get_filter_templates() -> Dict[str, Dict]:
    """Get all available filter templates."""
    return QueryIntelligence.FILTER_TEMPLATES.copy()