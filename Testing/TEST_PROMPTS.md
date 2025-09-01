# Test Prompts for ServiceNow MCP Functionality

## Test Prompt 1: Basic Server Connectivity & Authentication
```
Test the following tools in sequence:
1. Call `nowtest()` to verify the MCP server is running
2. Call `nowtestauth()` to test authenticated access to ServiceNow custom API
3. Call `nowtest_auth_input("incident")` to get table description for the incident table

Expected Results:
- nowtest(): Should return "Server is running and ready to handle requests!"
- nowtestauth(): Should return API response data or connection error message
- nowtest_auth_input(): Should return incident table description or "Record not found."
```

## Test Prompt 2: Incident Management Tools
```
Test incident-related functionality:
1. Call `similar_incidents_for_text("server down database error")` to find similar incidents
2. Call `get_short_desc_for_incident("INC0010001")` to get description of a specific incident
3. Call `getincidentdetails("INC0010001")` to get full details of the same incident
4. Call `similar_incidents_for_incident("INC0010001")` to find incidents similar to INC0010001
5. Call `get_incidents_by_filter({"state": "1", "priority": "1"}, ["number", "short_description", "state"])` with custom filters

Expected Results:
- Text search should return incidents matching keywords or "No records found."
- Description lookup should return short_description field or "Record not found."
- Details should return comprehensive incident information
- Similar incident search should work based on the reference incident's description
- Filter search should return incidents matching the specified criteria
```

## Test Prompt 3: Change Request Management Tools
```
Test change request functionality:
1. Call `similar_changes_for_text("system upgrade maintenance window")` to find related changes
2. Call `get_short_desc_for_change("CHG0000001")` to get description of a specific change
3. Call `getchangedetails("CHG0000001")` to get full change details
4. Call `similar_changes_for_change("CHG0000001")` to find similar changes

Expected Results:
- All functions should work identically to incident tools but for change_request table
- Should return appropriate change request data or "No records found."/"Record not found."
- Field structure should include change-specific fields (number, short_description, priority, state)
```

## Test Prompt 4: Universal Request (UR) Management Tools
```
Test Universal Request functionality:
1. Call `similar_ur_for_text("password reset account locked")` to find related URs
2. Call `get_short_desc_for_ur("UR0073721")` to get description of a specific UR
3. Call `get_ur_details("UR0073721")` to get full UR details  
4. Call `similar_urs_for_ur("UR0073721")` to find similar URs

Expected Results:
- All UR functions should mirror incident/change functionality for universal_request table
- Should handle Universal Request records appropriately
- Return UR-specific data or standard error messages
- Maintain same field optimization (4 essential vs 7 detailed fields)
```

## Test Prompt 5: Knowledge Base Management Tools
```
Test knowledge base functionality:
1. Call `similar_knowledge_for_text("VPN connection troubleshooting", None, "IT")` to search knowledge articles
2. Call `get_knowledge_details("KB0000001")` to get specific knowledge article details
3. Call `get_knowledge_by_category("IT")` to get knowledge articles by category
4. Call `get_active_knowledge_articles()` to get all active knowledge articles

Expected Results:
- Knowledge search should return relevant articles or "No records found."
- Details lookup should return comprehensive knowledge article information
- Category filter should return articles from specified category
- Active articles should return all published/active knowledge base entries
- Should handle optional parameters (kb_base, category) correctly
```

## Test Prompt 6: Private Task Management Tools (CRUD Operations)
```
Test Private Task functionality with full CRUD operations (vtb_task table):

### Read Operations:
1. Call `similarprivatetasksfortext("server maintenance database backup")` to find private tasks matching text
2. Call `getshortdescforprivatetask("VTB0001234")` to get description of a specific private task
3. Call `getprivatetaskdetails("VTB0001234")` to get full private task details
4. Call `similarprivatetasksforprivatetask("VTB0001234")` to find similar private tasks
5. Call `getprivatetasksbyfilter({"state": "1", "priority": "2"}, ["number", "short_description", "assigned_to"])` with custom filters

### Create Operation:
6. Call `createprivatetask({
    "short_description": "Test private task creation",
    "description": "This is a test private task created via MCP",
    "priority": "3",
    "assigned_to": "admin"
})` to create a new private task

### Update Operation:
7. Call `updateprivatetask("VTB0001234", {
    "state": "2",
    "comments": "Updated via MCP test",
    "priority": "1"
})` to update an existing private task

Expected Results:
- Text search should return private tasks matching keywords or "No private task records found."
- Description lookup should return short_description field or "Private Task not found."
- Details should return comprehensive private task information with extended fields
- Similar task search should work based on the reference task's description
- Filter search should return private tasks matching the specified criteria
- Create operation should return the newly created private task details with generated number
- Update operation should return the updated private task details or error if task not found
- All operations should work with both OAuth 2.0 and Basic Auth
- Note: Uses vtb_task table internally but presents as "Private Tasks" to users
```

## Validation Checklist

After running each test prompt, verify:

### ✅ **Functionality Preservation**
- [ ] All tool names work exactly as before
- [ ] Same input parameters accepted
- [ ] Same output structure maintained
- [ ] Error messages are consistent (though potentially shorter)

### ✅ **Performance Optimization**
- [ ] Responses contain fewer fields for basic queries (4 instead of 7+)
- [ ] Error messages are shorter but still informative
- [ ] Keyword extraction returns fewer, more relevant terms
- [ ] API queries use optimized field selection

### ✅ **Error Handling**
- [ ] Invalid incident/change/UR numbers return "Record not found."
- [ ] Text searches with no matches return "No records found."
- [ ] Authentication failures handled gracefully
- [ ] Invalid table names handled appropriately

### ✅ **Backward Compatibility**
- [ ] All existing client code continues to work
- [ ] No breaking changes in tool signatures
- [ ] Response structures remain compatible
- [ ] Same authentication mechanisms work

## Expected Token Usage Improvements

Compare before/after for:
- **API Response Size**: ~20% smaller due to fewer fields
- **Error Messages**: ~60% shorter
- **Keyword Queries**: ~40% fewer search terms
- **Tool Definitions**: ~40% less redundant code

## Notes for Testing
- Replace example record numbers (INC0010001, CHG0000001, etc.) with actual records from your ServiceNow instance
- Adjust search terms to match your ServiceNow data
- Test with both valid and invalid record numbers to verify error handling
- Monitor actual token usage during testing to validate optimization effectiveness