# Test Prompts for ServiceNow MCP Functionality - V2 Optimized

## Updated for V2 Architecture with Practical Testing Scenarios

> **Note**: This MCP server uses the consolidated V2 architecture with AI-powered intelligence and optimized for real-world ServiceNow environments with 100k+ records. All tests designed for practical result sets and business scenarios.

## Test Prompt 1: Authentication & Server Connectivity

```
Test the following tools in sequence:
1. Call `nowtest()` to verify the MCP server is running
2. Call `now_test_oauth()` to test OAuth 2.0 authentication
3. Call `now_auth_info()` to check current authentication method
4. Call `nowtestauth()` to test authenticated access to ServiceNow API
5. Call `nowtest_auth_input("incident")` to get table description for the incident table

Expected Results:
- nowtest(): Should return "Server is running and ready to handle requests!"
- now_test_oauth(): Should return OAuth connection status and details
- now_auth_info(): Should return {"oauth_enabled": true, "instance_url": "https://your-instance.service-now.com", "auth_method": "oauth"}
- nowtestauth(): Should return authentication success with ServiceNow API access confirmation
- nowtest_auth_input(): Should return table schema info including sample fields and accessibility status
```

## Test Prompt 2: Practical Incident Management (Optimized for Large Datasets)

```
Test incident functionality with realistic, time-bounded queries for large ServiceNow environments:

### Recent High-Priority Incidents (Manageable Result Sets):
1. Call `get_incidents_by_filter({"priority": "1", "sys_created_on": ">=javascript:gs.dateGenerate(gs.hoursAgo(24))"})` - P1 incidents from last 24 hours
2. Call `get_incidents_by_filter({"priority": "1,2", "state": "1", "sys_created_on": ">=javascript:gs.dateGenerate(gs.daysAgo(3))"})` - P1/P2 active incidents from last 3 days
3. Call `get_incidents_by_filter({"state": "6", "priority": "1", "sys_created_on": "BETWEEN javascript:gs.dateGenerate(gs.daysAgoStart(7))@javascript:gs.dateGenerate(gs.daysAgoEnd(1))"})` - P1 incidents resolved in last week

### Text-Based Discovery (Find Real Records):
4. Call `similar_incidents_for_text("database connection error timeout")` - Find existing database-related incidents
5. Use one incident number from step 4 results, then call `get_incident_details("[FOUND_INCIDENT_NUMBER]")` to get full details
6. Call `similar_incidents_for_incident("[FOUND_INCIDENT_NUMBER]")` to find similar incidents

### Business Scenario Testing:
7. Call `get_incidents_by_filter({"assignment_group": "[YOUR_TEAM_SYS_ID]", "state": "1,2,3", "priority": "1,2", "sys_created_on": ">=javascript:gs.dateGenerate(gs.hoursAgo(48))"})` - Team's active critical work from last 48 hours

Expected Results:
- Time-bounded queries return manageable result sets (typically 5-50 records vs thousands)
- Text search discovers actual existing incidents with database-related content
- Similar incident search provides relevant matches based on real incident data
- Business scenario demonstrates practical daily operations workflow
- All queries complete within reasonable time (< 30 seconds)
- Priority parsing uses proper ServiceNow OR syntax: "priority=1^ORpriority=2"
```

## Test Prompt 3: AI-Powered Intelligent Search (New V2 Feature)

```
Test the revolutionary natural language query capabilities:

### Conversational Queries:
1. Call `intelligent_search({"query": "critical incidents from today that are unassigned", "table": "incident"})` - Natural language to ServiceNow syntax
2. Call `intelligent_search({"query": "database outage reports from this morning", "table": "incident"})` - Time-specific search
3. Call `intelligent_search({"query": "P1 tickets resolved in the last 48 hours", "table": "incident"})` - Recent resolution analysis

### Smart Filter Building (Without Execution):
4. Call `build_smart_servicenow_filter({"query": "high priority incidents assigned to infrastructure team from yesterday", "table": "incident"})` - Complex filter generation
5. Call `build_smart_servicenow_filter({"query": "network issues reported between 2-6 PM today", "table": "incident"})` - Time range parsing

### Filter Intelligence & Templates:
6. Call `get_servicenow_filter_templates()` - Get pre-built business scenario filters
7. Call `explain_servicenow_filters({"filters": {"priority": "1^ORpriority=2", "state": "!=6", "sys_created_on": ">=javascript:gs.hoursAgo(24)"}, "table": "incident"})` - Understand complex filters
8. Call `get_query_examples()` - Get comprehensive natural language examples

Expected Results:
- Natural language automatically converted to proper ServiceNow encoded syntax
- Time expressions like "today", "this morning", "yesterday" parsed to JavaScript date functions
- Priority expressions "critical", "P1", "high priority" converted to correct priority values
- Smart filters include confidence scores and explanations
- Templates provide enterprise-ready filter patterns for common scenarios
- Filter explanations include SQL equivalents and optimization suggestions
```

## Test Prompt 4: Change Management with Intelligence

```
Test change request functionality with realistic business scenarios:

### Recent Change Discovery:
1. Call `similar_changes_for_text("database upgrade maintenance window")` to find existing maintenance changes
2. Use one change number from results, then call `get_change_details("[FOUND_CHANGE_NUMBER]")` to get comprehensive details
3. Call `similar_changes_for_change("[FOUND_CHANGE_NUMBER]")` to find related changes

### AI-Powered Change Analysis:
4. Call `intelligent_search({"query": "emergency changes implemented this week", "table": "change_request"})` - Recent emergency change review
5. Call `intelligent_search({"query": "scheduled maintenance changes for next weekend", "table": "change_request"})` - Upcoming maintenance planning

### Business Process Testing:
6. Call `build_smart_servicenow_filter({"query": "approved changes scheduled for implementation in next 7 days", "table": "change_request"})` - Change implementation planning

Expected Results:
- Text search discovers actual change requests with maintenance-related content
- Similar change search finds related infrastructure or maintenance changes
- AI queries properly parse "emergency" vs "scheduled" change types
- Time-based queries handle "this week", "next weekend", "next 7 days" intelligently
- Results focus on actionable business information for change management workflows
```

## Test Prompt 5: Service Catalog Request Items (Optimized)

```
Test Service Catalog Request Item functionality with realistic support scenarios:

### Support Request Discovery:
1. Call `similar_request_items_for_text("password reset account locked access")` to find existing access-related requests
2. Use one RITM number from results, then call `get_request_item_details("[FOUND_RITM_NUMBER]")` for comprehensive details
3. Call `similar_request_items_for_request_item("[FOUND_RITM_NUMBER]")` to find similar access requests

### AI-Powered Request Analysis:
4. Call `intelligent_search({"query": "new user onboarding requests from this week", "table": "sc_req_item"})` - Onboarding workflow analysis
5. Call `intelligent_search({"query": "software license requests pending approval", "table": "sc_req_item"})` - License management workflow

### Support Operations:
6. Call `build_smart_servicenow_filter({"query": "access requests submitted today that need immediate attention", "table": "sc_req_item"})` - Daily support prioritization

Expected Results:
- Text search finds actual password/access-related request items
- Similar request search identifies patterns in access request handling
- AI queries distinguish between different request types (onboarding, licensing, access)
- Time-based analysis supports daily support operations
- Results provide actionable insights for service catalog management
```

## Test Prompt 6: Universal Requests (New)
```Test Universal Request functionality with enterprise-wide request scenarios:
### Universal Request Discovery:1. Call `similar_universal_requests_for_text("department budget approval workflow")` to find existing enterprise-level requests2. Use one UR number from results, then call `get_universal_request_details("[FOUND_UR_NUMBER]")` for comprehensive details3. Call `similar_universal_requests_for_universal_request("[FOUND_UR_NUMBER]")` to find similar universal requests
### AI-Powered Universal Request Analysis:4. Call `intelligent_search({"query": "enterprise-wide policy changes from this quarter", "table": "universal_request"})` - Policy change tracking5. Call `intelligent_search({"query": "high-priority organizational requests pending approval", "table": "universal_request"})` - Executive workflow analysis
### Enterprise Operations:6. Call `build_smart_servicenow_filter({"query": "department requests submitted this month requiring executive approval", "table": "universal_request"})` - Executive dashboard preparation
Expected Results:- Text search finds actual enterprise/organizational Universal Requests- Similar request search identifies patterns in organizational request handling- AI queries distinguish between different universal request types (policy, budget, organizational)- Time-based analysis supports enterprise planning and approval workflows- Results provide insights for executive decision-making and organizational change management```
## Test Prompt 7: Knowledge Base Intelligence & Discovery

```
Test knowledge base functionality with practical search scenarios:

### Knowledge Discovery:
1. Call `similar_knowledge_for_text("VPN connection troubleshooting steps remote access")` - Find existing troubleshooting articles
2. Use one KB number from results, then call `get_knowledge_details("[FOUND_KB_NUMBER]")` for full article content
3. Call `get_active_knowledge_articles("network connectivity")` - Get all active network-related articles

### AI-Powered Knowledge Search:
4. Call `intelligent_search({"query": "troubleshooting guides for database connection issues", "table": "kb_knowledge"})` - Specific problem-solution matching
5. Call `intelligent_search({"query": "step-by-step guides published in the last 30 days", "table": "kb_knowledge"})` - Recent knowledge updates

### Knowledge Management:
6. Call `get_knowledge_by_category("IT")` - Category-based knowledge organization
7. Call `build_smart_servicenow_filter({"query": "frequently accessed troubleshooting articles this month", "table": "kb_knowledge"})` - Popular content analysis

Expected Results:
- Text search discovers actual VPN and network troubleshooting articles
- Knowledge details include comprehensive article content and metadata
- AI queries match problems to appropriate solution articles
- Category filtering organizes knowledge by business domain
- Active article search focuses on current, maintained knowledge
- Popular content analysis identifies most valuable knowledge assets
```

## Test Prompt 7: Private Task Management with CRUD Validation

```
Test Private Task functionality with comprehensive CRUD operations:

### Task Discovery & Reading:
1. Call `similar_private_tasks_for_text("server maintenance database backup")` to find existing maintenance tasks
2. Use one VTB number from results, then call `get_private_task_details("[FOUND_VTB_NUMBER]")` for full task details
3. Call `get_private_tasks_by_filter({"state": "1", "priority": "1,2", "sys_created_on": ">=javascript:gs.dateGenerate(gs.daysAgo(7))"})` - Active high-priority tasks from last week

### AI-Powered Task Intelligence:
4. Call `intelligent_search({"query": "urgent maintenance tasks scheduled for this weekend", "table": "vtb_task"})` - Weekend maintenance planning
5. Call `build_smart_servicenow_filter({"query": "overdue high priority tasks assigned to my team", "table": "vtb_task"})` - Task backlog analysis

### CRUD Operations Testing:
6. Call `create_private_task({
    "short_description": "Test task - Network backup validation",
    "description": "Validate network backup procedures for DR testing - Created via MCP testing",
    "priority": "3",
    "assigned_to": "admin",
    "state": "1"
})` - Create test task with realistic content

7. Use the created task number from step 6, then call `update_private_task("[CREATED_VTB_NUMBER]", {
    "state": "3",
    "comments": "Task completed successfully via MCP test automation",
    "priority": "4"
})` - Update task to completed state

### Error Handling Validation:
8. Call `get_private_task_details("VTB9999999")` - Test error handling for non-existent task
9. Call `update_private_task("VTB9999999", {"state": "2"})` - Test update error handling

Expected Results:
- Text search finds actual maintenance-related private tasks
- Time-bounded filters return manageable result sets for task management
- AI queries properly interpret "urgent", "overdue", "scheduled" task states
- Create operation returns newly created task with generated VTB number
- Update operation successfully modifies task state and adds comments
- Error handling provides appropriate "Private Task not found" messages
- All CRUD operations maintain proper OAuth 2.0 authentication
```

## Test Prompt 8: Performance & Scale Validation (New)

```
Test system performance and handling of large datasets:

### Response Time Validation:
1. Call `intelligent_search({"query": "incidents from today", "table": "incident"})` - Should complete in < 10 seconds
2. Call `get_incidents_by_filter({"sys_created_on": ">=javascript:gs.dateGenerate(gs.hoursAgo(24))"})` - 24-hour data retrieval timing
3. Call `similar_incidents_for_text("network connectivity")` - Text search performance with large corpus

### Pagination & Large Result Handling:
4. Call `get_incidents_by_filter({"sys_created_on": ">=javascript:gs.dateGenerate(gs.daysAgo(30))", "priority": "3,4,5"})` - Month of lower priority incidents (expect pagination)
5. Monitor result count and verify complete data retrieval despite ServiceNow query limits

### Memory & Resource Efficiency:
6. Call multiple concurrent searches to test resource handling:
   - `similar_incidents_for_text("database")`
   - `similar_changes_for_text("maintenance")`
   - `similar_knowledge_for_text("troubleshooting")`

### Error Rate Monitoring:
7. Track success/failure rates across all previous test prompts
8. Validate that error messages are informative and don't expose sensitive data

Expected Results:
- All queries complete within acceptable time limits (< 30 seconds typical, < 60 seconds maximum)
- Pagination handles large result sets transparently without data loss
- Concurrent searches execute successfully without resource conflicts
- Memory usage remains stable during large data operations
- Error rates remain low (< 5% for valid queries)
- System maintains performance with 150k+ record databases
```

## Test Prompt 9: Real-World Business Scenarios (New)

```
Test realistic daily operations workflows:

### Daily Operations Workflow:
1. Call `intelligent_search({"query": "what critical issues need immediate attention today", "table": "incident"})` - Daily priority triage
2. Call `intelligent_search({"query": "show me P1 incidents assigned to my team that are still open", "table": "incident"})` - Team workload assessment
3. Call `intelligent_search({"query": "changes scheduled for implementation today", "table": "change_request"})` - Daily change coordination

### Weekly Review Workflow:
4. Call `intelligent_search({"query": "show me all P1 incidents resolved this week", "table": "incident"})` - Weekly performance review
5. Call `intelligent_search({"query": "emergency changes implemented in the last 7 days", "table": "change_request"})` - Emergency change analysis
6. Call `intelligent_search({"query": "new knowledge articles published this week", "table": "kb_knowledge"})` - Knowledge base updates

### Troubleshooting Workflow:
7. Call `similar_incidents_for_text("database timeout connection pool")` - Find similar past issues
8. Use one incident from results, then call `similar_knowledge_for_text("database timeout troubleshooting")` - Find relevant solutions
9. Call `intelligent_search({"query": "similar database issues resolved in the last 30 days", "table": "incident"})` - Recent resolution patterns

### Reporting & Analytics:
10. Call `build_smart_servicenow_filter({"query": "incidents by priority breakdown for this month", "table": "incident"})` - Monthly metrics preparation
11. Call `explain_servicenow_filters({"filters": {"state": "6", "sys_resolved_on": ">=javascript:gs.dateGenerate(gs.monthsAgo(1))"}, "table": "incident"})` - Understand resolution metrics

Expected Results:
- Daily workflows provide actionable, current information for immediate decisions
- Weekly reviews offer comprehensive period analysis for performance assessment
- Troubleshooting workflows connect problems to solutions across knowledge domains
- Reporting filters generate proper ServiceNow syntax for business intelligence
- All scenarios complete quickly enough for interactive use (< 15 seconds typical)
- Results directly support real ServiceNow administrator and analyst workflows
```

## Test Prompt 10: Security & ReDoS Protection Validation (Enhanced)

```
Test enhanced security features and ReDoS protection:

### ReDoS Protection Testing:
1. Test malicious regex patterns: `intelligent_search({"query": "a?a?a?a?a?a?a?a?a?a?a?a?a?a?a?a?a?a?a?a?a?a?a?a?a?a?a?a?a?a?aaaaaaaaaaaaaaaaaaaaaaaaa", "table": "incident"})` - Should timeout safely
2. Test excessive input length: `intelligent_search({"query": "${"a".repeat(500)}", "table": "incident"})` - Should reject long input
3. Test suspicious pattern counts: `intelligent_search({"query": "((((((((((nested regex))))))))", "table": "incident"})` - Should validate and reject

### Security Input Testing:
4. Test SQL injection attempts: `intelligent_search({"query": "'; DROP TABLE incidents; --", "table": "incident"})` - Should sanitize safely
5. Test XSS attempts: `intelligent_search({"query": "<script>alert('xss')</script>", "table": "incident"})` - Should handle safely
6. Test path traversal: `intelligent_search({"query": "../../etc/passwd", "table": "incident"})` - Should treat as search text
7. Test command injection: `intelligent_search({"query": "; rm -rf /", "table": "incident"})` - Should sanitize safely

### Input Validation Edge Cases:
8. Test empty queries: `intelligent_search({"query": "", "table": "incident"})` - Should provide meaningful error
9. Test invalid table names: `intelligent_search({"query": "test", "table": "invalid_table"})` - Should validate table existence
10. Test malformed JSON in filters: `build_smart_servicenow_filter({"query": "test", "table": "incident", "context": "{malformed json}"})` - Should handle gracefully

### Windows Timeout Protection:
11. Run multiple concurrent ReDoS tests to validate Windows-compatible timeout protection
12. Verify system remains responsive during timeout protection activation

Expected Results:
- ReDoS patterns are detected and rejected before processing with informative error messages
- Timeout protection engages on Windows systems without system crashes
- All injection attempts are safely neutralized without executing malicious code
- Input validation prevents crashes from malformed or excessive input
- Error messages are informative but don't expose sensitive system information
- System maintains security posture under concurrent attack simulation
- All dangerous inputs log appropriately for security monitoring
```

## Automated Test Suite Execution

```bash
# Run all V2 optimized tests in sequence
python Testing/test_oauth_simple.py                    # Authentication validation
python Testing/test_consolidated_tools.py              # Architecture consolidation
python Testing/test_query_intelligence.py              # AI features + security
python Testing/test_cmdb_tools.py                     # CMDB tools validation
python Testing/test_filtering_fixes.py                # ServiceNow filtering
python Testing/test_performance_validation.py         # New: Performance testing (if created)
python Testing/test_business_scenarios.py             # New: Business workflow testing (if created)
```

## Validation Checklist for V2 Architecture

### ✅ **Practical Testing Standards**
- [ ] All incident queries return manageable result sets (< 100 records typically)
- [ ] Time-bounded queries use recent data (24h, 48h, 1 week maximum)
- [ ] Business scenarios reflect real daily operations workflows
- [ ] AI queries demonstrate natural language understanding
- [ ] Performance tests complete within acceptable time limits (< 30 seconds)

### ✅ **Result Quality Validation**
- [ ] Text searches discover actual relevant records from your ServiceNow instance
- [ ] Similar record searches provide meaningful matches
- [ ] Priority filtering uses proper ServiceNow OR syntax
- [ ] Date ranges parse correctly to JavaScript date functions
- [ ] Error handling provides informative messages without system exposure

### ✅ **Architecture Optimization Verification**
- [ ] All 40+ MCP tools are accessible and functional
- [ ] Generic functions handle all table types uniformly
- [ ] OAuth 2.0 authentication works exclusively (Basic Auth removed)
- [ ] AI-powered features demonstrate intelligence and accuracy
- [ ] Security features protect against ReDoS and injection attacks

### ✅ **Business Value Confirmation**
- [ ] Daily operations workflows provide actionable information
- [ ] Weekly review scenarios support performance analysis
- [ ] Troubleshooting workflows connect problems to solutions
- [ ] Reporting scenarios generate proper business intelligence filters
- [ ] Knowledge discovery supports effective problem resolution

## Testing Strategy Notes

### **Data Preparation**
- Replace example record numbers with actual records from your ServiceNow instance
- Adjust search terms to match your organization's ServiceNow data patterns
- Verify team assignment groups and user sys_ids for business scenario testing

### **Performance Expectations**
- **Small queries (< 50 records)**: Complete in 5-15 seconds
- **Medium queries (50-500 records)**: Complete in 15-30 seconds
- **Large queries (500+ records)**: May take 30-60 seconds, should use pagination
- **AI intelligence features**: Add 2-5 seconds for natural language processing

### **Success Criteria**
- **Functional**: All tools work as specified with real ServiceNow data
- **Performance**: Queries complete within business-acceptable time frames
- **Intelligence**: AI features demonstrate understanding of natural language queries
- **Security**: No crashes or data exposure from malicious inputs
- **Business Value**: Tests support actual ServiceNow administrative workflows

This V2 test suite focuses on practical, performance-optimized testing that validates the consolidated architecture while ensuring real-world business value for ServiceNow environments with large datasets.