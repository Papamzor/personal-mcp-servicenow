# ServiceNow Query Syntax Guide

This guide provides examples and best practices for ServiceNow API queries to avoid common filtering mistakes and ensure complete data retrieval.

## Common Query Patterns

### Multiple Priorities (OR Logic)
```python
# ✅ CORRECT - Use ServiceNow's native OR syntax
filters = {"priority": "1^ORpriority=2"}

# ❌ INCORRECT - Separate API calls don't combine results properly
filters1 = {"priority": "1"}
filters2 = {"priority": "2"}
```

### Date Ranges
```python
# ✅ CORRECT - Complete date range
filters = {
    "sys_created_on": ">=2025-08-25 00:00:00^<=2025-08-31 23:59:59"
}

# ✅ CORRECT - ServiceNow JavaScript functions
filters = {
    "sys_created_on": ">=javascript:gs.beginningOfLastWeek()^<=javascript:gs.endOfLastWeek()"
}

# ⚠️ INCOMPLETE - Missing end date may return more results than expected
filters = {"sys_created_on": ">=2025-08-25"}
```

### Exclusion Filters
```python
# ✅ CORRECT - Exclude multiple callers
filters = {
    "caller_id": "!=1727339e47d99190c43d3171e36d43ad^caller_id!=479f2d3d475ad150c43d3171e36d43bc"
}
```

### Complex Combined Queries
```python
# ✅ CORRECT - P1/P2 incidents from last week, excluding system users
filters = {
    "priority": "1^ORpriority=2",
    "sys_created_on": ">=javascript:gs.beginningOfLastWeek()^<=javascript:gs.endOfLastWeek()",
    "caller_id": "!=1727339e47d99190c43d3171e36d43ad^caller_id!=479f2d3d475ad150c43d3171e36d43bc"
}
```

## Using the Enhanced MCP Functions

### Priority Incidents with Proper Syntax
```python
# Use the new get_priority_incidents function
from Table_Tools.incident_tools import get_priority_incidents

# Get P1 and P2 incidents with date range
incidents = await get_priority_incidents(
    priorities=["1", "2"],
    sys_created_on=">=2025-08-25 00:00:00^<=2025-08-31 23:59:59"
)
```

### Using Query Builder Helpers
```python
from query_validation import ServiceNowQueryBuilder

# Build proper OR syntax for multiple priorities
priority_filter = ServiceNowQueryBuilder.build_priority_or_filter(["1", "2", "3"])
# Result: "1^ORpriority=2^ORpriority=3"

# Build date range filter
date_filter = ServiceNowQueryBuilder.build_date_range_filter("2025-08-25", "2025-08-31")
# Result: ">=2025-08-25 00:00:00^<=2025-08-31 23:59:59"

# Build exclusion filter
exclusion_filter = ServiceNowQueryBuilder.build_exclusion_filter("caller_id", ["id1", "id2"])
# Result: "caller_id!=id1^caller_id!=id2"
```

## Common Mistakes to Avoid

### ❌ Separate API Calls for OR Logic
```python
# DON'T DO THIS - Results don't combine properly
p1_incidents = await get_incidents_by_filter({"priority": "1"})
p2_incidents = await get_incidents_by_filter({"priority": "2"})
combined = p1_incidents + p2_incidents  # This doesn't work correctly
```

### ❌ Incorrect OR Syntax
```python
# DON'T DO THIS - ServiceNow won't understand this format
filters = {"priority": "1,2"}  # Comma separation doesn't work
filters = {"priority": "1 OR 2"}  # SQL-style OR doesn't work
```

### ❌ Incomplete Date Ranges
```python
# DON'T DO THIS - May return unexpected results
filters = {"sys_created_on": ">2025-08-25"}  # Missing time and end date
```

## Validation and Debugging

The enhanced MCP server now includes:

### Automatic Query Validation
- Warns about potential syntax issues
- Suggests corrections for common mistakes
- Validates result completeness for critical queries

### Result Completeness Checks
- Flags unusually low results for high-priority incidents
- Cross-validates critical incident queries
- Provides suggestions for query improvements

### Pagination Handling
- Automatically handles large result sets
- Ensures no data is missed due to ServiceNow query limits
- Retrieves complete datasets up to configurable limits

## Troubleshooting

### Low Result Counts
If you're getting unexpectedly few results:
1. Check OR syntax for multiple values
2. Verify date range completeness
3. Confirm field names match ServiceNow schema
4. Test with broader criteria first

### Missing Critical Incidents
For high-priority incident queries:
1. Use the `get_priority_incidents()` function
2. Cross-verify with individual incident lookups
3. Check pagination limits and increase if needed
4. Validate date ranges cover the expected period

### Zero Results
When getting no results:
1. Verify filter syntax matches examples above
2. Test individual filter components separately
3. Check ServiceNow field names and values
4. Try broader date ranges or criteria

## Examples for Common Use Cases

### Weekly Incident Report (P1/P2)
```python
from Table_Tools.incident_tools import get_priority_incidents

# Get all P1 and P2 incidents from last week
weekly_incidents = await get_priority_incidents(
    priorities=["1", "2"],
    sys_created_on=">=javascript:gs.beginningOfLastWeek()^<=javascript:gs.endOfLastWeek()"
)
```

### Incidents by Assignment Group
```python
filters = {
    "assignment_group": "IT Support",
    "state": "1^ORstate=2",  # New or In Progress
    "sys_created_on": ">=javascript:gs.daysAgoStart(7)"  # Last 7 days
}
result = await get_incidents_by_filter(IncidentFilterParams(filters=filters))
```

### Major Incident Analysis
```python
# Get all P1 incidents for the month
major_incidents = await get_priority_incidents(
    priorities=["1"],
    sys_created_on=">=2025-08-01 00:00:00^<=2025-08-31 23:59:59",
    state="6"  # Resolved incidents only
)
```

This guide helps ensure reliable, complete data retrieval from ServiceNow while avoiding common syntax pitfalls that can lead to missing critical incidents.