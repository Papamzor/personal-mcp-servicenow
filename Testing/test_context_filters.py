"""
Test script to validate context-based filtering fixes.

This script tests:
1. Date range context filters are properly applied
2. Caller exclusion context filters are properly applied
3. State filters are NOT automatically added (only when explicitly requested)
4. Response shows all filters with their sources
"""

import asyncio
import json
import sys
from Table_Tools.intelligent_query_tools import intelligent_search, IntelligentQueryParams

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


async def test_context_filters():
    """Test context-based date range and caller exclusion."""

    print("=" * 80)
    print("TEST 1: P1 and P2 incidents with date range and caller exclusion")
    print("=" * 80)

    params = IntelligentQueryParams(
        query="P1 and P2 incidents",
        table="incident",
        context={
            "date_range": {
                "start": "2025-09-22",
                "end": "2025-09-28"
            },
            "exclude_caller": "1727339e47d99190c43d3171e36d43ad"
        }
    )

    result = await intelligent_search(params)

    print(f"\n✓ Success: {result['success']}")
    print(f"✓ Record count: {result['record_count']}")
    print(f"\n--- Intelligence Metadata ---")
    print(f"Explanation: {result['intelligence']['explanation']}")
    print(f"Confidence: {result['intelligence']['confidence']}")
    print(f"Template used: {result['intelligence'].get('template_used')}")

    print(f"\n--- Filters Used ---")
    print(json.dumps(result['intelligence']['filters_used'], indent=2))

    print(f"\n--- Filter Sources ---")
    print(json.dumps(result['intelligence'].get('filter_sources', {}), indent=2))

    print(f"\n--- Debug Information ---")
    debug_info = result['intelligence'].get('debug', {})
    print(f"Encoded query: {debug_info.get('encoded_query_sent_to_servicenow', 'N/A')}")
    print(f"\nFilters from context:")
    print(json.dumps(debug_info.get('filters_from_context', {}), indent=2))
    print(f"\nFilters from natural language:")
    print(json.dumps(debug_info.get('filters_from_nl', {}), indent=2))
    print(f"\nFinal merged filters:")
    print(json.dumps(debug_info.get('final_merged_filters', {}), indent=2))

    print(f"\n--- Records Found ---")
    if result['records']:
        for record in result['records']:
            number = record.get('number', 'N/A')
            short_desc = record.get('short_description', 'N/A')
            created = record.get('sys_created_on', 'N/A')
            priority = record.get('priority', 'N/A')
            print(f"  {number}: {short_desc[:60]}... (Created: {created}, Priority: {priority})")
    else:
        print("  No records found")

    # Validate expected behavior
    print(f"\n--- Validation ---")
    filters_used = result['intelligence']['filters_used']

    # Check 1: Date filter from context should be present
    if 'sys_created_on' in filters_used:
        print("✓ PASS: Date range filter applied from context")
    else:
        print("✗ FAIL: Date range filter NOT applied from context")

    # Check 2: Caller exclusion should be present
    caller_filter_present = any('caller_id' in key or 'caller_exclusion' in key for key in filters_used.keys())
    if caller_filter_present:
        print("✓ PASS: Caller exclusion filter applied from context")
    else:
        print("✗ FAIL: Caller exclusion filter NOT applied from context")

    # Check 3: State filter should NOT be present (not explicitly requested)
    if 'state' not in filters_used:
        print("✓ PASS: State filter NOT automatically added (correct behavior)")
    else:
        print("✗ FAIL: State filter was automatically added (should not happen)")

    # Check 4: Priority filter should be present (from natural language)
    if 'priority' in filters_used:
        print("✓ PASS: Priority filter applied from natural language query")
    else:
        print("✗ FAIL: Priority filter NOT applied from natural language query")

    print("\n" + "=" * 80)


async def test_active_query_with_state_filter():
    """Test that state filters ARE added when explicitly requested."""

    print("\nTEST 2: Active P1 and P2 incidents (should include state filter)")
    print("=" * 80)

    params = IntelligentQueryParams(
        query="active P1 and P2 incidents",
        table="incident",
        context={
            "date_range": {
                "start": "2025-09-22",
                "end": "2025-09-28"
            }
        }
    )

    result = await intelligent_search(params)

    print(f"\n✓ Success: {result['success']}")
    print(f"✓ Record count: {result['record_count']}")

    print(f"\n--- Filters Used ---")
    print(json.dumps(result['intelligence']['filters_used'], indent=2))

    # Validation
    print(f"\n--- Validation ---")
    filters_used = result['intelligence']['filters_used']

    if 'state' in filters_used:
        print("✓ PASS: State filter correctly added for 'active' query")
    else:
        print("✗ FAIL: State filter should be added for 'active' query")

    print("\n" + "=" * 80)


async def test_no_context():
    """Test query without context (baseline test)."""

    print("\nTEST 3: P1 and P2 incidents without context (baseline)")
    print("=" * 80)

    params = IntelligentQueryParams(
        query="P1 and P2 incidents",
        table="incident"
    )

    result = await intelligent_search(params)

    print(f"\n✓ Success: {result['success']}")
    print(f"✓ Record count: {result['record_count']}")

    print(f"\n--- Filters Used ---")
    print(json.dumps(result['intelligence']['filters_used'], indent=2))

    # Validation
    print(f"\n--- Validation ---")
    filters_used = result['intelligence']['filters_used']

    if 'sys_created_on' not in filters_used:
        print("✓ PASS: No date filter (context not provided)")
    else:
        print("✗ FAIL: Date filter should not be present without context")

    if 'state' not in filters_used:
        print("✓ PASS: No state filter (not explicitly requested)")
    else:
        print("✗ FAIL: State filter should not be added automatically")

    print("\n" + "=" * 80)


async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("CONTEXT FILTER VALIDATION TESTS")
    print("=" * 80)

    try:
        await test_context_filters()
        await test_active_query_with_state_filter()
        await test_no_context()

        print("\n✓ All tests completed!")
        print("\nExpected behavior:")
        print("  - Context date_range should be applied as sys_created_on BETWEEN filter")
        print("  - Context exclude_caller should be applied as caller_id!= filter")
        print("  - State filters should ONLY appear when 'active', 'open', etc. in query")
        print("  - Response should show filter sources (context vs natural_language)")

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())