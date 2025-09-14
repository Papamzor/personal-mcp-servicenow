# Migration Guide: v1.x to v2.0

This guide helps you migrate from Personal MCP ServiceNow v1.x to v2.0. Version 2.0 includes significant architectural changes and new features that require some adjustments to existing code.

## 🚨 Breaking Changes Overview

### Deleted Files
The following individual tool files have been **completely removed** and consolidated:
- ❌ `Table_Tools/incident_tools.py`
- ❌ `Table_Tools/change_tools.py`
- ❌ `Table_Tools/kb_tools.py`
- ❌ `Table_Tools/ur_tools.py`

### Authentication Changes
- ❌ **Basic Authentication Removed**: No longer supported
- ✅ **OAuth 2.0 Only**: Now the exclusive authentication method

### Function Naming
- All MCP tool functions now use `snake_case` naming convention

## 📋 Step-by-Step Migration

### 1. Update Authentication Setup

#### v1.x (No longer works)
```python
# Basic auth - REMOVED
SERVICENOW_USERNAME = "your_username"
SERVICENOW_PASSWORD = "your_password"
```

#### v2.0 (Required)
```env
# .env file
SERVICENOW_INSTANCE=https://your-instance.service-now.com
SERVICENOW_CLIENT_ID=your_oauth_client_id
SERVICENOW_CLIENT_SECRET=your_oauth_client_secret
```

**Action Required**: Follow the OAuth setup guide in `OAUTH_SETUP_GUIDE.md`

### 2. Update Import Statements

#### v1.x (No longer works)
```python
from Table_Tools.incident_tools import get_incident_by_number
from Table_Tools.change_tools import get_change_by_number
from Table_Tools.kb_tools import get_knowledge_by_number
from Table_Tools.ur_tools import get_ur_by_number
```

#### v2.0 (New approach)
```python
from Table_Tools.consolidated_tools import (
    get_incident_details,
    get_change_details,
    get_knowledge_details,
    get_ur_details
)
```

### 3. Function Name Updates

#### Incident Functions
| v1.x Function | v2.0 Function | Notes |
|--------------|---------------|--------|
| `getIncidentByNumber()` | `get_incident_details()` | Now snake_case |
| `getSimilarIncidents()` | `similar_incidents_for_text()` | Enhanced with AI |
| `getIncidentsByPriority()` | `get_priority_incidents()` | Improved OR syntax |

#### Change Request Functions
| v1.x Function | v2.0 Function | Notes |
|--------------|---------------|--------|
| `getChangeByNumber()` | `get_change_details()` | Now snake_case |
| `getSimilarChanges()` | `similar_changes_for_text()` | Enhanced with AI |

#### Knowledge Base Functions
| v1.x Function | v2.0 Function | Notes |
|--------------|---------------|--------|
| `getKnowledgeByNumber()` | `get_knowledge_details()` | Now snake_case |
| `searchKnowledge()` | `similar_knowledge_for_text()` | Enhanced search |

#### User Request Functions
| v1.x Function | v2.0 Function | Notes |
|--------------|---------------|--------|
| `getURByNumber()` | `get_ur_details()` | Now snake_case |
| `getSimilarURs()` | `similar_ur_for_text()` | Enhanced with AI |

### 4. Update Function Calls

#### v1.x Example
```python
# Old way - multiple separate tools
incident = await getIncidentByNumber("INC0001234")
change = await getChangeByNumber("CHG0001234")
kb = await getKnowledgeByNumber("KB0001234")
```

#### v2.0 Example
```python
# New way - consolidated tools
incident = await get_incident_details("INC0001234")
change = await get_change_details("CHG0001234")
kb = await get_knowledge_details("KB0001234")

# OR use the new generic approach
from Table_Tools.generic_table_tools import get_record_details

incident = await get_record_details("incident", "INC0001234")
change = await get_record_details("change_request", "CHG0001234")
kb = await get_record_details("kb_knowledge", "KB0001234")
```

### 5. Leverage New AI Features

#### Natural Language Queries (NEW in v2.0)
```python
from Table_Tools.intelligent_query_tools import intelligent_search

# Natural language queries - completely new capability
result = await intelligent_search(IntelligentQueryParams(
    query="high priority incidents from last week",
    table="incident"
))

# Get explanations of what the query understood
print(result["intelligence"]["explanation"])
print(result["intelligence"]["sql_equivalent"])
```

#### Smart Filtering (Enhanced in v2.0)
```python
from Table_Tools.generic_table_tools import query_table_with_filters, TableFilterParams

# v2.0 - Intelligent parsing of natural language
filters = {
    "sys_created_on": "Week 35 2025",  # Automatically parsed
    "priority": "1,2",                 # Automatically becomes OR syntax
    "exclude_caller": "logicmonitor"   # Automatically mapped to sys_id
}

incidents = await query_table_with_filters(
    "incident",
    TableFilterParams(filters=filters)
)
```

## 🚀 New Features to Adopt

### 1. AI-Powered Search
Take advantage of natural language queries:

```python
# Instead of building complex filters manually...
# Use natural language:
result = await intelligent_search(IntelligentQueryParams(
    query="unassigned critical tickets from today",
    table="incident"
))
```

### 2. Predefined Templates
Use ready-made filter patterns:

```python
from Table_Tools.intelligent_query_tools import get_servicenow_filter_templates

templates = get_servicenow_filter_templates()
high_priority_filters = templates["templates"]["high_priority_last_week"]["filters"]

incidents = await query_table_with_filters("incident", TableFilterParams(filters=high_priority_filters))
```

### 3. Generic Table Operations
Work with any ServiceNow table using generic functions:

```python
from Table_Tools.generic_table_tools import (
    query_table_by_text,
    get_records_by_priority,
    query_table_intelligently
)

# Works with any table
any_table_results = await query_table_by_text("your_custom_table", "search text")
priority_records = await get_records_by_priority("incident", ["1", "2"])
```

## 🔧 Testing Your Migration

### 1. Verify Authentication
```python
from utility_tools import nowtestoauth

auth_result = await nowtestoauth()
print(auth_result)  # Should show OAuth success
```

### 2. Test Basic Functionality
```python
# Test consolidated tools
incident = await get_incident_details("INC0001234")
print(incident)

# Test AI features
ai_result = await intelligent_search(IntelligentQueryParams(
    query="test query",
    table="incident"
))
print(ai_result)
```

### 3. Run Test Suite
```bash
# Run the comprehensive tests
python Testing/test_consolidated_tools.py
python Testing/test_query_intelligence.py
```

## 📚 Additional Resources

- **OAuth Setup**: See `OAUTH_SETUP_GUIDE.md` for complete OAuth configuration
- **AI Features**: Check `Diagrams & Documentation/05-ai-intelligence-flow.md`
- **API Reference**: Updated in `README.md` with all v2.0 functions
- **Examples**: See `Testing/TEST_PROMPTS.md` for extensive examples

## ❓ Common Migration Issues

### Issue: Import Error
```
ModuleNotFoundError: No module named 'Table_Tools.incident_tools'
```
**Solution**: Update imports to use `consolidated_tools.py`

### Issue: Authentication Failed
```
Authentication test failed - unable to access ServiceNow API
```
**Solution**: Configure OAuth 2.0 credentials in `.env` file

### Issue: Function Not Found
```
AttributeError: module has no attribute 'getIncidentByNumber'
```
**Solution**: Update function names to snake_case versions

## 🎯 Benefits After Migration

- ✅ **AI-Powered Queries**: Natural language to ServiceNow filtering
- ✅ **Enhanced Security**: OAuth 2.0 only authentication
- ✅ **Better Performance**: Optimized queries and pagination
- ✅ **ReDoS Protection**: Security against malicious regex attacks
- ✅ **Unified API**: Consistent interface across all functions
- ✅ **Future-Proof**: Modern architecture ready for enhancements

The migration provides significant improvements in functionality, security, and maintainability while maintaining all existing capabilities through the new consolidated architecture.