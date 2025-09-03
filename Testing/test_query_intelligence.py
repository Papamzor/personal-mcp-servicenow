"""
Test script for the enhanced query intelligence features.
Run this to validate the natural language parsing and filter generation.
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from query_intelligence import QueryIntelligence, build_smart_filter, explain_existing_filter
from Table_Tools.intelligent_query_tools import (
    IntelligentQueryParams, FilterExplanationParams, SmartFilterParams,
    build_smart_servicenow_filter, explain_servicenow_filters, get_servicenow_filter_templates
)


def test_language_parsing():
    """Test natural language parsing without API calls."""
    print("=== Testing Natural Language Parsing ===")
    
    test_queries = [
        "high priority incidents from last week",
        "critical tickets from yesterday",
        "unassigned P1 incidents",
        "resolved incidents this month",
        "active changes with high priority",
        "database server issues",
        "P1 and P2 incidents from last 30 days"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        result = QueryIntelligence.parse_natural_language(query, "incident")
        
        print(f"  Filters generated: {result['filters']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Template used: {result.get('template_used', 'None')}")
        print(f"  Explanation: {result['explanation']}")
        if result['suggestions']:
            print(f"  Suggestions: {result['suggestions']}")


def test_filter_templates():
    """Test predefined filter templates."""
    print("\n=== Testing Filter Templates ===")
    
    templates = QueryIntelligence.FILTER_TEMPLATES
    
    for name, filters in templates.items():
        print(f"\nTemplate: {name}")
        print(f"  Filters: {filters}")
        
        # Test explanation
        explanation = QueryIntelligence._generate_filter_explanation(filters, "incident")
        print(f"  Explanation: {explanation}")


async def test_smart_filter_building():
    """Test smart filter building function."""
    print("\n=== Testing Smart Filter Building ===")
    
    test_cases = [
        {"query": "critical incidents from last week", "table": "incident"},
        {"query": "unassigned high priority tickets", "table": "incident"},
        {"query": "resolved changes from this month", "table": "change_request"}
    ]
    
    for case in test_cases:
        print(f"\nTesting: {case['query']} (table: {case['table']})")
        
        params = SmartFilterParams(query=case["query"], table=case["table"])
        result = await build_smart_servicenow_filter(params)
        
        if result["success"]:
            print(f"  Generated filters: {result['generated_filters']}")
            print(f"  Confidence: {result['intelligence']['confidence']:.2f}")
            print(f"  Explanation: {result['intelligence']['explanation']}")
            if result['validation']['warnings']:
                print(f"  Warnings: {result['validation']['warnings']}")
        else:
            print(f"  Error: {result['error']}")


async def test_filter_explanation():
    """Test filter explanation functionality."""
    print("\n=== Testing Filter Explanation ===")
    
    test_filters = [
        {
            "filters": {"priority": "1^ORpriority=2", "sys_created_on": ">=javascript:gs.beginningOfLastWeek()"},
            "table": "incident"
        },
        {
            "filters": {"priority": "1,2", "state": "!=6"},  # Intentionally incorrect syntax
            "table": "incident"
        },
        {
            "filters": {"assigned_to": "NULL", "sys_created_on": ">=2024-01-01"},
            "table": "incident"
        }
    ]
    
    for test_case in test_filters:
        print(f"\nExplaining filters: {test_case['filters']}")
        
        params = FilterExplanationParams(filters=test_case["filters"], table=test_case["table"])
        result = await explain_servicenow_filters(params)
        
        if result["success"]:
            print(f"  Explanation: {result['explanation']}")
            print(f"  Estimated size: {result['estimated_result_size']}")
            if result['potential_issues']:
                print(f"  Issues: {result['potential_issues']}")
            if result['suggestions']:
                print(f"  Suggestions: {result['suggestions']}")
        else:
            print(f"  Error: {result['error']}")


async def test_template_retrieval():
    """Test template retrieval functionality."""
    print("\n=== Testing Template Retrieval ===")
    
    result = await get_servicenow_filter_templates()
    
    if result["success"]:
        print(f"Found {result['template_count']} templates:")
        for name, template in result["templates"].items():
            print(f"  {name}: {template['description']}")
            print(f"    Use case: {template['use_case']}")
    else:
        print(f"Error: {result['error']}")


def test_query_validation():
    """Test query validation and correction."""
    print("\n=== Testing Query Validation and Correction ===")
    
    test_filters = [
        {"priority": "1,2"},  # Incorrect comma syntax
        {"sys_created_on": ">=2024-01-01"},  # Missing time component
        {"priority": "priority=1^ORpriority=2"},  # Correct syntax
    ]
    
    for filters in test_filters:
        print(f"\nValidating: {filters}")
        result = QueryIntelligence._validate_and_improve_filters(filters, "incident")
        
        print(f"  Valid: {result.is_valid}")
        if result.warnings:
            print(f"  Warnings: {result.warnings}")
        if result.suggestions:
            print(f"  Suggestions: {result.suggestions}")
        if result.corrected_filters:
            print(f"  Corrected: {result.corrected_filters}")


async def run_all_tests():
    """Run all tests."""
    print("Starting Query Intelligence Tests...")
    print("="*50)
    
    # Non-async tests
    test_language_parsing()
    test_filter_templates()
    test_query_validation()
    
    # Async tests
    await test_smart_filter_building()
    await test_filter_explanation()
    await test_template_retrieval()
    
    print("\n" + "="*50)
    print("All tests completed!")


if __name__ == "__main__":
    # Run tests
    asyncio.run(run_all_tests())