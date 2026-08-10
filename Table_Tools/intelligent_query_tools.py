"""
MCP tool wrappers for intelligent query functionality.
These tools provide natural language query capabilities for ServiceNow data.
"""

from typing import Annotated, Dict, Any, Optional, List
from pydantic import BaseModel, BeforeValidator, Field
from Table_Tools.generic_table_tools import (
    query_table_intelligently,
    explain_filter_query,
    build_and_validate_smart_filter
)
from Table_Tools.read_helpers import carry_partial, is_read_failure
from filter import get_filter_templates
from http_layer import ServiceNowRequestError
from constants import SERVICENOW_QUERY_OPERATORS, QUERY_SYNTAX_NOTES
from param_coercion import coerce_json_dict


class IntelligentQueryParams(BaseModel):
    """Parameters for intelligent natural language queries."""
    query: str = Field(description="Natural language description of what to find (e.g., 'high priority incidents from last week')")
    table: str = Field(default="incident", description="ServiceNow table to search (incident, change_request, sc_req_item, universal_request, kb_knowledge)")
    context: Annotated[Optional[Dict[str, Any]], BeforeValidator(coerce_json_dict)] = Field(None, description="Optional context to enhance the query")


class FilterExplanationParams(BaseModel):
    """Parameters for explaining filter queries."""
    filters: Dict[str, str] = Field(description="ServiceNow filters to explain")
    table: str = Field(default="incident", description="ServiceNow table name")


class SmartFilterParams(BaseModel):
    """Parameters for building and validating smart filters."""
    query: str = Field(description="Natural language query to convert to filters")
    table: str = Field(default="incident", description="ServiceNow table name")
    context: Annotated[Optional[Dict[str, Any]], BeforeValidator(coerce_json_dict)] = Field(None, description="Additional context for filter building")


async def intelligent_search(params: IntelligentQueryParams) -> Dict[str, Any]:
    """Search ServiceNow records using natural-language queries.

    WHEN TO USE: the user hands you a plain-English request to RUN and get rows
        back — "search for unresolved P2 tickets from May using plain English".
    WHEN NOT TO USE: you already know exact field filters (filter_records); you
        only want the filter string, not results (build_smart_servicenow_filter);
        keyword search on one field (search_records).
    PREFER OVER: search_records / filter_records when the input is a natural
        sentence rather than keywords or field values.
    TABLES: incident, change_request, sc_req_item, universal_request,
        kb_knowledge, vtb_task.
    SIDE EFFECT: read-only — executes the query.
    EXAMPLE: search for unresolved P2 tickets from May using plain English.

    Converts NL (e.g. "high priority incidents from last week", "unassigned
    P1 changes today") to ServiceNow filter syntax, validates it, and returns
    results with an explanation of what was searched.

    A read failure returns success=False with the structured
    {"code", "message"} error object from the query layer rather than
    success=True and an empty record list. A partial read returns the rows it
    got, success=True, and partial=True alongside the error.
    """
    query_info = {
        "original_query": params.query,
        "table_searched": params.table,
        "context_used": params.context is not None,
    }
    try:
        result = await query_table_intelligently(
            table_name=params.table,
            natural_language_query=params.query,
            context=params.context
        )

        if is_read_failure(result):
            return {"success": False, "error": result["error"], "query_info": query_info}

        response = {
            "success": True,
            "records": result.get("result", []),
            "record_count": len(result.get("result", [])),
            "intelligence": result.get("intelligence", {}),
            "query_info": query_info,
        }
        return carry_partial(response, result)
    except ServiceNowRequestError as e:
        # Must precede `except Exception`: str(e) would drop the error code and
        # a caller could no longer tell a timeout from a validation failure.
        return {"success": False, **e.to_error_dict(), "query_info": query_info}
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query_info": {
                "original_query": params.query,
                "table_searched": params.table
            }
        }


def explain_servicenow_filters(params: FilterExplanationParams) -> Dict[str, Any]:
    """Explain what ServiceNow filters will do and identify potential issues.

    WHEN TO USE: the user wants to understand an EXISTING filter — "what does
        the filter priority=1 and state=2 actually do".
    WHEN NOT TO USE: turning plain English INTO a filter
        (build_smart_servicenow_filter); the operator reference
        (get_query_syntax_help); running a query (intelligent_search).
    PREFER OVER: get_query_syntax_help when the question is about one concrete
        filter, not operators in general.
    SIDE EFFECT: none — analyses the filter, runs nothing.
    EXAMPLE: what does the filter priority=1 and state=2 actually do.

    This tool helps understand complex ServiceNow filter syntax and provides
    suggestions for improvement. Useful for debugging queries that return
    unexpected results.

    Example filters:
    - {"priority": "1^ORpriority=2", "sys_created_on": ">=2024-01-01"}
    - {"state": "!=6^state!=7", "assigned_to": "NULL"}
    """
    try:
        explanation = explain_filter_query(params.table, params.filters)
        
        return {
            "success": True,
            "explanation": explanation["explanation"],
            "sql_equivalent": explanation["sql_equivalent"],
            "potential_issues": explanation["potential_issues"],
            "suggestions": explanation["suggestions"],
            "estimated_result_size": explanation["estimated_result_size"],
            "filter_analysis": explanation["filter_analysis"],
            "original_filters": params.filters
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "original_filters": params.filters
        }


def build_smart_servicenow_filter(params: SmartFilterParams) -> Dict[str, Any]:
    """Convert natural language to ServiceNow filters without executing the query.

    WHEN TO USE: the user wants the filter STRING built but NOT run — "turn
        'open P1 incidents' into a ServiceNow filter without running it".
    WHEN NOT TO USE: actually fetching rows (intelligent_search); explaining an
        existing filter (explain_servicenow_filters); a live reachability or
        health probe (now_test_oauth) — this tool never contacts ServiceNow.
    PREFER OVER: intelligent_search when you want to inspect the filter first.
    SIDE EFFECT: none — builds and validates a filter, runs nothing.
    EXAMPLE: turn "open P1 incidents" into a ServiceNow filter without running it.

    This tool is useful for:
    - Testing filter generation
    - Understanding what filters will be created
    - Debugging query conversion issues

    Examples:
    - "critical incidents from yesterday"
    - "unassigned high priority tickets"
    - "resolved changes from last month"
    """
    try:
        result = build_and_validate_smart_filter(
            natural_language=params.query,
            table_name=params.table,
            context=params.context
        )
        
        return {
            "success": True,
            "generated_filters": result["filters"],
            "intelligence": result["intelligence"],
            "validation": result["validation"],
            "original_query": params.query,
            "table_name": params.table
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "original_query": params.query,
            "table_name": params.table
        }


def get_servicenow_filter_templates() -> Dict[str, Any]:
    """Get predefined filter templates for common ServiceNow queries.

    WHEN TO USE: the user wants a ready-made filter to copy — "give me a ready
        made filter template for open incidents".
    WHEN NOT TO USE: converting a specific sentence (build_smart_servicenow_filter);
        the operator reference (get_query_syntax_help); NL query examples
        (get_query_examples).
    PREFER OVER: get_query_examples when you want copyable filter dicts, not
        example phrasings.
    SIDE EFFECT: none — returns static templates.
    EXAMPLE: give me a ready made filter template for open incidents.

    These templates provide correctly formatted filters for frequent use cases:
    - High priority incidents from last week
    - Critical recent incidents
    - Unassigned recent tickets
    - Resolved incidents this month
    - Active P1/P2 incidents

    Use these as examples or starting points for building custom queries.
    """
    try:
        templates = get_filter_templates()
        
        template_descriptions = {
            "high_priority_last_week": "P1 and P2 incidents created last week",
            "critical_recent": "Priority 1 (Critical) incidents from last 7 days",
            "unassigned_recent": "Unassigned incidents from last 3 days",
            "resolved_this_month": "Resolved incidents created this month",
            "active_p1_p2": "Active (not resolved/closed) P1 and P2 incidents"
        }
        
        enriched_templates = {}
        for name, filters in templates.items():
            enriched_templates[name] = {
                "filters": filters,
                "description": template_descriptions.get(name, "No description available"),
                "use_case": f"Use for finding {template_descriptions.get(name, name).lower()}"
            }
        
        return {
            "success": True,
            "templates": enriched_templates,
            "template_count": len(templates),
            "usage_info": {
                "how_to_use": "Copy the 'filters' dictionary and pass it to filter_records(table, filters)",
                "customization": "Modify filter values to match your specific needs"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# Template usage examples for documentation
QUERY_EXAMPLES = {
    "time_based": [
        "incidents from last week",
        "critical tickets from yesterday", 
        "changes from this month",
        "resolved incidents from last 30 days"
    ],
    "priority_based": [
        "high priority incidents",
        "P1 and P2 tickets",
        "critical unassigned incidents",
        "low priority resolved tickets"
    ],
    "state_based": [
        "active incidents",
        "resolved tickets",
        "new unassigned incidents",
        "pending changes"
    ],
    "combined": [
        "high priority incidents from last week",
        "unassigned critical tickets from today",
        "resolved P1 incidents this month",
        "active changes with high priority"
    ]
}


def get_query_syntax_help() -> Dict[str, Any]:
    """Return the authoritative ServiceNow encoded-query operator reference.

    WHEN TO USE: you need the operator vocabulary in general — "which encoded
        query operators does ServiceNow support".
    WHEN NOT TO USE: explaining one concrete filter (explain_servicenow_filters);
        ready-made filter dicts (get_servicenow_filter_templates).
    PREFER OVER: get_query_examples when the question is about operators, not
        natural-language phrasings.
    SIDE EFFECT: none — returns a static reference.
    EXAMPLE: which encoded query operators does ServiceNow support.

    Use this BEFORE constructing a `sysparm_query` / filter value to avoid
    guessing operator syntax. Key gotcha: the substring/"contains" operator in
    encoded queries is **LIKE** (`fieldLIKEvalue`), NOT `CONTAINS` — `CONTAINS`
    is a GlideRecord scripting operator and is silently ignored in encoded
    queries (returns zero rows). Reference fields (assignment_group,
    assigned_to, caller_id, cmdb_ci, ...) store sys_ids: filter by sys_id or
    dot-walk (e.g. `assignment_group.nameLIKEFleet`).
    """
    return {
        "success": True,
        "notes": QUERY_SYNTAX_NOTES,
        "operators": SERVICENOW_QUERY_OPERATORS,
        "common_mistakes": [
            "Using CONTAINS in an encoded query — use LIKE instead.",
            "Filtering a reference field by display name — use a sys_id or dot-walk (field.name).",
            "Comma-separated priorities without OR — use priority=1^ORpriority=2 or priorityIN1,2.",
        ],
    }


def get_query_examples() -> Dict[str, Any]:
    """Get examples of natural-language queries that work with intelligent_search.

    WHEN TO USE: the user wants sample phrasings to learn what NL search accepts.
    WHEN NOT TO USE: copyable filter dicts (get_servicenow_filter_templates);
        the operator reference (get_query_syntax_help); running a search
        (intelligent_search).
    PREFER OVER: get_servicenow_filter_templates when you want example wordings,
        not filter structures.
    SIDE EFFECT: none — returns static examples.
    EXAMPLE: show me example plain-English searches I can run.

    Provides categorized examples showing different types of queries supported
    by the intelligent search functionality.
    """
    return {
        "success": True,
        "examples": QUERY_EXAMPLES,
        "tips": [
            "Be specific about time periods (last week, yesterday, this month)",
            "Include priority levels (P1, P2, critical, high, low)",
            "Mention states (active, resolved, new, pending)",
            "Combine multiple criteria for more targeted results",
            "Use 'unassigned' to find tickets without assignees"
        ],
        "supported_tables": [
            "incident - IT incidents and service requests",
            "change_request - Change requests and maintenance",
            "sc_req_item - Service Catalog Request Items",            "universal_request - Universal Requests", 
            "kb_knowledge - Knowledge base articles",
            "vtb_task - Private task records (if configured)"
        ]
    }