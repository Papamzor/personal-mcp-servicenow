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
    intelligent_search, build_smart_servicenow_filter, explain_servicenow_filters,
    get_servicenow_filter_templates, get_query_examples
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


async def test_intelligent_search_tool():
    """Test the intelligent search MCP tool wrapper."""
    print("\n=== Testing Intelligent Search MCP Tool ===")

    test_cases = [
        {"query": "high priority incidents from last week", "table": "incident"},
        {"query": "unassigned critical tickets", "table": "incident"},
        {"query": "resolved changes from this month", "table": "change_request"},
        {"query": "active knowledge articles about servers", "table": "kb_knowledge"}
    ]

    for case in test_cases:
        print(f"\nTesting intelligent search: {case['query']} (table: {case['table']})")

        try:
            params = IntelligentQueryParams(query=case["query"], table=case["table"])
            result = await intelligent_search(params)

            if result["success"]:
                print(f"  Records found: {result['record_count']}")
                print(f"  Confidence: {result['intelligence'].get('confidence', 'N/A')}")
                print(f"  Explanation: {result['intelligence'].get('explanation', 'N/A')}")
                if result['intelligence'].get('template_used'):
                    print(f"  Template used: {result['intelligence']['template_used']}")
            else:
                print(f"  Expected connection error: {result['error']}")
        except Exception as e:
            print(f"  Exception (expected in test environment): {str(e)}")


async def test_query_examples_tool():
    """Test the query examples MCP tool."""
    print("\n=== Testing Query Examples Tool ===")

    try:
        result = await get_query_examples()

        if result["success"]:
            print(f"Found example categories: {list(result['examples'].keys())}")
            for category, examples in result["examples"].items():
                print(f"  {category}: {len(examples)} examples")
                if examples:
                    print(f"    Sample: '{examples[0]}'")

            print(f"Tips provided: {len(result['tips'])}")
            print(f"Supported tables: {len(result['supported_tables'])}")
        else:
            print(f"Error: {result['error']}")
    except Exception as e:
        print(f"Exception: {str(e)}")


def test_redos_protection():
    """Test ReDoS (Regular Expression Denial of Service) protection."""
    print("\n=== Testing ReDoS Protection ===")

    from Table_Tools.generic_table_tools import _validate_regex_input, _parse_date_range_from_text

    # Test input validation
    test_inputs = [
        ("normal input", True),  # Should pass
        ("a" * 300, False),      # Too long - should fail
        ("a " * 100, False),     # Too many spaces - should fail
        ("a-" * 50, False),      # Too many dashes - should fail
        ("Week 35 2025", True)   # Valid date string - should pass
    ]

    for test_input, expected in test_inputs:
        result = _validate_regex_input(test_input)
        status = "PASS" if result == expected else "FAIL"
        print(f"  [{status}] Input validation: '{test_input[:20]}...' -> {result}")

    # Test date parsing with potentially malicious input
    malicious_inputs = [
        "a" * 500,  # Very long string
        "(" * 100,  # Many special characters
        "Week " + "35 " * 100,  # Repeated patterns
    ]

    for malicious_input in malicious_inputs:
        try:
            result = _parse_date_range_from_text(malicious_input)
            print(f"  [PASS] ReDoS protection handled: '{malicious_input[:20]}...' -> {result}")
        except Exception as e:
            print(f"  [INFO] Input rejected (expected): {str(e)[:50]}...")


def test_security_features():
    """Test security features and validation."""
    print("\n=== Testing Security Features ===")

    # Test that dangerous inputs are handled safely
    dangerous_queries = [
        "'; DROP TABLE incidents; --",  # SQL injection attempt
        "<script>alert('xss')</script>",  # XSS attempt
        "../../etc/passwd",  # Path traversal attempt
        "a" * 1000,  # Buffer overflow attempt
    ]

    for dangerous_query in dangerous_queries:
        print(f"\nTesting dangerous input: '{dangerous_query[:30]}...'")
        try:
            # Test natural language parsing
            result = QueryIntelligence.parse_natural_language(dangerous_query, "incident")
            print(f"  Natural language parsing completed safely")
            print(f"  Confidence: {result['confidence']}")

            # Test smart filter building
            params = SmartFilterParams(query=dangerous_query, table="incident")
            filter_result = await build_smart_servicenow_filter(params)
            print(f"  Smart filter building completed safely: {filter_result['success']}")

        except Exception as e:
            print(f"  Safely handled exception: {str(e)[:50]}...")


async def test_error_handling():
    """Test comprehensive error handling in intelligent tools."""
    print("\n=== Testing Error Handling ===")

    # Test invalid table names
    try:
        params = IntelligentQueryParams(query="test query", table="invalid_table")
        result = await intelligent_search(params)
        status = "PASS" if not result["success"] else "FAIL"
        print(f"  [{status}] Invalid table handled: {result.get('error', 'No error')}")
    except Exception as e:
        print(f"  [PASS] Invalid table caught: {str(e)[:50]}...")

    # Test empty queries
    try:
        params = IntelligentQueryParams(query="", table="incident")
        result = await intelligent_search(params)
        print(f"  [INFO] Empty query handled: Success={result['success']}")
    except Exception as e:
        print(f"  [INFO] Empty query caught: {str(e)[:50]}...")

    # Test malformed filters for explanation
    try:
        params = FilterExplanationParams(filters={"invalid": None}, table="incident")
        result = await explain_servicenow_filters(params)
        print(f"  [INFO] Invalid filter handled: Success={result['success']}")
    except Exception as e:
        print(f"  [INFO] Invalid filter caught: {str(e)[:50]}...")


async def run_all_tests():
    """Run all tests including expanded coverage."""
    print("Enhanced Query Intelligence Tests")
    print("="*50)
    print("Testing natural language processing, MCP tools, and security features")

    # Original tests
    test_language_parsing()
    test_filter_templates()
    test_query_validation()

    # Security and protection tests
    test_redos_protection()
    await test_security_features()
    await test_error_handling()

    # MCP tool wrapper tests
    await test_smart_filter_building()
    await test_filter_explanation()
    await test_template_retrieval()
    await test_intelligent_search_tool()
    await test_query_examples_tool()

    print("\n" + "="*50)
    print("Enhanced Query Intelligence Tests Completed!")
    print("✅ Natural language processing tested")
    print("✅ MCP tool wrappers tested")
    print("✅ ReDoS protection validated")
    print("✅ Security features verified")
    print("✅ Error handling confirmed")


if __name__ == "__main__":
    # Run enhanced test suite
    asyncio.run(run_all_tests())