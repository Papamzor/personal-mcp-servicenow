"""
MCP tool wrappers for intelligent query functionality.
These tools provide natural language query capabilities for ServiceNow data.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from Table_Tools.generic_table_tools import (
    query_table_intelligently, 
    explain_filter_query, 
    build_and_validate_smart_filter
)
from query_intelligence import get_filter_templates


class IntelligentQueryParams(BaseModel):
    """Parameters for intelligent natural language queries."""
    query: str = Field(description="Natural language description of what to find (e.g., 'high priority incidents from last week')")
    table: str = Field(default="incident", description="ServiceNow table to search (incident, change_request, sc_req_item, kb_knowledge)")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context to enhance the query")


class FilterExplanationParams(BaseModel):
    """Parameters for explaining filter queries."""
    filters: Dict[str, str] = Field(description="ServiceNow filters to explain")
    table: str = Field(default="incident", description="ServiceNow table name")


class SmartFilterParams(BaseModel):
    """Parameters for building and validating smart filters."""
    query: str = Field(description="Natural language query to convert to filters")
    table: str = Field(default="incident", description="ServiceNow table name")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for filter building")


async def intelligent_search(params: IntelligentQueryParams) -> Dict[str, Any]:
    """
    Search ServiceNow records using natural language queries with intelligent filter conversion.
    
    Examples:
    - "high priority incidents from last week"
    - "unassigned critical tickets from today"
    - "resolved P1 incidents this month"
    - "active changes for database servers"
    
    This tool automatically converts natural language to proper ServiceNow filter syntax,
    validates the query, and provides explanations of what was searched.
    """
    try:
        result = await query_table_intelligently(
            table_name=params.table,
            natural_language_query=params.query,
            context=params.context
        )
        
        return {
            "success": True,
            "records": result.get("result", []),
            "record_count": len(result.get("result", [])),
            "intelligence": result.get("intelligence", {}),
            "query_info": {
                "original_query": params.query,
                "table_searched": params.table,
                "context_used": params.context is not None
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query_info": {
                "original_query": params.query,
                "table_searched": params.table
            }
        }


async def explain_servicenow_filters(params: FilterExplanationParams) -> Dict[str, Any]:
    """
    Explain what ServiceNow filters will do and identify potential issues.
    
    This tool helps understand complex ServiceNow filter syntax and provides
    suggestions for improvement. Useful for debugging queries that return
    unexpected results.
    
    Example filters:
    - {"priority": "1^ORpriority=2", "sys_created_on": ">=2024-01-01"}
    - {"state": "!=6^state!=7", "assigned_to": "NULL"}
    """
    try:
        explanation = await explain_filter_query(params.table, params.filters)
        
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


async def build_smart_servicenow_filter(params: SmartFilterParams) -> Dict[str, Any]:
    """
    Convert natural language to ServiceNow filters without executing the query.
    
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
        result = await build_and_validate_smart_filter(
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
    """
    Get predefined filter templates for common ServiceNow queries.
    
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
                "how_to_use": "Copy the 'filters' dictionary and use with getIncidentsByFilter or similar functions",
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


def get_query_examples() -> Dict[str, Any]:
    """
    Get examples of natural language queries that work with the intelligent search.
    
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
            "sc_req_item - Service catalog request items", 
            "kb_knowledge - Knowledge base articles",
            "vtb_task - Private task records (if configured)"
        ]
    }