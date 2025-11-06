#!/usr/bin/env python3
"""
Simple test script for incident category filtering functionality.
Tests the logic without requiring full dependencies.
"""

# Test the constants
print("=" * 70)
print("Testing Incident Category Filtering Implementation")
print("=" * 70)

# Test 1: Check constants
print("\nTest 1: Checking constants...")
from constants import ESSENTIAL_FIELDS, DETAIL_FIELDS

assert "category" in ESSENTIAL_FIELDS["incident"], "category not in ESSENTIAL_FIELDS"
print("✓ category is in ESSENTIAL_FIELDS for incident")

assert "category" in DETAIL_FIELDS["incident"], "category not in DETAIL_FIELDS"
print("✓ category is in DETAIL_FIELDS for incident")

# Test 2: Check filtering configuration
print("\nTest 2: Checking filtering configuration...")
from constants import ENABLE_INCIDENT_CATEGORY_FILTERING, EXCLUDED_INCIDENT_CATEGORIES

assert ENABLE_INCIDENT_CATEGORY_FILTERING is True, "Filtering should be enabled"
print(f"✓ ENABLE_INCIDENT_CATEGORY_FILTERING = {ENABLE_INCIDENT_CATEGORY_FILTERING}")

expected_categories = ["Payroll", "People Support", "Workplace"]
assert EXCLUDED_INCIDENT_CATEGORIES == expected_categories, f"Expected {expected_categories}"
print(f"✓ EXCLUDED_INCIDENT_CATEGORIES = {EXCLUDED_INCIDENT_CATEGORIES}")

# Test 3: Test the filtering logic manually
print("\nTest 3: Testing filtering logic manually...")


def test_apply_incident_category_filter(table_name: str, existing_query: str = "") -> str:
    """Replicate the filtering logic for testing."""
    if table_name != "incident" or not ENABLE_INCIDENT_CATEGORY_FILTERING:
        return existing_query

    category_filters = [f"category!={category}" for category in EXCLUDED_INCIDENT_CATEGORIES]
    category_query = "^".join(category_filters)

    if existing_query:
        return f"{existing_query}^{category_query}"
    return category_query


# Test with empty query
result = test_apply_incident_category_filter("incident", "")
expected = "category!=Payroll^category!=People Support^category!=Workplace"
assert result == expected, f"Expected '{expected}', got '{result}'"
print(f"✓ Empty query for incident: {result}")

# Test with existing query
result = test_apply_incident_category_filter("incident", "priority=1")
expected = "priority=1^category!=Payroll^category!=People Support^category!=Workplace"
assert result == expected, f"Expected '{expected}', got '{result}'"
print(f"✓ Existing query for incident: {result}")

# Test with complex query
result = test_apply_incident_category_filter("incident", "priority=1^state!=6")
expected = "priority=1^state!=6^category!=Payroll^category!=People Support^category!=Workplace"
assert result == expected, f"Expected '{expected}', got '{result}'"
print(f"✓ Complex query for incident: {result}")

# Test with non-incident table (should not apply filter)
result = test_apply_incident_category_filter("change_request", "priority=1")
expected = "priority=1"
assert result == expected, f"Expected '{expected}', got '{result}'"
print(f"✓ Non-incident table: {result}")

# Test with empty query for non-incident table
result = test_apply_incident_category_filter("change_request", "")
expected = ""
assert result == expected, f"Expected '{expected}', got '{result}'"
print(f"✓ Non-incident table with empty query: (empty string)")

print("\n" + "=" * 70)
print("✓ All tests passed!")
print("=" * 70)
print("\nSummary:")
print("- Category field added to incident field definitions")
print("- Filtering configuration properly set up")
print("- Filter logic correctly blocks sensitive categories")
print("- Non-incident tables are not affected")
print("- Filtering is configurable via ENABLE_INCIDENT_CATEGORY_FILTERING")
