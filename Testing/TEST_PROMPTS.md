# Test Prompts for ServiceNow MCP Functionality

## Updated for Consolidated Architecture (Post-Optimization)

> **Note**: This MCP server now uses a consolidated, generic architecture with 70% fewer files and enhanced performance. All tool names remain the same for backward compatibility, but internally use optimized generic functions.

## Test Prompt 1: Basic Server Connectivity & Authentication

```
Test the following tools in sequence:
1. Call `nowtest()` to verify the MCP server is running
2. Call `now_test_oauth()` to test OAuth 2.0 authentication  
3. Call `now_auth_info()` to check current authentication method
4. Call `nowtestauth()` to test authenticated access to ServiceNow custom API
5. Call `nowtest_auth_input("incident")` to get table description for the incident table

Expected Results:
- nowtest(): Should return "Server is running and ready to handle requests!"
- now_test_oauth(): Should return OAuth connection status and details
- now_auth_info(): Should return {"oauth_enabled": true, "instance_url": "https://your-instance.service-now.com", "auth_method": "oauth"}
- nowtestauth(): Should return authentication success with ServiceNow API access confirmation
- nowtest_auth_input(): Should return table schema info including sample fields and accessibility status
```

## Test Prompt 2: Incident Management Tools (Using Generic Architecture)

```
Test incident-related functionality (now powered by generic table functions):
1. Call `similar_incidents_for_text("server down database error")` to find similar incidents
2. Call `get_short_desc_for_incident("INC0129646")` to get description of a specific incident
3. Call `get_incident_details("INC0129646")` to get full details of the same incident
4. Call `similar_incidents_for_incident("INC0129646")` to find incidents similar to INC0129646
5. Call `get_incidents_by_filter({"state": "1", "priority": "1"}, ["number", "short_description", "state"])` with custom filters
6. Call `get_priority_incidents(["1", "2"], {"state": "1"})` to test priority filtering with OR syntax

Expected Results:
- Text search uses optimized regex-based keyword extraction (no SpaCy dependency)
- Keywords extracted: ["server", "database", "error"] - more focused than before
- Description lookup should return short_description field or table-specific error message
- Details should return comprehensive incident information using generic get_record_details()
- Similar incident search uses generic find_similar_records() function
- Filter search uses intelligent filtering with natural language parsing
- Priority search demonstrates proper ServiceNow OR syntax: "priority=1^ORpriority=2"
```

## Test Prompt 3: Change Request Management Tools (Using Generic Architecture)

```
Test change request functionality (internally uses query_table_by_text("change_request", ...)):
1. Call `similar_changes_for_text("system upgrade maintenance window")` to find related changes
2. Call `get_short_desc_for_change("CHG0000001")` to get description of a specific change
3. Call `get_change_details("CHG0000001")` to get full change details
4. Call `similar_changes_for_change("CHG0000001")` to find similar changes

Expected Results:
- All functions use the same generic architecture as incidents, just with table="change_request"
- Keywords extracted: ["system", "upgrade", "maintenance", "window"] using lightweight regex
- Should return appropriate change request data or table-specific error messages from constants.py
- Field structure optimized: 4 essential fields for basic queries, expanded for detailed queries
- All operations maintain backward compatibility while using generic functions underneath
```

## Test Prompt 4: User Request (Service Catalog) Management Tools (Using Generic Architecture)

```
Test User Request functionality (internally uses table="sc_req_item"):
1. Call `similar_ur_for_text("password reset account locked")` to find related URs
2. Call `get_short_desc_for_ur("RITM0073721")` to get description of a specific UR
3. Call `get_ur_details("RITM0073721")` to get full UR details  
4. Call `similar_urs_for_ur("RITM0073721")` to find similar URs

Expected Results:
- All UR functions use generic architecture with table="sc_req_item" (Service Catalog Request Items)
- Keywords extracted: ["password", "reset", "account", "locked"] using optimized regex
- Should handle Request Item records with number prefix "RITM" (not "UR")
- Return UR-specific data or error messages: "UR not found." from TABLE_ERROR_MESSAGES
- Maintain same field optimization: 4 essential vs expanded detailed fields from constants.py
- All operations use the same generic functions as incidents/changes underneath
```

## Test Prompt 5: Knowledge Base Management Tools (Using Generic Architecture)

```
Test knowledge base functionality (internally uses table="kb_knowledge"):
1. Call `similar_knowledge_for_text("VPN connection troubleshooting", None, "IT")` to search knowledge articles
2. Call `get_knowledge_details("KB0000001")` to get specific knowledge article details
3. Call `get_knowledge_by_category("IT")` to get knowledge articles by category
4. Call `get_active_knowledge_articles("troubleshooting")` to get active knowledge articles

Expected Results:
- Knowledge search uses query_table_with_generic_filters() when category/kb_base provided
- Keywords extracted: ["connection", "troubleshooting"] (VPN filtered as stop word)
- Details lookup uses generic get_record_details("kb_knowledge", record_number)
- Category filter uses query_table_with_generic_filters() with {"kb_category": "IT"}
- Active articles filter by {"state": "published"} using generic filtering
- Should handle optional parameters (kb_base, category) through enhanced generic functions
- Error messages: "Knowledge article not found." from TABLE_ERROR_MESSAGES
- No priority field support (TABLE_CONFIGS shows priority_field: None for kb_knowledge)
```

## Test Prompt 6: Private Task Management Tools (CRUD Operations - Using Generic + Specialized)

```
Test Private Task functionality with full CRUD operations (vtb_task table):

### Read Operations (Using Generic Architecture):
1. Call `similar_private_tasks_for_text("server maintenance database backup")` to find private tasks matching text
2. Call `get_short_desc_for_private_task("VTB0001234")` to get description of a specific private task
3. Call `get_private_task_details("VTB0001234")` to get full private task details
4. Call `similar_private_tasks_for_private_task("VTB0001234")` to find similar private tasks
5. Call `get_private_tasks_by_filter({"state": "1", "priority": "2"})` with custom filters

### Create & Update Operations (Specialized VTB functions):
6. Call `create_private_task({
    "short_description": "Test private task creation",
    "description": "This is a test private task created via MCP",
    "priority": "3",
    "assigned_to": "admin"
})` to create a new private task

7. Call `update_private_task("VTB0001234", {
    "state": "2",
    "comments": "Updated via MCP test",
    "priority": "1"
})` to update an existing private task

Expected Results:
- Read operations use generic functions with table="vtb_task"
- Keywords extracted: ["server", "maintenance", "database", "backup"] using regex extraction
- Description lookup should return short_description field or "Private Task not found."
- Details should return comprehensive private task information with extended fields
- Similar task search should work based on the reference task's description
- Filter search should return private tasks matching the specified criteria
- Create operation should return the newly created private task details with generated number
- Update operation should return the updated private task details or error if task not found
- OAuth 2.0 ONLY authentication (Basic Auth removed for enhanced security)
- Note: Uses vtb_task table internally but presents as "Private Tasks" to users
- CRUD operations kept specialized since they require ServiceNow write permissions
```

## Test Prompt 7: Intelligent Query Tools (🚀 NEW AI-Powered Architecture)

```
Test the revolutionary AI-powered natural language query functionality:

### Natural Language Search:
1. Call `intelligent_search({"query": "high priority incidents from last week", "table": "incident"})` for conversational search
2. Call `intelligent_search({"query": "unassigned critical tickets from today", "table": "incident"})` for real-time queries
3. Call `intelligent_search({"query": "resolved P1 incidents this month", "table": "incident"})` for historical analysis
4. Call `intelligent_search({"query": "active changes for database servers", "table": "change_request"})` for cross-table intelligence

### Smart Filter Building:
5. Call `build_smart_servicenow_filter({"query": "P1 and P2 tickets from August 25-31, 2025", "table": "incident"})` to build filters without executing
6. Call `build_smart_servicenow_filter({"query": "critical incidents from yesterday", "table": "incident"})` for recent events

### Filter Intelligence & Explanation:
7. Call `explain_servicenow_filters({"filters": {"priority": "1^ORpriority=2", "sys_created_on": ">=2025-08-25"}, "table": "incident"})` to understand complex filters
8. Call `explain_servicenow_filters({"filters": {"priority": "1,2", "state": "!=6"}, "table": "incident"})` to catch syntax issues

### Pre-built Templates:
9. Call `get_servicenow_filter_templates()` to get enterprise-grade filter templates
10. Call `get_query_examples()` to get comprehensive natural language examples

Expected Results:
- 🧠 **AI-Powered Parsing**: Natural language automatically converted to proper ServiceNow syntax
- 📅 **Intelligent Date Parsing**: "last week" → proper BETWEEN syntax with JavaScript date functions
- 🎯 **Smart Priority Parsing**: "P1 and P2" → "priority=1^ORpriority=2" (proper OR syntax)
- 🔍 **Filter Explanations**: Include SQL equivalents, potential issues, and improvement suggestions
- 📋 **Enterprise Templates**: Pre-built filters for common business scenarios
- 🛡️ **Security Features**: ReDoS protection and input validation
- 📊 **Intelligence Metadata**: Confidence scores, template usage, and query explanations
- ✅ **Cross-Table Support**: All intelligent tools work across incident, change, knowledge, and task tables
```

## 🚀 NEW: Test Prompt 8: Consolidated Architecture Validation

```
Validate that the new consolidated architecture maintains all functionality:

### Test Consolidated Tools Import Structure:
1. Run `python Testing/test_consolidated_tools.py` to validate all tool imports
2. Verify all functions from deleted files are accessible through consolidated_tools.py

### Test Architecture Consolidation:
3. Call incident tools: `similar_incidents_for_text("database error")`, `get_incident_details("INC0010001")`
4. Call change tools: `similar_changes_for_text("system upgrade")`, `get_change_details("CHG0000001")`
5. Call UR tools: `similar_ur_for_text("password reset")`, `get_ur_details("RITM0000001")`
6. Call knowledge tools: `similar_knowledge_for_text("troubleshooting")`, `get_knowledge_details("KB0000001")`
7. Call private task tools: `similar_private_tasks_for_text("maintenance")`, `get_private_task_details("VTB0000001")`

### Test Generic Functions Power All Operations:
8. Verify that all tools use the same underlying generic functions
9. Test that table-specific error messages are maintained from constants.py
10. Confirm that priority filtering works for supported tables (incident, change, vtb_task)
11. Validate that knowledge base correctly handles tables without priority fields

Expected Results:
- ✅ **Zero Functional Regression**: All tools work exactly as before
- ✅ **Unified Architecture**: All operations powered by generic functions
- ✅ **Table-Specific Behavior**: Proper error messages and field handling per table
- ✅ **Backward Compatibility**: Existing tool names and interfaces maintained
- ✅ **Import Validation**: All 20+ functions importable from consolidated_tools.py
- ✅ **Performance Benefits**: Faster keyword extraction, better error handling
```

## 🛡️ NEW: Test Prompt 9: Security & ReDoS Protection Validation

```
Test the enhanced security features and ReDoS protection:

### ReDoS Protection Testing:
1. Run `python Testing/test_query_intelligence.py` (includes ReDoS tests)
2. Test malicious regex inputs with natural language parsing
3. Validate timeout protection on Windows systems
4. Test input length validation (>200 chars rejected)
5. Test pattern validation (suspicious character counts)

### Security Input Testing:
6. Test SQL injection attempts: `intelligent_search({"query": "'; DROP TABLE incidents; --", "table": "incident"})`
7. Test XSS attempts: `intelligent_search({"query": "<script>alert('xss')</script>", "table": "incident"})`
8. Test path traversal: `intelligent_search({"query": "../../etc/passwd", "table": "incident"})`
9. Test buffer overflow: `intelligent_search({"query": "a" * 1000, "table": "incident"})`

### Input Validation:
10. Test empty queries, invalid table names, malformed filters
11. Verify all dangerous inputs are handled safely without crashes
12. Confirm error messages don't expose sensitive information

Expected Results:
- 🛡️ **ReDoS Protection**: Malicious regex patterns safely rejected
- ⏱️ **Timeout Protection**: Windows-compatible protection against long operations
- 📏 **Input Validation**: Overly long or suspicious inputs rejected
- 🔒 **Security Handling**: SQL injection, XSS, and path traversal attempts neutralized
- ⚠️ **Safe Error Handling**: No crashes or information disclosure
- 🧪 **Comprehensive Testing**: All attack vectors tested and protected
```

## Validation Checklist (Updated for Consolidated Architecture)

After running each test prompt, verify:

### ✅ **Architecture Optimization**

- [ ] All tool names work exactly as before (backward compatibility maintained)
- [ ] Generic functions handle all table types uniformly
- [ ] SpaCy dependency eliminated - regex-based keyword extraction working
- [ ] orjson added for enhanced JSON performance
- [ ] Cognitive complexity of all functions remains under 15

### ✅ **Performance Improvements**

- [ ] Keywords extracted are more focused (no stop words, 4+ char minimum)
- [ ] Error messages use centralized TABLE_ERROR_MESSAGES from constants.py
- [ ] API queries built using helper functions (_build_url_with_params, etc.)
- [ ] ServiceNow record numbers (INC, CHG, KB, RITM, VTB) detected by compiled regex patterns

### ✅ **Enhanced Error Handling**

- [ ] Table-specific error messages: "Incident not found.", "Change not found.", etc.
- [ ] Generic error handling with fallbacks from constants.py
- [ ] OAuth 2.0 only authentication (Basic Auth removed)
- [ ] Table configuration validation (TABLE_CONFIGS checks)

### ✅ **Generic Architecture Benefits**

- [ ] Same 4 core functions work for all table types (text search, description, details, similar)
- [ ] Priority filtering works for tables that support it (incidents, changes, VTB tasks)
- [ ] Knowledge Base correctly handles tables without priority fields
- [ ] All operations use the same underlying generic functions while maintaining table-specific interfaces

## 🚀 NEW: Automated Test Suite Execution

### **Run Complete Test Suite:**

```bash
# Run all modernized tests in sequence
python Testing/test_oauth_simple.py                    # OAuth authentication
python Testing/test_consolidated_tools.py              # Consolidated architecture
python Testing/test_query_intelligence.py              # AI features + security
python Testing/test_cmdb_tools.py                     # CMDB tools (snake_case)
python Testing/test_filtering_fixes.py                # ServiceNow filtering
```

### **Test Coverage Summary:**
- **OAuth Authentication**: Connection and credential validation
- **Consolidated Architecture**: Backward compatibility and zero regression
- **AI-Powered Intelligence**: Natural language processing and smart filtering
- **Security Features**: ReDoS protection, input validation, attack resistance
- **CMDB Operations**: Configuration item discovery and search
- **ServiceNow Filtering**: Date parsing, priority OR syntax, caller exclusions

## Expected Performance Improvements (After Consolidation)

Compare before/after optimization results:

### **Code Reduction & Architecture (Achieved)**

- **Individual Table Files**: 4 files eliminated (incident_tools.py, change_tools.py, ur_tools.py, kb_tools.py)
- **Function Consolidation**: 25+ table-specific functions → 5 generic functions + AI intelligence
- **Code Duplication**: 200+ duplicate strings → centralized in constants.py
- **Architecture**: From scattered table tools → unified generic architecture with AI
- **Test Modernization**: Fixed broken imports, updated naming, added comprehensive coverage

### **New AI & Security Features (Added)**

- **🧠 Natural Language Processing**: Advanced query intelligence with confidence scoring
- **🛡️ ReDoS Protection**: Windows-compatible timeout and input validation
- **📋 Smart Templates**: Pre-built enterprise filter patterns
- **🔍 Filter Intelligence**: Automatic explanation and SQL generation
- **⚡ Performance**: Faster regex vs SpaCy, optimized JSON parsing

### **Testing Infrastructure (Enhanced)**

- **✅ Fixed Broken Tests**: Updated imports and function names
- **🆕 Consolidated Test**: Comprehensive validation of architectural changes
- **🔒 Security Testing**: ReDoS protection and attack resistance validation
- **📊 AI Testing**: Natural language processing and intelligent query validation
- **🏗️ Architecture Testing**: Zero regression validation for all consolidated functionality

### **Quality Assurance (Maintained)**

- **All Functions**: Maintained under 15 cognitive complexity limit
- **Helper Functions**: Single responsibility principle throughout
- **Code Quality**: Enhanced maintainability with modular design
- **SonarCloud Compliance**: All naming violations and complexity issues resolved
- **Test Coverage**: Comprehensive testing for all major functionality

## Notes for Testing (Updated for Consolidated Architecture)

### **Testing Strategy**

- Replace example record numbers (INC0010001, CHG0000001, RITM0073721, VTB0001234, KB0000001) with actual records
- Adjust search terms to match your ServiceNow data
- Test regex keyword extraction with ServiceNow record numbers and content keywords
- Verify all 41 MCP tools are properly registered

### **Validation Focus Areas**

- **Generic Function Coverage**: Ensure all table types work with same core functions
- **Error Message Consistency**: Verify table-specific error messages from constants.py
- **Authentication**: Test OAuth 2.0 only authentication (Basic Auth removed)
- **Backward Compatibility**: Confirm all existing tool names continue to work
- **Performance**: Monitor improved keyword extraction and JSON parsing speeds

### **Architecture Validation**

- Verify generic functions handle all 5 table types: incident, change_request, sc_req_item, kb_knowledge, vtb_task
- Test TABLE_CONFIGS metadata drives table-specific behavior correctly
- Confirm cognitive complexity remains under 15 for all functions
- Validate helper functions properly separate concerns
