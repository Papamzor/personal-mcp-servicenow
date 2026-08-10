# Graph Report - .  (2026-08-10)

## Corpus Check
- 97 files · ~82,775 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2904 nodes · 5518 edges · 134 communities (127 shown, 7 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 388 edges (avg confidence: 0.6)
- Token cost: 90,000 input · 31,226 output

## Community Hubs (Navigation)
- Generic Table Engine
- Test Generic Table Tools
- Test Consolidated Tools
- Generic Table Engine #2
- Test Generic Table Tools #2
- Filter Validator
- Test Query Intelligence
- Constants Config
- Test Typed Read Generic Table Tools
- Test Kb Article Tools
- Test Query Intelligence #2
- Test Query Validation
- OAuth Exceptions
- Test Oauth
- Test Config Loader
- Test Generic Tool Wrappers
- Test Service Now Api
- Test Security Sanitization
- Test Param Coercion
- Test Typed Read Cmdb Tools
- Test Tool Selection
- Test Typed Read Table Tools
- Test Filtering
- Intelligent Query Tools
- Test Http Layer
- Test Query Intelligence #3
- Test Query Intelligence #4
- Test Query Intelligence #5
- Test Typed Read Kb Article Tools
- Test Query Intelligence #6
- Test Date Utils
- CMDB Tools
- Test Kb Article Tools #2
- Test Cmdb Citype Validation
- KB Article Tools
- Test Cmdb Tools
- Test Query Intelligence #7
- OAuth Client
- Test Task Sla Guard
- Build Mcpb
- Test Date Utils #2
- Test Generic Table Tools #3
- Test Typed Read Vtb Task Tools
- Test Date Utils #3
- Test Kb Article Tools #3
- Test Date Utils #4
- Test Integration
- Test Oauth Client Enhanced
- Test Typed Read Kb Article Tools #2
- Test Kb Article Tools #4
- Test Vtb Task Tools
- Run Tests
- Test Oauth Client Enhanced #2
- Test Query Intelligence #8
- Test Generic Table Tools #4
- Test Vtb Task Tools #2
- Test Generic Table Tools #5
- Test Query Validation #2
- Test Query Validation #3
- Test No Stdout Pollution
- Utils
- Test Kb Article Tools #5
- Test Typed Read Kb Article Tools #3
- Test Date Utils #5
- Test Generic Table Tools #6
- Test Query Validation #4
- Changelog
- E2E Test Prompts
- 01-Architecture-Overview
- Test Http Layer Errors
- Test Typed Read Kb Article Tools #4
- Test Typed Read Cmdb Tools #2
- 01-Architecture-Overview #2
- Test Query Intelligence #9
- Test Query Validation #5
- Manifest.Json
- Test Generic Table Tools #7
- Test Oauth Client Enhanced #3
- Test Query Validation #6
- Test Query Validation #7
- Test Query Validation #8
- 06-Sla-Architecture-Flow
- 01-Architecture-Overview #3
- Test Http Layer Errors #2
- Test Http Layer #2
- Test Pyproject Sync
- Test Typed Read Kb Article Tools #5
- Manifest.Json #2
- Date Utils
- Test Cmdb Tools #2
- Test Oauth Client Enhanced #4
- 05-Ai-Intelligence-Flow
- Request Executor
- OAuth Singleton
- Test Vtb Task Tools #3
- Test Cmdb Tools #3
- 02-Oauth-Authentication-Flow
- 01-Architecture-Overview #4
- Test Kb Article Tools #6
- Test Consolidated Tools #2
- Test Date Utils #6
- Test Generic Table Tools #8
- Test Mcp Tools
- Test Oauth Client Enhanced #5
- Test Oauth Client
- Test Oauth #2
- Test Token Footprint
- Priority Incidents (Domain Filtering)
- Oauth Setup Guide
- Test Consolidated Tools #3
- Manifest.Json #3
- Manifest.Json #4
- Manifest.Json #5
- Manifest.Json #6
- Test Cli
- Test Date Utils #7
- Test Http Layer Errors #3
- Test Oauth Client Enhanced #6
- Manifest.Json #7
- Test Infrastructure (handle http)
- Conftest
- Test Cmdb Citype Validation #2
- Test Integration #2
- Bitbucket-Pipelines
- Manifest.Json #8
- Test Integration #3
- Test Oauth Client Enhanced #7
- Test Oauth Client Enhanced #8
- Test Oauth Client Enhanced #9
- Test Oauth Client Enhanced #10
- tests init__ py
- VTB Task CRUD (Test successful)
- VTB Task CRUD (Test update)
- personal mcp servicenow

## God Nodes (most connected - your core abstractions)
1. `ServiceNowRequestError` - 97 edges
2. `ErrorCode` - 68 edges
3. `ServiceNowOAuthClient` - 59 edges
4. `QueryValidationResult` - 40 edges
5. `QueryIntelligence` - 39 edges
6. `make_nws_request()` - 36 edges
7. `TokenStore` - 36 edges
8. `TestQueryBuilding` - 34 edges
9. `KbDuplicateCheckInconclusive` - 33 edges
10. `_check_kb_duplicates()` - 33 edges

## Surprising Connections (you probably didn't know these)
- `oauth/http_pool Shared Client` --semantically_similar_to--> `Pooled httpx AsyncClient`  [INFERRED] [semantically similar]
  Diagrams & Documentation/02-oauth-authentication-flow.md → CHANGELOG.md
- `get_query_syntax_help Tool` --semantically_similar_to--> `Encoded Query OR Syntax ^OR`  [INFERRED] [semantically similar]
  Diagrams & Documentation/05-ai-intelligence-flow.md → SERVICENOW_QUERY_GUIDE.md
- `ServiceNow Date Range Filters` --semantically_similar_to--> `QueryIntelligence Regex NL Parser`  [INFERRED] [semantically similar]
  SERVICENOW_QUERY_GUIDE.md → Diagrams & Documentation/05-ai-intelligence-flow.md
- `GET Token-Optimization Invariants` --semantically_similar_to--> `HTTP Token-Budget Invariants Tests`  [INFERRED] [semantically similar]
  Diagrams & Documentation/01-architecture-overview.md → MIGRATION_v3_to_v4.md
- `Similarity Search Path` --semantically_similar_to--> `OR-Combined LIKE Text Search`  [INFERRED] [semantically similar]
  Diagrams & Documentation/04-similarity-search-flow.md → CHANGELOG.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **GET Read-Path Pipeline** — diagrams_documentation_01_architecture_overview_generic_table_tools, diagrams_documentation_01_architecture_overview_make_nws_request, diagrams_documentation_04_similarity_search_flow_url_builder, diagrams_documentation_04_similarity_search_flow_response_parser, diagrams_documentation_02_oauth_request_executor, diagrams_documentation_01_architecture_overview_get_invariants [EXTRACTED 1.00]
- **NL Filter Intelligence Pipeline** — diagrams_documentation_05_ai_intelligence_flow_intelligent_search, diagrams_documentation_05_ai_intelligence_flow_query_intelligence, diagrams_documentation_05_ai_intelligence_flow_validator, diagrams_documentation_05_ai_intelligence_flow_builder, diagrams_documentation_05_ai_intelligence_flow_explainer, diagrams_documentation_01_architecture_overview_filter_package [EXTRACTED 1.00]
- **OAuth Authentication Stack** — diagrams_documentation_02_oauth_singleton, diagrams_documentation_02_oauth_client_facade, diagrams_documentation_02_oauth_token_store, diagrams_documentation_02_oauth_request_executor, diagrams_documentation_02_oauth_http_pool, diagrams_documentation_02_oauth_client_credentials [EXTRACTED 1.00]

## Communities (134 total, 7 thin omitted)

### Community 0 - "Generic Table Engine"
Cohesion: 0.03
Nodes (90): _build_debug_extras(), _build_debug_info(), _build_priority_filter(), _build_query_condition(), _build_query_string(), _build_url_with_params(), _clean_priority_input(), _determine_filter_sources() (+82 more)

### Community 1 - "Test Generic Table Tools"
Cohesion: 0.04
Nodes (62): BaseModel, Generic filter parameters for table queries., TableFilterParams, _build_metadata(), _build_sla_status_filter(), _format_deduped_kb_row(), get_active_knowledge_articles(), get_kb_articles_by_state() (+54 more)

### Community 2 - "Test Consolidated Tools"
Cohesion: 0.05
Nodes (33): get_priority_incidents(), OptJsonDict, query_slas_by_status(), Get incidents by priority with optional date range filtering. Uses simple >= /…, Query SLA records by a named status preset. Args: status: one of: - active:…, asyncio, Test knowledge tool functions., Test SLA tool functions. (+25 more)

### Community 3 - "Generic Table Engine #2"
Cohesion: 0.04
Nodes (62): The field a free-text search must target for *table_name*., text_search_field_for(), get_knowledge_by_category(), Find knowledge articles based on input text., Get knowledge articles by category., similar_knowledge_for_text(), _build_additional_filters(), _build_fallback_response() (+54 more)

### Community 4 - "Test Generic Table Tools #2"
Cohesion: 0.03
Nodes (42): _handle_operator_condition(), _handle_servicenow_filter_condition(), _has_operator_in_value(), _is_complete_servicenow_filter(), Check if value already contains a comparison operator or ServiceNow text…, Check if value is already a complete ServiceNow filter (e.g.,…, Handle complete ServiceNow filters., Handle direct operator syntax. (+34 more)

### Community 5 - "Filter Validator"
Cohesion: 0.05
Nodes (58): ServiceNow query-string builder. Static helpers that emit syntactically-correct…, Helper class for building ServiceNow queries with proper syntax., ServiceNowQueryBuilder, Filter pipeline — ServiceNow query construction, validation, NL parsing,…, Pydantic models and result containers for the filter pipeline., _analyze_caller_exclusion(), _analyze_date_filtering(), _analyze_javascript_functions() (+50 more)

### Community 6 - "Test Query Intelligence"
Cohesion: 0.04
Nodes (39): build_smart_filter(), Any, QueryIntelligence, Check for template match and return template data., Parse exclusion patterns and return exclusion filters., Try to parse date range from query., Build keyword-based fallback filter. The field comes from…, Parse natural language query into ServiceNow filters with intelligence. (+31 more)

### Community 7 - "Constants Config"
Cohesion: 0.05
Nodes (48): Constants used throughout the ServiceNow MCP server., _from_decode(), _from_oauth_auth(), _from_oauth_connection(), _from_oauth_forbidden(), _from_status_error(), _from_timeout(), _from_transport() (+40 more)

### Community 8 - "Test Typed Read Generic Table Tools"
Cohesion: 0.06
Nodes (30): PartialPageReadError, Exception, A page after the first failed; the rows already collected are attached.…, IntelligentQueryParams, Parameters for intelligent natural language queries., _assert_plain_failure(), asyncio, Otherwise every `except ServiceNowRequestError` arm would eat the rows. (+22 more)

### Community 9 - "Test Kb Article Tools"
Cohesion: 0.06
Nodes (41): AuthHeaderSource, ErrorCode, The complete failure vocabulary. Adding a code is a contract change., ServiceNowOAuthClient — orchestrator façade. Composes ``TokenStore`` +…, Authenticated HTTP request execution with 401 retry. Owns the actual…, Make authenticated HTTP requests with token-refresh on 401., RequestExecutor, Caches a single OAuth access token and refreshes it on demand. (+33 more)

### Community 10 - "Test Query Intelligence #2"
Cohesion: 0.05
Nodes (37): Delegate validation + auto-correction to the validator module. Kept as a…, QueryValidationResult, Container for query validation results., Add a warning message., Add a suggestion for improvement., True if the query is invalid or has warnings., patch, Test complete natural language parsing. (+29 more)

### Community 11 - "Test Query Validation"
Cohesion: 0.04
Nodes (33): Build OR filter for multiple priorities., Build date range filter for ServiceNow using proper BETWEEN syntax., Build ServiceNow relative date filter with proper BETWEEN syntax., Build exclusion filter for multiple IDs using NOT EQUALS., Build a complete ServiceNow filter string with proper syntax. Args: priorities:…, _correct_priority(), Return (corrected_value, suggestion_or_None) for a priority field., Specific tests for ServiceNowQueryBuilder class. (+25 more)

### Community 12 - "OAuth Exceptions"
Cohesion: 0.06
Nodes (40): Exception, OAuth-domain exception hierarchy., Exception raised when authentication fails., Exception raised when connection to ServiceNow fails., Exception raised when authorization is denied., Base exception for ServiceNow OAuth operations., ServiceNowAuthenticationError, ServiceNowAuthorizationError (+32 more)

### Community 13 - "Test Oauth"
Cohesion: 0.05
Nodes (39): get_auth_info(), Any, Test OAuth connection and return status., Get information about current authentication method., test_oauth_connection(), dict, patch, Test API client integration with OAuth. (+31 more)

### Community 14 - "Test Config Loader"
Cohesion: 0.06
Nodes (42): ConfigError, get_config_dir(), get_config_file_path(), get_setup_instructions(), load_config(), load_config_from_env(), load_config_from_file(), Any (+34 more)

### Community 15 - "Test Generic Tool Wrappers"
Cohesion: 0.07
Nodes (35): filter_records(), find_similar(), get_record(), get_record_summary(), Any, OptJsonList, Generic MCP tool wrappers that replace 24 table-specific 1-line functions. Each…, Get full detail fields for a single known record by number. Use when you know… (+27 more)

### Community 16 - "Test Service Now Api"
Cohesion: 0.05
Nodes (25): patch, Test extracting display values from non-dict input., Test that URLs without sysparm_query pass through unchanged., Test that spaces in query values are percent-encoded., Test that ServiceNow operators (=, ^, <, >, etc.) are preserved., Test that # in query is encoded to prevent URL fragment issues., Test that already-encoded URLs are not double-encoded., Test that other URL parameters are not affected by encoding. (+17 more)

### Community 17 - "Test Security Sanitization"
Cohesion: 0.08
Nodes (36): AuditMiddleware, Middleware, MiddlewareContext, Audit logging middleware for MCP tool calls. Emits one structured JSON log line…, _sanitize(), _summarize(), _user_from_headers(), AuthMiddleware (+28 more)

### Community 18 - "Test Param Coercion"
Cohesion: 0.06
Nodes (15): coerce_json_dict(), coerce_json_list(), Any, Param-boundary JSON coercion for MCP tool signatures. LLM-driven MCP clients…, Peel repeated JSON-string layers (handles single- AND double-encoded input).…, Coerce a (possibly double-encoded) stringified JSON array to a native list., Coerce a (possibly double-encoded) stringified JSON object to a native dict., _unwrap_json_str() (+7 more)

### Community 19 - "Test Typed Read Cmdb Tools"
Cohesion: 0.11
Nodes (19): get_all_ci_types(), quick_ci_search(), Search Configuration Items by multiple attributes. Args: name: CI name/hostname…, Find Configuration Items similar to the specified CI based on attributes. Args:…, Get all available CI types/classes in the CMDB. Returns: Dictionary of the CI…, Quick search for CIs by name, IP, or number. Args: search_term: Term to search…, search_cis_by_attributes(), similar_cis_for_ci() (+11 more)

### Community 20 - "Test Tool Selection"
Cohesion: 0.07
Nodes (29): _evaluate(), evaluation(), _plausible_paths(), _profiles(), fixture, parametrize, _rank(), Golden intent set — tool-selection baseline (v4.4 Tier 0.1). Measures whether… (+21 more)

### Community 21 - "Test Typed Read Table Tools"
Cohesion: 0.08
Nodes (20): nowtest_auth_input(), nowtestauth(), Test function to verify authentication with ServiceNow standard API., Get ServiceNow table schema information for a given table., Test server connectivity and authentication tools., Set up test fixtures., Test basic server connectivity., Test OAuth authentication test. (+12 more)

### Community 22 - "Test Filtering"
Cohesion: 0.05
Nodes (20): patch, Test multiple caller exclusions by sys_id., Test that URL encoding preserves JavaScript functions., Test ServiceNowQueryBuilder query validation., Test proper BETWEEN syntax generation., Test TableFilterParams object creation and validation., Test combined filtering with mocked API call., Test handling of invalid date format inputs. (+12 more)

### Community 23 - "Intelligent Query Tools"
Cohesion: 0.09
Nodes (31): build_and_validate_smart_filter(), Build and validate an intelligent filter without executing the query. This is…, build_smart_servicenow_filter(), explain_servicenow_filters(), FilterExplanationParams, get_query_examples(), get_query_syntax_help(), get_servicenow_filter_templates() (+23 more)

### Community 24 - "Test Http Layer"
Cohesion: 0.10
Nodes (22): _get_typed(), The GET pipeline, with failures raised as ``ServiceNowRequestError``. An empty…, Path + stable query hash for stderr logs — never the raw sysparm_query., _redact_url(), extract_display_values(), extract_field_value(), process_item_dict(), Any (+14 more)

### Community 25 - "Test Query Intelligence #3"
Cohesion: 0.07
Nodes (18): Generate explanation for priority filter., Generate explanation for date-related filters. Matches the gs.* helpers the NL…, Generate explanation for state filter., Generate explanation for assigned_to filter., Generate explanation for complete query filter., Test filter explanation generation., Test explaining single priority filter., Test explaining OR priority filter. (+10 more)

### Community 26 - "Test Query Intelligence #4"
Cohesion: 0.08
Nodes (17): Determine size category from factors., Provide rough estimate of expected result size., Calculate priority contribution to size factor., Calculate date contribution to size factor., Test result size estimation., Test priority factor with no priority filter., Test priority factor with P1., Test priority factor with OR (reduces selectivity). (+9 more)

### Community 27 - "Test Query Intelligence #5"
Cohesion: 0.09
Nodes (17): Parse language patterns and update filters., Merge two priority values with OR syntax., Test priority filter handling., Test merging same priority values., Test merging different priority values., Test merging into existing OR filter., Test that duplicate priorities are not added., Test natural language pattern parsing. (+9 more)

### Community 28 - "Test Typed Read Kb Article Tools"
Cohesion: 0.10
Nodes (15): asyncio, parametrize, `[]` must mean "checked, clear" and nothing else., A '^' in the title splits the encoded query, silently widening it. Percent-…, The quiet one: ensure_query_encoded unquotes, so '%XY' is decoded. ServiceNow…, No false positives: a '%' not followed by hex digits survives intact.…, Only ^ and & break structure; the others survive the round trip. Pinned so a…, A full page may have left the real duplicate off the end of it. (+7 more)

### Community 29 - "Test Query Intelligence #6"
Cohesion: 0.08
Nodes (20): explain_existing_filter(), Any, QueryExplainer, Filter explanation + result-size estimation. Wraps QueryIntelligence's…, Explain what an existing filter does., Explains existing filters and suggests improvements., Explain what an existing filter does and suggest improvements., get_filter_templates() (+12 more)

### Community 30 - "Test Date Utils"
Cohesion: 0.10
Nodes (16): Validate date format is either "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS". Args:…, validate_date_format(), Test date format validation., Test valid YYYY-MM-DD format., Test valid YYYY-MM-DD HH:MM:SS format., Test valid midnight time., Test valid end of day time., Test invalid MM-DD-YYYY format. (+8 more)

### Community 31 - "CMDB Tools"
Cohesion: 0.11
Nodes (19): _build_similar_ci_response(), _ci_type_error(), _extract_ci_search_attributes(), _filter_and_limit_ci_results(), find_cis_by_type(), _probe_ci_table(), Any, Fetch a CI by number from one table; return the first row, or None if absent.… (+11 more)

### Community 32 - "Test Kb Article Tools #2"
Cohesion: 0.13
Nodes (9): Return the published row for *article_number*, or None if not yet published.…, Update fields on a knowledge article by article number (e.g. KB0001234). Args:…, update_knowledge_article(), _verify_kb_published(), _write_kb_article(), asyncio, None means "no Published row yet"; a failed read is not that. Conflating them…, TestCheckKbDuplicatesTool (+1 more)

### Community 33 - "Test Cmdb Citype Validation"
Cohesion: 0.15
Nodes (14): get_ci_details(), Get comprehensive details for a specific Configuration Item. Args: ci_number:…, _Capture, asyncio, The headline bug: never query cmdb_ci when the caller named another table., Absent is not invalid — no ci_type means "search all CIs"., Previously any type outside the static list was ignored and all 7 probed., The concurrent probe must pair each row with the table it came from. The probes… (+6 more)

### Community 34 - "KB Article Tools"
Cohesion: 0.11
Nodes (21): _call_kb_publish_workflow(), _call_kb_workflow(), _check_single_kb_duplicate(), _duplicate_check_inconclusive(), _duplicate_row_inconclusive(), _fire_publish(), _get_kb_article_meta(), _outcome_error_message() (+13 more)

### Community 35 - "Test Cmdb Tools"
Cohesion: 0.08
Nodes (14): Test finding CIs with invalid type., Test searching CIs by name attribute., Test searching CIs by IP address attribute., Test searching CIs by multiple attributes., Test successful CI details retrieval., Test suite for CMDB tools functionality., Test CI details retrieval for non-existent CI., Test finding similar CIs for a given CI. (+6 more)

### Community 36 - "Test Query Intelligence #7"
Cohesion: 0.10
Nodes (13): Return (issue, suggestion) if the priority filter has comma syntax., Return (issue, suggestion) if the date filter is open-ended., Return (issues, suggestions) for the given filter dict., Test QueryExplainer functionality., Test detection of comma-separated priority issue., Test that correct priority filter has no issue., Test detection of incomplete date range., Test that complete date range has no issue. (+5 more)

### Community 37 - "OAuth Client"
Cohesion: 0.12
Nodes (10): Any, AsyncClient, Response, Return Authorization + JSON headers for an API request. Inlined (rather than…, Make an authenticated request to ServiceNow API. Delegates to RequestExecutor;…, Test the OAuth connection by making a simple API call., OAuth 2.0 Client Credentials implementation for ServiceNow. Composes three…, ServiceNowOAuthClient (+2 more)

### Community 38 - "Test Task Sla Guard"
Cohesion: 0.13
Nodes (13): _Capture, asyncio, parametrize, A bare short_description condition is the silently-dropped filter. Splitting on…, A caller that forgets search_field must still get a valid query., The caller's conditions from a captured URL, sort clause removed. Splitting the…, A refusal that does not say what to use instead just moves the dead end., The identity guard must not mask the plain unsupported-table error. (+5 more)

### Community 39 - "Build Mcpb"
Cohesion: 0.15
Nodes (22): assert_no_leaks(), assert_versions_aligned(), clean_staging(), copy_package_dirs(), copy_root_files(), fail(), main(), Path (+14 more)

### Community 40 - "Test Date Utils #2"
Cohesion: 0.11
Nodes (14): get_current_month_range(), get_this_week_range(), Get start and end dates for the current calendar month. Returns: Tuple of…, Get start (Monday) and end (Sunday) of the current week. Returns: Tuple of…, Test convenience date range functions., Test current month range calculation for January., Test current month range for February (non-leap year)., Test current month range for December (year boundary). (+6 more)

### Community 41 - "Test Generic Table Tools #3"
Cohesion: 0.09
Nodes (12): Test priority parsing functions., Test normalizing P-notation., Test normalizing plain numbers., Test cleaning priority input., Test processing comma-separated priorities., Test processing P-notation priorities., Test formatting single priority., Test parsing single priority. (+4 more)

### Community 42 - "Test Typed Read Vtb Task Tools"
Cohesion: 0.18
Nodes (11): Update an existing private task record in ServiceNow. Args: task_number: The…, update_private_task(), _assert_plain_failure(), asyncio, fixture, Decision (b): absent is still absent, and the message is unchanged., A rejected field must not cost a round trip., A failed lookup reaches `update_private_task` through the real dispatcher.… (+3 more)

### Community 43 - "Test Date Utils #3"
Cohesion: 0.14
Nodes (12): build_date_filter(), Build ServiceNow date filter using simple >= and <= operators. This replaces…, Test date filter building., Test filter with both start and end dates., Test filter with only start date., Test filter with only end date., Test filter with no dates returns None., Test filter with both None returns None. (+4 more)

### Community 44 - "Test Kb Article Tools #3"
Cohesion: 0.14
Nodes (10): _publish_with_verify(), Fire the publish workflow then verify by polling for a Published row. Treats…, Fire-and-verify orchestrator — verify is the only success signal., The main bug class: POST times out, SN still committed the publish., Regression: anyio.fail_after raises builtin TimeoutError, not…, When fire keeps raising HTTPStatusError and verify never finds Published, the…, TestPublishWithVerify, The retry path is for a verify that positively says "not published yet". (+2 more)

### Community 45 - "Test Date Utils #4"
Cohesion: 0.15
Nodes (13): datetime, Read-only view of the current token's expiry., _sla_filter_breached(), _sla_filter_performance(), build_last_n_days_filter(), Build ServiceNow filter for records from the last N days. This replaces the…, Test build_last_n_days_filter helper function., Test filter uses sys_created_on by default. (+5 more)

### Community 46 - "Test Integration"
Cohesion: 0.14
Nodes (11): asyncio, parametrize, The decoded sysparm_query value from a captured request URL., The outbound query equals the caller's conditions — nothing appended. Domain…, Nothing is dropped after the response comes back. The URL assertions above…, create_private_task → make_nws_request(method=POST) → oauth_client…, HTTPStatusError raised at the OAuth boundary surfaces as a domain error string., search_records → query_table_by_text → make_nws_request → make_oauth_request. (+3 more)

### Community 47 - "Test Oauth Client Enhanced"
Cohesion: 0.14
Nodes (11): dict, Test access token request functionality., Test successful token request., Test token request with 401 authentication error., Test token request with 403 authorization error., Test token request with 500 server error., Test token request with connection error., Test token request with timeout error. (+3 more)

### Community 48 - "Test Typed Read Kb Article Tools #2"
Cohesion: 0.16
Nodes (7): publish_knowledge_article(), Publish a knowledge article via the ServiceNow workflow endpoint. Runs a…, TestPublishKnowledgeArticle, The guard must not have become so strict that nothing can publish., A publish requires a duplicate check that positively came back clear., The headline bug. A timeout in the guard must not become permission., TestPublishGuardIsFailClosed

### Community 49 - "Test Kb Article Tools #4"
Cohesion: 0.18
Nodes (7): _check_kb_duplicates(), _dedup_query_defect(), Why the dedup query would not faithfully carry *short_description*, if so. Two…, Return KB articles matching short_description exactly across live workflow…, Check for duplicate KB articles without publishing. For each number: looks up…, The headline fix: [] means "checked, clear" and nothing else. The old test…, TestCheckKbDuplicates

### Community 50 - "Test Vtb Task Tools"
Cohesion: 0.12
Nodes (11): create_private_task(), _prepare_task_create_data(), Any, Create a new private task record in ServiceNow. Args: task_data: Dictionary…, Prepare and validate data for task creation., Test preparing task data with minimal required fields., Test preparing task data with optional fields., Test that extra fields not in optional list are ignored. (+3 more)

### Community 51 - "Run Tests"
Cohesion: 0.20
Nodes (16): check_test_environment(), main(), Show coverage results if available., Main test runner function., Run a command and return success status., Run all tests with coverage reporting and JUnit XML output., Run a specific test module., Run only integration tests. (+8 more)

### Community 52 - "Test Oauth Client Enhanced #2"
Cohesion: 0.15
Nodes (10): asyncio, Test making authenticated API requests., Test successful authenticated request., Test authenticated request with 401 and successful retry., Test authenticated request with non-401 HTTP error., Test authenticated request with connection error., Test authenticated request with timeout., Test authenticated request with JSON decode error. (+2 more)

### Community 53 - "Test Query Intelligence #8"
Cohesion: 0.17
Nodes (9): Apply context-based filters (e.g., user preferences, previous queries)., Test context-based filter application., Test applying date range from context., Test applying single caller exclusion from context., Test applying multiple caller exclusions from context., Test applying exclude resolved from context., Test applying user-assigned filter from context., Test that empty context returns empty filters. (+1 more)

### Community 54 - "Test Generic Table Tools #4"
Cohesion: 0.17
Nodes (10): _inject_sort_order(), Inject a sort directive into the URL's sysparm_query if no ORDERBY is present.…, Test _inject_sort_order() helper., Test sort directive is appended to existing sysparm_query., Test URL is returned unchanged when ORDERBY already exists., Test sysparm_query is created when URL has no query param., Test sysparm_query is created when URL has no params at all., Test sort is appended correctly to a multi-condition query. (+2 more)

### Community 55 - "Test Vtb Task Tools #2"
Cohesion: 0.29
Nodes (7): Send a write request through make_nws_request, mapping errors locally., _write_private_task(), _make_http_status_error(), asyncio, HTTPStatusError, Test the unified write helper that wraps make_nws_request., TestWritePrivateTask

### Community 56 - "Test Generic Table Tools #5"
Cohesion: 0.12
Nodes (9): Test edge cases and error handling., Test priority parsing with special characters., Test building query with suffix operators., Test that encoding preserves important ServiceNow characters., Test exception handling in find_similar_records., Test getting records by priority with additional filters., Test exception handling in get_records_by_priority., Test exception handling in query_table_with_generic_filters. (+1 more)

### Community 57 - "Test Query Validation #2"
Cohesion: 0.12
Nodes (9): Test utility and helper functions., Test cross verification function structure., Test building pagination parameters with defaults., Test building pagination parameters with custom values., Test suggestions for zero results., Test suggestions for low priority query results., Test suggestions for high result count., Test no suggestions for normal result count. (+1 more)

### Community 58 - "Test Query Validation #3"
Cohesion: 0.12
Nodes (9): Test edge cases and error handling scenarios., Test ServiceNowQueryBuilder handles None inputs gracefully., Test ServiceNowQueryBuilder handles empty lists gracefully., Test priority filter validation with empty string., Test date range filter validation with empty string., Test result count validation with edge values., Test debug_query_construction handles None inputs., Test pagination params with edge values. (+1 more)

### Community 59 - "Test No Stdout Pollution"
Cohesion: 0.19
Nodes (14): expr, _find_offending_prints(), _is_stderr_target(), _iter_runtime_modules(), Path, Lint guard: server runtime code must never print to stdout. MCP stdio transport…, Self-check: the AST scanner must NOT flag stderr-routed prints., True when the ``file=`` argument resolves to ``sys.stderr``. (+6 more)

### Community 60 - "Utils"
Cohesion: 0.17
Nodes (13): Natural-language to ServiceNow filter conversion. Pure NL parsing — does not…, _correct_date(), Return (corrected_value, suggestion_or_None) for a sys_created_on field., Validate filters and auto-correct common syntax issues. Returns a result with…, validate_and_correct_filters(), _extract_content_keywords(), extract_keywords(), _extract_record_numbers() (+5 more)

### Community 61 - "Test Kb Article Tools #5"
Cohesion: 0.18
Nodes (8): _get_kb_article_sys_id(), Return the article's sys_id, or None if no such article exists. None means…, Re-read the draft sys_id between publish attempts, best effort. ServiceNow…, _refresh_draft_sys_id(), Decision (d): None means absent, so a failed read must NOT return None. The old…, The shape a failed GET now arrives in for this module (v4.4 Tier 0.3)., TestGetKbArticleSysId, _timeout()

### Community 62 - "Test Typed Read Kb Article Tools #3"
Cohesion: 0.17
Nodes (6): Retire a knowledge article via the ServiceNow workflow endpoint. Args:…, retire_knowledge_article(), _assert_plain_failure(), Typed read failures in the KB article tools (v4.4 Tier 0.3, PR C). A failed GET…, Decision (d): a write never reports "not found" because a lookup failed., TestPreWriteReadsDistinguishAbsentFromFailed

### Community 63 - "Test Date Utils #5"
Cohesion: 0.19
Nodes (9): normalize_date_to_full_format(), Normalize date string to full format with time component. Args: date_string:…, Test date normalization., Test normalizing simple date for start (adds 00:00:00)., Test normalizing simple date for end (adds 23:59:59)., Test full datetime is unchanged for start., Test full datetime is unchanged for end., Test midnight datetime is preserved. (+1 more)

### Community 64 - "Test Generic Table Tools #6"
Cohesion: 0.14
Nodes (8): Test ReDoS (Regular Expression Denial of Service) protection., Test validation accepts valid strings., Test validation rejects non-strings., Test validation rejects overly long strings., Test validation rejects strings with too many spaces., Test validation rejects strings with too many dashes., Test validation with edge case strings., TestReDoSProtection

### Community 65 - "Test Query Validation #4"
Cohesion: 0.14
Nodes (8): Test priority filter validation functionality., Test validating single priority filter., Test validating proper OR syntax., Test validation warns about comma syntax., Test validation warns about OR syntax without priority= prefix., Test validation suggests numeric format for text priorities., Test validation with mixed numeric and text format., TestPriorityFilterValidation

### Community 66 - "Changelog"
Cohesion: 0.17
Nodes (13): Claude Desktop MCPB Packaging, Seven-Code Error Vocabulary, Partial Read with partial:true, v4.4 Read-Failure Contract, ServiceNowRequestError, MCPB Build Guide, MCPB Staging Whitelist Packaging, MCPB server.type uv Runtime (+5 more)

### Community 67 - "E2E Test Prompts"
Cohesion: 0.21
Nodes (13): OR-Combined LIKE Text Search, find_similar Tool, search_records Tool, Paginated Request with ORDERBYDESC, query_table_by_text Engine, Similarity Search Path, Intelligence Confidence Metadata, intelligent_search Tool (+5 more)

### Community 68 - "01-Architecture-Overview"
Cohesion: 0.15
Nodes (13): AuditMiddleware Structured Logs, AuthMiddleware SSE Bearer, FastMCP Server Core, Stdout JSON-RPC Stderr Logs Invariant, tools.py Tool Registration, stdio and SSE Transport, SSE Auth Independent of ServiceNow OAuth, PayPal Sponsor Funding (+5 more)

### Community 69 - "Test Http Layer Errors"
Cohesion: 0.23
Nodes (6): classify_read_failure(), Map a read-path exception onto the error vocabulary. ``TimeoutError`` covers…, ServiceNowOAuthClient raises ValueError('Missing OAuth configuration').…, anyio.fail_after raises the builtin TimeoutError, not an httpx one., Unreachable host is retryable, but it is not a deadline expiry., TestClassifyTransportFailures

### Community 70 - "Test Typed Read Kb Article Tools #4"
Cohesion: 0.22
Nodes (4): _normalize_publish_result(), Normalize publish_knowledge_article output into a flat batch-result row. Four…, `published` is the fall-through, so every other shape must be caught first., TestNormalizePublishResultNeverInventsSuccess

### Community 71 - "Test Typed Read Cmdb Tools #2"
Cohesion: 0.21
Nodes (7): _by_table(), The headline bug: one timed-out probe attributing a CI to the wrong table., cmdb_ci_server times out; the base cmdb_ci row must NOT be the answer. cmdb_ci…, A higher-priority table already decided; later failures are irrelevant., A real bug must not be laundered into a not-found string., Fake make_nws_request that answers per table name in the URL. Values are either…, TestProbeFailuresAreNotAbsence

### Community 72 - "01-Architecture-Overview #2"
Cohesion: 0.21
Nodes (12): Encoded-Query Value Encoding Limitation, KB Publish Fail-Closed Duplicate Check, 39 MCP Tools Inventory, CMDB Tools Module, Intelligent Query Tools, KB Article Write Tools, make_nws_request Dispatcher, VTB Private Task CRUD Tools (+4 more)

### Community 73 - "Test Query Intelligence #9"
Cohesion: 0.21
Nodes (7): Handle exclusion filters with intelligent name-to-ID mapping., Test exclusion filter handling., Test exclusion of known entity LogicMonitor., Test exclusion of LogicMonitor Integration (with spaces)., Test exclusion of unknown entity., Test field mapping for exclusions., TestExclusionFilters

### Community 74 - "Test Query Validation #5"
Cohesion: 0.23
Nodes (6): True if the value already expresses an operator (so it is not a bare match)., Warn when a reference field is filtered by a bare display value. Reference…, validate_reference_field(), _value_carries_operator(), validate_reference_field flags bare reference-field display values., TestReferenceFieldValidation

### Community 75 - "Manifest.Json"
Cohesion: 0.17
Nodes (11): author, name, description, display_name, long_description, manifest_version, name, repository (+3 more)

### Community 76 - "Test Generic Table Tools #7"
Cohesion: 0.17
Nodes (7): Test caller exclusion parsing., Test parsing known caller (logicmonitor)., Test parsing single sys_id., Test parsing comma-separated sys_ids., Test parsing already formatted exclusion., Test parsing empty input., TestCallerExclusions

### Community 77 - "Test Oauth Client Enhanced #3"
Cohesion: 0.17
Nodes (7): Test token caching and refresh functionality., Test getting token when none exists., Test using cached token when still valid., Test refreshing token when expired., Test getting authorization headers., Test clearing token cache., TestTokenManagement

### Community 78 - "Test Query Validation #6"
Cohesion: 0.17
Nodes (7): Test date range filter validation functionality., Test validating proper BETWEEN syntax., Test validation warns about old comparison syntax., Test validation warns about BETWEEN without JavaScript functions., Test validation warns about missing @ separator., Test validation provides suggestion for Week 35 2025., TestDateRangeFilterValidation

### Community 79 - "Test Query Validation #7"
Cohesion: 0.17
Nodes (7): Test the main validate_query_filters function., Test validating empty filters., Test validating filters with priority only., Test validating filters with date only., Test validating filters with both priority and date issues., Test that validation ignores other (non-validated, non-reference) fields…, TestQueryFiltersValidation

### Community 80 - "Test Query Validation #8"
Cohesion: 0.17
Nodes (7): Test result count validation functionality., Test validation passes for normal incident count., Test validation warns about low P1/P2 incident count., Test validation doesn't warn for non-incident tables., Test validation doesn't warn for non-priority incident queries., Test validation only warns for high priority (1,2) incidents., TestResultCountValidation

### Community 81 - "06-Sla-Architecture-Flow"
Cohesion: 0.25
Nodes (11): get_sla_details sys_id Bug Fix, SLA Tool Consolidation 10→5, GET Token-Optimization Invariants, SLA Architecture Document, query_slas_custom Escape Hatch, query_slas_by_status Presets, task_sla Table, SLA Token Optimization Strategy (+3 more)

### Community 82 - "01-Architecture-Overview #3"
Cohesion: 0.29
Nodes (11): v4.0 Package Split filter/http_layer/oauth, v4.1 Shim Module Deletion, filter/ Package Pipeline, http_layer/ Package, oauth/ Package, QueryExplainer, Layered Architecture Stack, Migration Guide v3 to v4 (+3 more)

### Community 83 - "Test Http Layer Errors #2"
Cohesion: 0.24
Nodes (5): asyncio, Derived from the CODE, not from a list. The list was wrong once already. The…, The headline bug: a 30s deadline must never look like a missing record., Empty is success. Deciding it means not-found is the consumer's job., TestReadFailuresPropagate

### Community 84 - "Test Http Layer #2"
Cohesion: 0.22
Nodes (7): asyncio, GET path: encoding + perf params + display flattening all apply., Critical negative tests — write path MUST NOT touch read-path mutations. Per…, Write responses have a single-record shape; flattening would corrupt them.…, Write must pass ``raise_for_status=True`` so callers map status codes., TestMakeNwsRequestReadPath, TestMakeNwsRequestWritePath

### Community 85 - "Test Pyproject Sync"
Cohesion: 0.36
Nodes (10): _load_manifest(), _load_pyproject(), _main_version(), Packaging-consistency tests for the .mcpb bundle sources. These guard the…, _requirements_entries(), test_manifest_entry_point_exists(), test_manifest_env_mapping_covers_required_config(), test_requirements_mirrored_in_pyproject() (+2 more)

### Community 86 - "Test Typed Read Kb Article Tools #5"
Cohesion: 0.29
Nodes (6): _no_sleep(), fixture, A failed read reaches the publish guard through the real dispatcher. These…, Fake the transport under the real dispatcher; record every write., GET handler: meta resolves, the dedup query does whatever `dedup` says., TestEndToEndThroughTheRealDispatcher

### Community 87 - "Manifest.Json #2"
Cohesion: 0.20
Nodes (10): args, command, server, entry_point, mcp_config, type, --directory, ${__dirname} (+2 more)

### Community 88 - "Date Utils"
Cohesion: 0.24
Nodes (7): get_today_range(), get_yesterday_range(), Date utilities for ServiceNow MCP incident queries. Provides date validation,…, Get start and end of today (same date for both). Returns: Tuple of (start_date,…, Get start and end of yesterday (same date for both). Returns: Tuple of…, Tests for date utilities module. Tests date validation, normalization, and date…, Test yesterday range returns previous day for both.

### Community 89 - "Test Cmdb Tools #2"
Cohesion: 0.20
Nodes (6): Test input validation and error handling for CMDB tools., Test CI number format validation., Test CI type parameter validation., Test search attributes parameter validation., Test search term validation for quick search., TestCMDBToolsValidation

### Community 90 - "Test Oauth Client Enhanced #4"
Cohesion: 0.20
Nodes (6): Test OAuth client initialization., Test initialization with valid configuration., Test initialization fails when SERVICENOW_INSTANCE is missing., Test initialization fails when CLIENT_ID is missing., Test initialization fails when CLIENT_SECRET is missing., TestServiceNowOAuthClientInit

### Community 91 - "05-Ai-Intelligence-Flow"
Cohesion: 0.28
Nodes (9): filter Intelligence-Builder Backref Discipline, NL Filter Intelligence Document, ServiceNowQueryBuilder, QueryIntelligence Regex NL Parser, filter/validator Auto-Correct Bridge, ServiceNow Query Syntax Guide, _complete_query Filter Pattern, ServiceNow Date Range Filters (+1 more)

### Community 92 - "Request Executor"
Cohesion: 0.28
Nodes (6): Any, AsyncClient, Response, Drop the cached token, re-authenticate, retry once., Make an authenticated request to ServiceNow API. When…, Decode a successful response payload.

### Community 93 - "OAuth Singleton"
Cohesion: 0.28
Nodes (8): get_oauth_client(), _hydrate_env_from_config(), make_oauth_request(), Any, Module-level OAuth client singleton + convenience request helpers. Canonical…, Populate SERVICENOW_* env vars from the setup-wizard config file. The OAuth…, Get or create the global OAuth client instance., Convenience function for making OAuth-authenticated GET requests. Propagates…

### Community 94 - "Test Vtb Task Tools #3"
Cohesion: 0.31
Nodes (5): Extract the inner result payload from a write response., _unwrap_write_response(), Test the response unwrapper helper., An empty write response cannot establish that the write landed., TestUnwrapWriteResponse

### Community 95 - "Test Cmdb Tools #3"
Cohesion: 0.22
Nodes (5): Integration tests for CMDB tools workflow., Set up integration test fixtures., Test complete CMDB discovery workflow., Test complete CMDB search workflow., TestCMDBToolsIntegration

### Community 96 - "02-Oauth-Authentication-Flow"
Cohesion: 0.36
Nodes (8): Pooled httpx AsyncClient, ServiceNowOAuthClient Facade, oauth/http_pool Shared Client, RequestExecutor 401 Retry, oauth/singleton Process-Wide Client, TOKEN_REFRESH_BUFFER_MINUTES, TokenStore Cache and Refresh, httpx HTTP Client Dependency

### Community 97 - "01-Architecture-Overview #4"
Cohesion: 0.25
Nodes (8): Architecture Overview Document, Generic Tool Wrappers, TABLE_CONFIGS Supported Tables, Tool Organization Document, Table Extensibility via TABLE_CONFIGS, v3 Generic Wrapper Consolidation, Search and Query Flow Document, Architecture Documentation Index

### Community 98 - "Test Kb Article Tools #6"
Cohesion: 0.25
Nodes (4): JsonList, publish_knowledge_articles(), Publish multiple KB articles in one tool call. Runs full publish flow per…, Verify Semaphore prevents more than `concurrency` in-flight publishes.

### Community 99 - "Test Consolidated Tools #2"
Cohesion: 0.36
Nodes (4): _build_priority_result_message(), Build human-readable result message for priority queries., Test the result message builder., TestBuildPriorityResultMessage

### Community 100 - "Test Date Utils #6"
Cohesion: 0.25
Nodes (5): get_last_n_days_range(), Get start and end dates for the last N days (including today). Args: days:…, Test last 7 days range calculation., Test last 30 days range calculation., Test last 1 day range (yesterday and today).

### Community 101 - "Test Generic Table Tools #8"
Cohesion: 0.25
Nodes (5): Test TableFilterParams model., Test creating params with filters., Test creating params with fields., Test creating empty params., TestTableFilterParams

### Community 102 - "Test Mcp Tools"
Cohesion: 0.25
Nodes (5): Test private task tools with CRUD operations., Set up test fixtures., Test creating a new private task., Test updating an existing private task., TestPrivateTaskTools

### Community 103 - "Test Oauth Client Enhanced #5"
Cohesion: 0.25
Nodes (5): Test retry with fresh token functionality., Test successful retry with fresh token., Test retry with fresh token that fails., retry_with_fresh_token re-raises HTTPStatusError when raise_for_status=True., TestRetryWithFreshToken

### Community 104 - "Test Oauth Client"
Cohesion: 0.39
Nodes (3): dict, patch, TestOAuthClientExtended

### Community 105 - "Test Oauth #2"
Cohesion: 0.25
Nodes (5): Test OAuth token handling and validation., Test validation of valid OAuth token format., Test validation of malformed OAuth token., Test token expiration logic., TestOAuthTokenHandling

### Community 106 - "Test Token Footprint"
Cohesion: 0.25
Nodes (5): Lock budget constants — accidental relaxation should fail review., Curated 7-field view must be at most ~15% over standard ESSENTIAL list., Performance preset has 11 fields vs essential's 6; budget reflects that., A sys_id lookup must never need more than ~200 tokens (1 row)., TestSLATokenBudgetConstants

### Community 107 - "Priority Incidents (Domain Filtering)"
Cohesion: 0.29
Nodes (7): Domain Filtering Deleted, consolidated_tools Module, generic_table_tools Query Engine, filter_records Tool, Knowledge Base Read Tools, KB Version Collapse by Number, get_priority_incidents Enhanced Queries

### Community 108 - "Oauth Setup Guide"
Cohesion: 0.33
Nodes (7): OAuth Authentication Flow Document, OAuth 2.0 Client Credentials Flow, OAuth Setup Guide, ServiceNow OAuth Application Registry, SERVICENOW OAuth Env Configuration, Dedicated OAuth Service Account Least Privilege, OAuth-Only Auth Policy

### Community 109 - "Test Consolidated Tools #3"
Cohesion: 0.38
Nodes (4): _get_error_message(), Get table-specific error message with cognitive complexity < 15., Test helper functions., TestHelperFunctions

### Community 110 - "Manifest.Json #3"
Cohesion: 0.33
Nodes (6): description, required, title, type, user_config, client_id

### Community 111 - "Manifest.Json #4"
Cohesion: 0.33
Nodes (6): description, required, sensitive, title, type, client_secret

### Community 112 - "Manifest.Json #5"
Cohesion: 0.33
Nodes (6): MCP_TRANSPORT, SERVICENOW_AUTH_TYPE, SERVICENOW_CLIENT_ID, SERVICENOW_CLIENT_SECRET, SERVICENOW_INSTANCE, env

### Community 113 - "Manifest.Json #6"
Cohesion: 0.33
Nodes (6): keywords, cmdb, incident, itsm, knowledge-base, servicenow

### Community 114 - "Test Cli"
Cohesion: 0.33
Nodes (5): Tests for CLI argument handling., --help should print usage and exit 0., --version should print version and exit 0., test_help_flag(), test_version_flag()

### Community 115 - "Test Date Utils #7"
Cohesion: 0.33
Nodes (4): Integration tests for date filter building with validation., Test complete workflow: validate -> normalize -> build filter., Verify filter doesn't use JavaScript syntax., TestDateFilterIntegration

### Community 117 - "Test Oauth Client Enhanced #6"
Cohesion: 0.33
Nodes (4): Test connection testing functionality., Test successful connection test., Test failed connection test., TestConnectionTesting

### Community 118 - "Manifest.Json #7"
Cohesion: 0.40
Nodes (5): description, required, title, type, servicenow_instance

### Community 119 - "Test Infrastructure (handle http)"
Cohesion: 0.40
Nodes (4): _handle_http_error(), HTTPStatusError, Handle HTTP errors consistently., parametrize

### Community 120 - "Conftest"
Cohesion: 0.40
Nodes (4): fixture, Shared pytest fixtures. The v4.2 connection-pooling refactor introduced a…, Drop the cached pooled client before and after each test., _reset_http_pool()

### Community 121 - "Test Cmdb Citype Validation #2"
Cohesion: 0.40
Nodes (3): Table segment of a ServiceNow Table API URL., Table segment of each captured URL., _table_of()

### Community 123 - "Bitbucket-Pipelines"
Cohesion: 0.50
Nodes (4): Bitbucket CI Pipeline, pytest Coverage CI Step, SonarCloud Quality Scan, pytest Dev Test Stack

### Community 124 - "Manifest.Json #8"
Cohesion: 0.50
Nodes (4): compatibility, platforms, darwin, win32

### Community 126 - "Test Oauth Client Enhanced #7"
Cohesion: 0.50
Nodes (3): Test Basic Auth header generation., Test Basic Auth header generation., TestBasicAuthHeader

### Community 127 - "Test Oauth Client Enhanced #8"
Cohesion: 0.50
Nodes (3): Test global client instance management., Test that get_oauth_client creates instance., TestGlobalClientInstance

### Community 128 - "Test Oauth Client Enhanced #9"
Cohesion: 0.50
Nodes (3): raise_for_status=True surfaces HTTPStatusError from write operations., raise_for_status=True propagates 4xx/5xx errors instead of returning None., TestRaiseForStatusPropagation

### Community 129 - "Test Oauth Client Enhanced #10"
Cohesion: 0.50
Nodes (3): Test response processing., Test processing successful response., TestProcessResponse

## Knowledge Gaps
- **64 isolated node(s):** `manifest_version`, `name`, `display_name`, `version`, `description` (+59 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `make_nws_request()` connect `Constants Config` to `Test Http Layer`, `OAuth Singleton`, `Test Oauth`?**
  _High betweenness centrality (0.004) - this node is a cross-community bridge._
- **Why does `get_oauth_client()` connect `OAuth Singleton` to `OAuth Client`?**
  _High betweenness centrality (0.003) - this node is a cross-community bridge._
- **Why does `ServiceNowOAuthClient` connect `OAuth Client` to `Test Kb Article Tools`?**
  _High betweenness centrality (0.003) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `ServiceNowRequestError` (e.g. with `ServiceNowAuthenticationError` and `ServiceNowAuthorizationError`) actually correct?**
  _`ServiceNowRequestError` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `ErrorCode` (e.g. with `ServiceNowAuthenticationError` and `ServiceNowAuthorizationError`) actually correct?**
  _`ErrorCode` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `ServiceNowOAuthClient` (e.g. with `RequestExecutor` and `TokenStore`) actually correct?**
  _`ServiceNowOAuthClient` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `manifest_version`, `name`, `display_name` to the rest of the system?**
  _64 weakly-connected nodes found - possible documentation gaps or missing edges._