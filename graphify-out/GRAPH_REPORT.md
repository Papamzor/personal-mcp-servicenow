# Graph Report - .  (2026-08-10)

## Corpus Check
- 19 files · ~92,635 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3056 nodes · 5818 edges · 166 communities (154 shown, 12 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 398 edges (avg confidence: 0.6)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- OAuth Client Auth Headers
- Generic Table Query Engine
- Encoded Query Value Escape
- Query Builder Operator Tests
- Constants and Error Codes
- Text Search and Pagination
- OAuth Client Facade
- Config Loader
- Date Utils and SLA Ranges
- OAuth Connection Tests
- Consolidated Tools Suite
- Auth and KB Test Tools
- HTTP Layer Encoding Tests
- Date Filter Utilities
- Audit Middleware
- Request Dispatcher Parser
- Tool Selection Evaluation
- OAuth Auth Info Tests
- CMDB Probe and Encoding
- Query Intelligence NL Parse
- Query Explainer
- SLA Status Presets
- Request Dispatcher Singleton
- Filter Validation Result
- Param Coercion Tests
- KB Dedup Title Encoding
- get record Tool Wrappers
- KB Article Write Tools
- Date Format Validation
- Similar Records Engine
- KB Batch Publish Helpers
- Publish Knowledge Tests
- Filter Builder Unit Tests
- NL Intelligence Tests
- CMDB Tools Unit Tests
- SQL Equivalent Explainer
- Filter Validator Analysis
- Identity Table Wrappers
- Request Executor 401 Retry
- MCPB Package Build
- get ci details Probes
- KB Duplicate Check
- Priority Filter Validation
- CMDB Search Helpers
- CI Types and Failure Paths
- Priority Parsing Tests
- Query Debug Construction Tests
- Query Validation Helpers
- Month Range Parsing
- Query Encoding Guard Tests
- Release Docs and Diagrams
- OAuth Architecture Docs
- Result Count Validation
- Publish With Verify
- SN Query Probe Harness Tests
- Token Footprint Tests
- Tool Organization Docs
- Find Cis By Type
- Priority Incidents Tool
- Retire Knowledge Article
- VTB Create Private Task
- VTB Update Private Task
- CMDB Validation Tests
- NL Date Range Parsing
- Query Value Encoding
- Table Tools Read Helpers
- Typed Read Kb
- Run Tests
- Integration
- Semantic Versioning
- Query Validation
- Query Intelligence
- Query Intelligence (2)
- Query Validation (2)
- Kb Article Tools
- Vtb Task Tools
- Generic Table Tools Tests
- CMDB Tools Module
- No Stdout Pollution
- Generic Table Tools
- 05-Ai-Intelligence-Flow
- E2E Tests PROMPTS
- Query Intelligence (3)
- Query Validation (3)
- Generic Table Tools (2)
- Generic Table Tools (3)
- oauth/ Package
- Query Intelligence (4)
- Utils.Py
- Http Layer Errors
- Generic Tool Wrappers
- Integration Tests
- Query Intelligence (5)
- Query Intelligence (6)
- Query Validation (4)
- Http Layer Url Builder
- Url
- Kb Article Tools (2)
- Generic Table Tools Tests (2)
- Query Validation Tests
- Query Validation (5)
- Filter Value Encoding
- Http Layer Errors (2)
- Pyproject Sync
- Run
- Cmdb Citype Validation
- Vtb Task Tools (2)
- Generic Table Tools Tests (3)
- Query Intelligence Tests
- 01-Architecture-Overview
- Query Validation (6)
- Filter Explainer
- Oauth Client
- Cmdb Citype Validation (2)
- Consolidated Tools
- Kb Article Tools (3)
- Kb Article Tools (4)
- Vtb Task Tools (3)
- Oauth Client Enhanced Tests
- Query Intelligence (7)
- Query Intelligence (8)
- Query Intelligence (9)
- Table Tools Generic Table Tools
- Generic Table Tools (4)
- Filtering Tests
- Generic Table Tools Tests (4)
- Oauth Client (2)
- Query Intelligence Tests (2)
- Query Value Encoding Tests
- Token Footprint Tests (2)
- Consolidated Tools (2)
- Generic Tool Wrappers (2)
- Mcp Tools Tests
- Oauth Tests
- Filter Builder
- Filter Builder (2)
- Query Intelligence (10)
- Query Intelligence (11)
- Type
- Type (2)
- Env
- Cmdb
- Personal Mcp Servicenow Main
- Generic Table Tools (5)
- Generic Table Tools (6)
- Cli Tests
- Query Value Encoding Tests (2)
- CMDB Tools (6)
- Query Validation (7)
- Type (3)
- Table Tools Vtb Task Tools
- Conftest
- Bitbucket CI Pipeline
- Filter Explainer (2)
- Win32
- Init Tests
- Query Value Encoding Tests (3)
- Query Value Encoding Tests (4)
- Query Value Encoding Tests (5)
- Vtb Task Tools Tests
- Vtb Task Tools Tests (2)
- Vtb Task Tools Tests (3)
- PayPal Sponsor Funding
- Personal-Mcp-Servicenow
- BaseException
- Fixture

## God Nodes (most connected - your core abstractions)
1. `ServiceNowRequestError` - 81 edges
2. `ServiceNowOAuthClient` - 59 edges
3. `ErrorCode` - 58 edges
4. `_send()` - 41 edges
5. `QueryValidationResult` - 39 edges
6. `KbDuplicateCheckInconclusive` - 39 edges
7. `QueryIntelligence` - 37 edges
8. `TokenStore` - 36 edges
9. `_check_kb_duplicates()` - 35 edges
10. `encode_query_value()` - 34 edges

## Surprising Connections (you probably didn't know these)
- `03 Tool Organization Diagram` --semantically_similar_to--> `39 MCP Tools Inventory`  [INFERRED] [semantically similar]
  Diagrams & Documentation/README.md → README.md
- `ServiceNow Date Range Filters` --semantically_similar_to--> `QueryIntelligence Regex NL Parser`  [INFERRED] [semantically similar]
  SERVICENOW_QUERY_GUIDE.md → Diagrams & Documentation/05-ai-intelligence-flow.md
- `SLA Token Optimization Strategy` --semantically_similar_to--> `GET Token-Optimization Invariants`  [INFERRED] [semantically similar]
  Diagrams & Documentation/06-sla-architecture-flow.md → CHANGELOG.md
- `Personal MCP ServiceNow Integration Server` --semantically_similar_to--> `Personal MCP ServiceNow Project`  [INFERRED] [semantically similar]
  README.md → CHANGELOG.md
- `get_query_syntax_help Tool` --semantically_similar_to--> `Encoded Query OR Syntax ^OR`  [INFERRED] [semantically similar]
  Diagrams & Documentation/05-ai-intelligence-flow.md → SERVICENOW_QUERY_GUIDE.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **v4.0 Package Split (filter + http_layer + oauth)** — changelog_filter_package, changelog_http_layer_package, changelog_oauth_package, changelog_release_4_0_0 [EXTRACTED 1.00]
- **Encoded-Query Value Guard Layers (4.4.1)** — changelog_encode_query_value, changelog_caret_refusal, changelog_ampersand_escape, changelog_nq_refusal, changelog_structural_vs_terminal_handlers, changelog_encoded_query_value_boundary [EXTRACTED 1.00]
- **End-to-End Layered Request Path** — readme_fastmcp, readme_generic_table_tools, changelog_filter_package, changelog_http_layer_package, changelog_oauth_package, readme_servicenow_rest_api [EXTRACTED 1.00]
- **GET Read-Path Pipeline** — diagrams_documentation_01_architecture_overview_generic_table_tools, diagrams_documentation_01_architecture_overview_make_nws_request, diagrams_documentation_04_similarity_search_flow_url_builder, diagrams_documentation_04_similarity_search_flow_response_parser, diagrams_documentation_02_oauth_request_executor [EXTRACTED 1.00]
- **NL Filter Intelligence Pipeline** — diagrams_documentation_05_ai_intelligence_flow_intelligent_search, diagrams_documentation_05_ai_intelligence_flow_query_intelligence, diagrams_documentation_05_ai_intelligence_flow_validator, diagrams_documentation_05_ai_intelligence_flow_builder, diagrams_documentation_05_ai_intelligence_flow_explainer, diagrams_documentation_01_architecture_overview_filter_package [EXTRACTED 1.00]
- **OAuth Authentication Stack** — diagrams_documentation_02_oauth_singleton, diagrams_documentation_02_oauth_client_facade, diagrams_documentation_02_oauth_token_store, diagrams_documentation_02_oauth_request_executor, diagrams_documentation_02_oauth_http_pool, diagrams_documentation_02_oauth_client_credentials [EXTRACTED 1.00]

## Communities (166 total, 12 thin omitted)

### Community 0 - "OAuth Client Auth Headers"
Cohesion: 0.05
Nodes (45): Return Authorization + JSON headers for an API request. Inlined (rather than…, OAuth 2.0 Client Credentials implementation for ServiceNow. Composes three…, ServiceNowOAuthClient, setter, asyncio, dict, Test access token request functionality., Test successful token request. (+37 more)

### Community 1 - "Generic Table Query Engine"
Cohesion: 0.06
Nodes (42): BaseModel, Generic filter parameters for table queries., TableFilterParams, get_record_details(), get_records_by_priority(), _make_paginated_request(), PartialPageReadError, Exception (+34 more)

### Community 2 - "Encoded Query Value Escape"
Cohesion: 0.05
Nodes (67): encode_query_value(), Escape one caller-supplied value for use inside a ``sysparm_query``. Args:…, Build a refusal from a message template in ``constants``. Keeps the value echo…, _build_additional_filters(), _build_debug_extras(), _build_debug_info(), _build_priority_filter(), _build_query_condition() (+59 more)

### Community 3 - "Query Builder Operator Tests"
Cohesion: 0.03
Nodes (34): Test query building functions., Test detecting operators in value., Test detecting ServiceNow text/date operators at start of value., Test non-operator values., Newly recognized encoded-query operators are detected., IN' must not be misread when it is just the start of a word., CONTAINS/NOTCONTAINS (GlideRecord-only) rewrite to LIKE/NOT LIKE., A CONTAINS filter value becomes a LIKE encoded-query condition. (+26 more)

### Community 4 - "Constants and Error Codes"
Cohesion: 0.06
Nodes (46): Constants used throughout the ServiceNow MCP server., ErrorCode, _from_decode(), _from_oauth_auth(), _from_oauth_connection(), _from_oauth_forbidden(), _from_status_error(), _from_timeout() (+38 more)

### Community 5 - "Text Search and Pagination"
Cohesion: 0.05
Nodes (37): The field a free-text search must target for *table_name*., text_search_field_for(), get_record_description(), _is_safe_record_number(), _partial_envelope(), query_table_by_text(), query_table_with_filters(), Mark an otherwise-normal response as a partial read. The one sanctioned shape… (+29 more)

### Community 6 - "OAuth Client Facade"
Cohesion: 0.06
Nodes (40): ServiceNowOAuthClient — orchestrator façade. Composes ``TokenStore`` +…, Exception, OAuth-domain exception hierarchy., Exception raised when authentication fails., Exception raised when connection to ServiceNow fails., Exception raised when authorization is denied., Base exception for ServiceNow OAuth operations., ServiceNowAuthenticationError (+32 more)

### Community 7 - "Config Loader"
Cohesion: 0.07
Nodes (37): ConfigError, get_config_dir(), get_config_file_path(), get_setup_instructions(), load_config(), load_config_from_env(), load_config_from_file(), Any (+29 more)

### Community 8 - "Date Utils and SLA Ranges"
Cohesion: 0.06
Nodes (29): datetime, Read-only view of the current token's expiry., _sla_filter_breached(), _sla_filter_performance(), build_last_n_days_filter(), get_last_n_days_range(), get_this_week_range(), Get start and end dates for the last N days (including today). Args: days:… (+21 more)

### Community 9 - "OAuth Connection Tests"
Cohesion: 0.07
Nodes (39): Test OAuth connection and return status., test_oauth_connection(), coerce_json_dict(), coerce_json_list(), Any, Param-boundary JSON coercion for MCP tool signatures. LLM-driven MCP clients…, Peel repeated JSON-string layers (handles single- AND double-encoded input).…, Coerce a (possibly double-encoded) stringified JSON array to a native list. (+31 more)

### Community 10 - "Consolidated Tools Suite"
Cohesion: 0.07
Nodes (30): _build_metadata(), _build_priority_result_message(), _format_deduped_kb_row(), get_active_knowledge_articles(), get_knowledge_by_category(), get_sla_details(), _merge_filters(), Any (+22 more)

### Community 11 - "Auth and KB Test Tools"
Cohesion: 0.06
Nodes (25): nowtest_auth_input(), nowtestauth(), Test function to verify authentication with ServiceNow standard API., Get ServiceNow table schema information for a given table., Test knowledge base tools., Test finding knowledge articles by text., Test getting knowledge articles by category., Test getting active knowledge articles. (+17 more)

### Community 12 - "HTTP Layer Encoding Tests"
Cohesion: 0.05
Nodes (25): patch, Test extracting display values from non-dict input., Test that URLs without sysparm_query pass through unchanged., Test that spaces in query values are percent-encoded., Test that ServiceNow operators (=, ^, <, >, etc.) are preserved., Test that # in query is encoded to prevent URL fragment issues., Test that already-encoded URLs are not double-encoded., Test that other URL parameters are not affected by encoding. (+17 more)

### Community 13 - "Date Filter Utilities"
Cohesion: 0.06
Nodes (30): build_date_filter(), get_current_month_range(), get_today_range(), get_yesterday_range(), normalize_date_to_full_format(), Date utilities for ServiceNow MCP incident queries. Provides date validation,…, Build ServiceNow date filter using simple >= and <= operators. This replaces…, Get start and end dates for the current calendar month. Returns: Tuple of… (+22 more)

### Community 14 - "Audit Middleware"
Cohesion: 0.08
Nodes (36): AuditMiddleware, Middleware, MiddlewareContext, Audit logging middleware for MCP tool calls. Emits one structured JSON log line…, _sanitize(), _summarize(), _user_from_headers(), AuthMiddleware (+28 more)

### Community 15 - "Request Dispatcher Parser"
Cohesion: 0.08
Nodes (24): make_nws_request(), Make a request to the ServiceNow API using OAuth 2.0 authentication. For GET…, extract_display_values(), extract_field_value(), process_item_dict(), Any, Response payload transformation for ServiceNow read responses. When…, Extract the display value if available, otherwise return the raw value. (+16 more)

### Community 16 - "Tool Selection Evaluation"
Cohesion: 0.07
Nodes (29): _evaluate(), evaluation(), _plausible_paths(), _profiles(), fixture, parametrize, _rank(), Golden intent set — tool-selection baseline (v4.4 Tier 0.1). Measures whether… (+21 more)

### Community 17 - "OAuth Auth Info Tests"
Cohesion: 0.06
Nodes (25): get_auth_info(), Any, Get information about current authentication method., dict, patch, Test OAuth client creation fails with missing environment variables., Test API client integration with OAuth., Test that get_auth_info correctly detects OAuth configuration. (+17 more)

### Community 18 - "CMDB Probe and Encoding"
Cohesion: 0.10
Nodes (37): _probe_ci_table(), Fetch a CI by number from one table; return the first row, or None if absent.…, query_table_with_generic_filters(), Generic function to query any table with filters., v4.4.1 — the encoded-query value boundary, asserted against what ServiceNow…, Run *call* with the transport stubbed at the OAuth boundary. Patched at…, A bare value, so `_build_query_condition` falls through to exact match. The…, `assigned_to_gte` -> `assigned_to>=`, a third terminal handler. (+29 more)

### Community 19 - "Query Intelligence NL Parse"
Cohesion: 0.08
Nodes (21): build_smart_filter(), Any, Check for template match and return template data., Parse exclusion patterns and return exclusion filters., Try to parse date range from query., Build keyword-based fallback filter. The field comes from…, Parse natural language query into ServiceNow filters with intelligence., Check if query matches a predefined template. (+13 more)

### Community 20 - "Query Explainer"
Cohesion: 0.07
Nodes (18): Generate explanation for priority filter., Generate explanation for date-related filters. Matches the gs.* helpers the NL…, Generate explanation for state filter., Generate explanation for assigned_to filter., Generate explanation for complete query filter., Generate human-readable explanation of what the filter will do., Test filter explanation generation., Test explaining single priority filter. (+10 more)

### Community 21 - "SLA Status Presets"
Cohesion: 0.11
Nodes (15): _build_sla_status_filter(), OptJsonDict, OptJsonList, query_slas_by_status(), query_slas_custom(), Translate an SLA status preset into a (filter_dict, fields) pair., Query SLA records by a named status preset. Args: status: one of: - active:…, Custom SLA query — escape hatch for filter shapes the presets do not cover.… (+7 more)

### Community 22 - "Request Dispatcher Singleton"
Cohesion: 0.08
Nodes (26): _get_typed(), Read/write request dispatcher for the ServiceNow REST API. This is the v4.0…, The GET pipeline, with failures raised as ``ServiceNowRequestError``. An empty…, Path + stable query hash for stderr logs — never the raw sysparm_query., _redact_url(), get_oauth_client(), _hydrate_env_from_config(), make_oauth_request() (+18 more)

### Community 23 - "Filter Validation Result"
Cohesion: 0.08
Nodes (18): Delegate validation + auto-correction to the validator module. Kept as a…, QueryValidationResult, Container for query validation results., Add a warning message., Add a suggestion for improvement., True if the query is invalid or has warnings., Test filter validation and auto-correction., Test that comma-separated priorities are corrected to OR syntax. (+10 more)

### Community 24 - "Param Coercion Tests"
Cohesion: 0.06
Nodes (7): Tests for param_coercion.py — JSON-string coercion at the MCP tool param…, Regression tests for the double-encoding bug found in E2E: some MCP clients…, TestDoubleEncoding, TestJsonDict, TestJsonList, TestOptJsonDict, TestOptJsonList

### Community 25 - "KB Dedup Title Encoding"
Cohesion: 0.09
Nodes (16): asyncio, parametrize, `[]` must mean "checked, clear" and nothing else., A '^' in the title splits the encoded query, silently widening it. Encoding…, v4.4.1: '&' was a transport defect, not an unrepresentable value. The encoder…, The quiet one, fixed: '%XY' used to be decoded on its way out. v4.4.0 searched…, No false positives: an ordinary "50% off" title is checked, not refused., Only ^ is unrepresentable; everything else survives the round trip. Pinned so a… (+8 more)

### Community 26 - "get record Tool Wrappers"
Cohesion: 0.10
Nodes (17): get_record(), Get full detail fields for a single known record by number. Use when you know…, Test get_record generic tool., TestGetRecord, _Capture, asyncio, parametrize, A bare short_description condition is the silently-dropped filter. Splitting on… (+9 more)

### Community 27 - "KB Article Write Tools"
Cohesion: 0.10
Nodes (24): JsonList, _call_kb_publish_workflow(), _call_kb_workflow(), _check_single_kb_duplicate(), _dedup_query_defect(), _duplicate_check_inconclusive(), _duplicate_row_inconclusive(), _fire_publish() (+16 more)

### Community 28 - "Date Format Validation"
Cohesion: 0.10
Nodes (16): Validate date format is either "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS". Args:…, validate_date_format(), Test date format validation., Test valid YYYY-MM-DD format., Test valid YYYY-MM-DD HH:MM:SS format., Test valid midnight time., Test valid end of day time., Test invalid MM-DD-YYYY format. (+8 more)

### Community 29 - "Similar Records Engine"
Cohesion: 0.08
Nodes (24): _build_fallback_response(), _build_intelligence_response(), _exclude_original_record(), find_similar_records(), _first_short_description(), _format_priority_results(), _generic_filter_envelope(), Any (+16 more)

### Community 30 - "KB Batch Publish Helpers"
Cohesion: 0.11
Nodes (14): BaseException, KbDuplicateCheckInconclusive, _normalize_publish_result(), _outcome_error_message(), Exception, Message for an exception that escaped a per-article coroutine., Normalize publish_knowledge_article output into a flat batch-result row. Four…, The duplicate check could not produce a trustworthy answer. Distinct from "no… (+6 more)

### Community 31 - "Publish Knowledge Tests"
Cohesion: 0.12
Nodes (13): fixture, publish_knowledge_article(), Publish a knowledge article via the ServiceNow workflow endpoint. Runs a…, TestPublishKnowledgeArticle, _no_sleep(), The guard must not have become so strict that nothing can publish., A failed read reaches the publish guard through the real dispatcher. These…, Fake the transport under the real dispatcher; record every write. (+5 more)

### Community 32 - "Filter Builder Unit Tests"
Cohesion: 0.07
Nodes (15): patch, Test multiple caller exclusions by sys_id., Test that URL encoding preserves JavaScript functions., Test ServiceNowQueryBuilder query validation., Test TableFilterParams object creation and validation., Test combined filtering with mocked API call., Test single priority value parsing., Test suite for ServiceNow filtering functionality using unittest. (+7 more)

### Community 33 - "NL Intelligence Tests"
Cohesion: 0.09
Nodes (17): patch, Test complete natural language parsing., Test parsing that matches a template., Test parsing without template match., Test keyword fallback when no patterns match., Test parsing with date range., Test parsing with exclusion patterns., Test the main intelligent filter building function. (+9 more)

### Community 34 - "CMDB Tools Unit Tests"
Cohesion: 0.08
Nodes (14): Test finding CIs with invalid type., Test searching CIs by name attribute., Test searching CIs by IP address attribute., Test searching CIs by multiple attributes., Test successful CI details retrieval., Test suite for CMDB tools functionality., Test CI details retrieval for non-existent CI., Test finding similar CIs for a given CI. (+6 more)

### Community 35 - "SQL Equivalent Explainer"
Cohesion: 0.12
Nodes (12): QueryIntelligence, Smart query building and validation for ServiceNow filters., Generate SQL-like representation for debugging., Determine appropriate SQL condition based on field and value., Test SQL equivalent generation., Test SQL generation for empty filters., Test SQL generation for single filter., Test SQL generation for OR conditions. (+4 more)

### Community 36 - "Filter Validator Analysis"
Cohesion: 0.13
Nodes (24): _analyze_caller_exclusion(), _analyze_date_filtering(), _analyze_javascript_functions(), _analyze_original_filters(), _analyze_priority_filtering(), _analyze_url_encoding(), _correct_date(), _correct_priority() (+16 more)

### Community 37 - "Identity Table Wrappers"
Cohesion: 0.12
Nodes (16): find_similar(), get_record_summary(), Any, Find records similar to an existing record (by short_description). Looks up the…, Return an error dict if *table* is not in TABLE_CONFIGS, else None., Table validation for the tools that address records by number or description.…, Get the short_description for a single record by its number. Supported tables:…, _validate_identity_table() (+8 more)

### Community 38 - "Request Executor 401 Retry"
Cohesion: 0.12
Nodes (15): AuthHeaderSource, Any, AsyncClient, Response, Drop the cached token, re-authenticate, retry once., Make authenticated HTTP requests with token-refresh on 401., Make an authenticated request to ServiceNow API. When…, Decode a successful response payload. (+7 more)

### Community 39 - "MCPB Package Build"
Cohesion: 0.15
Nodes (22): assert_no_leaks(), assert_versions_aligned(), clean_staging(), copy_package_dirs(), copy_root_files(), fail(), main(), Path (+14 more)

### Community 40 - "get ci details Probes"
Cohesion: 0.15
Nodes (11): get_ci_details(), Get comprehensive details for a specific Configuration Item. Args: ci_number:…, asyncio, Previously any type outside the static list was ignored and all 7 probed., The concurrent probe must pair each row with the table it came from. The probes…, Probe order is a priority order: the earliest matching table wins., TestGetCiDetails, _by_table() (+3 more)

### Community 41 - "KB Duplicate Check"
Cohesion: 0.18
Nodes (7): _check_kb_duplicates(), Return KB articles matching short_description exactly across live workflow…, Check for duplicate KB articles without publishing. For each number: looks up…, asyncio, The headline fix: [] means "checked, clear" and nothing else. The old test…, TestCheckKbDuplicates, TestCheckKbDuplicatesTool

### Community 42 - "Priority Filter Validation"
Cohesion: 0.11
Nodes (16): _has_comma_syntax_issue(), _has_or_format_issue(), Check if priority filter has comma syntax issue., Check if OR syntax is missing priority= prefix., Check if numeric format suggestion should be added., Validate priority filter syntax with enhanced debugging., _should_suggest_numeric_format(), validate_priority_filter() (+8 more)

### Community 43 - "CMDB Search Helpers"
Cohesion: 0.13
Nodes (15): _build_similar_ci_response(), _extract_ci_search_attributes(), _filter_and_limit_ci_results(), Any, quick_ci_search(), Extract search attributes from CI data. Complexity: 4, Filter out original CI and limit results. Complexity: 3, Build response for similar CIs. Complexity: 2 (+7 more)

### Community 44 - "CI Types and Failure Paths"
Cohesion: 0.17
Nodes (7): get_all_ci_types(), Get all available CI types/classes in the CMDB. Returns: Dictionary of the CI…, _assert_plain_failure(), asyncio, cmdb_ci_server times out; the base cmdb_ci row must NOT be the answer. cmdb_ci…, Narrowing the except must not remove the catch-all for real bugs., TestSingleRequestReads

### Community 45 - "Priority Parsing Tests"
Cohesion: 0.09
Nodes (12): Test priority parsing functions., Test normalizing P-notation., Test normalizing plain numbers., Test cleaning priority input., Test processing comma-separated priorities., Test processing P-notation priorities., Test formatting single priority., Test parsing single priority. (+4 more)

### Community 46 - "Query Debug Construction Tests"
Cohesion: 0.09
Nodes (12): Test query construction debugging functionality., Test basic query construction debugging., Test priority filtering detection in debug., Test date BETWEEN syntax detection in debug., Test caller exclusion detection in debug., Test detection of old date syntax as potential issue., Test detection of unencoded spaces as potential issue., Test recommendation for overly complex queries. (+4 more)

### Community 47 - "Query Validation Helpers"
Cohesion: 0.13
Nodes (13): build_pagination_params(), Build pagination parameters for ServiceNow queries., Provide suggestions for query improvements., suggest_query_improvements(), Comprehensive tests for the filter/ package (was query_validation.py before…, Test utility and helper functions., Test cross verification function structure., Test building pagination parameters with defaults. (+5 more)

### Community 48 - "Month Range Parsing"
Cohesion: 0.12
Nodes (13): _parse_cross_month_range(), _parse_month_range_format(), Parse 'Month DD-DD, YYYY' format. Complexity: 3, Parse 'Month DD YYYY to Month DD YYYY' format. Complexity: 3, Test parsing valid month range format., Test parsing month range with different month names., Test parsing invalid month name returns None., Test parsing cross-month range. (+5 more)

### Community 49 - "Query Encoding Guard Tests"
Cohesion: 0.12
Nodes (12): asyncio, Dot-walking is how `task_sla` is queried at all — it must survive., The second assembly path has to repeat the check, not inherit it., `get_ci_details` gathers its probes with `return_exceptions=True`. Its loop re-…, The three filter keys that take a fragment instead of a value. `_date_range`,…, It cannot be escaped, and a raw '&' truncates the fragment silently., The guard must not be so broad it refuses the real thing.…, Gated off by default, so the guard behind the gate needs its own test. (+4 more)

### Community 50 - "Release Docs and Diagrams"
Cohesion: 0.13
Nodes (20): Claude Desktop Extension (.mcpb) Packaging, OR-Combined LIKE Text Query, Release 4.3.0 — mcpb Packaging and Performance, SSE Transport Authentication, 01 Architecture Overview Diagram, Architecture Documentation Index (v4.3 Diagrams), Distribution via .mcpb or Docker SSE, 04 Similarity Search Flow Diagram (+12 more)

### Community 51 - "OAuth Architecture Docs"
Cohesion: 0.12
Nodes (20): OAuth Authentication Flow Document, OAuth 2.0 Client Credentials Flow, ServiceNowOAuthClient Facade, oauth/http_pool Shared Client, RequestExecutor 401 Retry, oauth/singleton Process-Wide Client, TOKEN_REFRESH_BUFFER_MINUTES, TokenStore Cache and Refresh (+12 more)

### Community 52 - "Result Count Validation"
Cohesion: 0.12
Nodes (14): _is_high_priority_query(), Check if query is for high-priority (P1/P2) records., Validate incident result count against expected baselines., Validate if result count seems reasonable for the query., _validate_incident_result_count(), validate_result_count(), Test result count validation functionality., Test validation passes for normal incident count. (+6 more)

### Community 53 - "Publish With Verify"
Cohesion: 0.14
Nodes (10): _publish_with_verify(), Fire the publish workflow then verify by polling for a Published row. Treats…, Fire-and-verify orchestrator — verify is the only success signal., The main bug class: POST times out, SN still committed the publish., Regression: anyio.fail_after raises builtin TimeoutError, not…, When fire keeps raising HTTPStatusError and verify never finds Published, the…, TestPublishWithVerify, The retry path is for a verify that positively says "not published yet". (+2 more)

### Community 54 - "SN Query Probe Harness Tests"
Cohesion: 0.15
Nodes (18): assert_no_smuggled_parameter(), What ServiceNow's condition parser actually receives, modelled for tests.…, The parameters ServiceNow's servlet layer would see, percent-decoded., The decoded ``sysparm_query`` split into conditions on ``^``., The one condition beginning with *prefix*, with the prefix stripped. Raises if…, No URL parameter appeared that the caller did not ask for. The signature of the…, servicenow_conditions(), servicenow_params() (+10 more)

### Community 55 - "Token Footprint Tests"
Cohesion: 0.24
Nodes (12): _count_tokens(), asyncio, parametrize, Token-footprint regression tests for v4.0 SLA tools. The Sprint 2 acceptance…, Per-tool token budgets — must not regress structurally., v3 bug returned 10K rows; v4 must return 1., Critical preset budget is tight because the field list is curated., Token budget invariant: custom with fields=None never returns all columns. (+4 more)

### Community 56 - "Tool Organization Docs"
Cohesion: 0.12
Nodes (19): consolidated_tools Module, generic_table_tools Query Engine, Generic Tool Wrappers, TABLE_CONFIGS Supported Tables, Tool Organization Document, Table Extensibility via TABLE_CONFIGS, filter_records Tool, v3 Generic Wrapper Consolidation (+11 more)

### Community 57 - "Find Cis By Type"
Cohesion: 0.16
Nodes (11): find_cis_by_type(), Find all Configuration Items of a specific type. Args: ci_type: CI class/table…, _Capture, ci_type validation across the CMDB tools (v4.4 Tier 0.6). The bug:…, number_ref is a numbering-config reference; calling it record_count lied., Table segment of a ServiceNow Table API URL., Records every URL passed to make_nws_request and returns a canned payload.…, Table segment of each captured URL. (+3 more)

### Community 58 - "Priority Incidents Tool"
Cohesion: 0.15
Nodes (9): get_priority_incidents(), Get incidents by priority with optional date range filtering. Uses simple >= /…, Test get_priority_incidents function., Test enhanced get_priority_incidents with date filtering., TestGetPriorityIncidents, TestGetPriorityIncidentsEnhanced, _mcp_get_priority_incidents(), Any (+1 more)

### Community 59 - "Retire Knowledge Article"
Cohesion: 0.15
Nodes (9): Retire a knowledge article via the ServiceNow workflow endpoint. Args:…, retire_knowledge_article(), _unwrap_kb_write_response(), Tests for kb_article_tools.py — KB article write path (update / publish /…, Verify write ops use make_nws_request write path (not GET path)., An empty write response cannot establish that the write landed., TestRetireKnowledgeArticle, TestRoutesThroughUnifiedPipeline (+1 more)

### Community 60 - "VTB Create Private Task"
Cohesion: 0.12
Nodes (12): create_private_task(), _prepare_task_create_data(), Any, Private task (vtb_task) CRUD. Read-failure contract (v4.4 Tier 0.3). A failed…, Create a new private task record in ServiceNow. Args: task_data: Dictionary…, Prepare and validate data for task creation., Test preparing task data with minimal required fields., Test preparing task data with optional fields. (+4 more)

### Community 61 - "VTB Update Private Task"
Cohesion: 0.21
Nodes (10): Update an existing private task record in ServiceNow. Args: task_number: The…, update_private_task(), _assert_plain_failure(), asyncio, fixture, Decision (b): absent is still absent, and the message is unchanged., A rejected field must not cost a round trip., A failed lookup reaches `update_private_task` through the real dispatcher.… (+2 more)

### Community 62 - "CMDB Validation Tests"
Cohesion: 0.11
Nodes (11): Test input validation and error handling for CMDB tools., Test CI number format validation., Test CI type parameter validation., Test search attributes parameter validation., Test search term validation for quick search., Integration tests for CMDB tools workflow., Set up integration test fixtures., Test complete CMDB discovery workflow. (+3 more)

### Community 63 - "NL Date Range Parsing"
Cohesion: 0.11
Nodes (10): _parse_date_range_from_text(), Parse date range from natural language text with ReDoS protection. Handles…, Test handling of invalid date format inputs., Test parsing of Week 35 2025 date range., Test parsing of month range format., Test parsing of ISO date range format., Test main parser with month range., Test main parser with ISO format. (+2 more)

### Community 64 - "Query Value Encoding"
Cohesion: 0.12
Nodes (11): parametrize, `query_table_by_text` is safe by accident, so the accident is pinned.…, Pins the mechanism, not just today's outputs. A test that only checks sample…, Covers the record-number branch too, which has its own patterns.…, A refusal that still sends the request would defeat the point. The KB duplicate…, The last `&` hole: structural handlers paste a caller fragment verbatim. A…, The reachable surface, not just the internal function., The guard refuses `&` only. Everything these fragments are made of stays. (+3 more)

### Community 65 - "Table Tools Read Helpers"
Cohesion: 0.18
Nodes (11): get_kb_articles_by_state(), List kb_knowledge articles de-duplicated by article number. ServiceNow KB…, carry_partial(), carry_partial_after_filter(), is_read_failure(), Any, Shared read-response helpers for the typed-read consumers (v4.4 Tier 0.3).…, True when *response* is a read failure carrying no usable rows. A partial read… (+3 more)

### Community 66 - "Typed Read Kb"
Cohesion: 0.17
Nodes (6): Update fields on a knowledge article by article number (e.g. KB0001234). Args:…, update_knowledge_article(), TestUpdateKnowledgeArticle, _assert_plain_failure(), Decision (d): a write never reports "not found" because a lookup failed., TestPreWriteReadsDistinguishAbsentFromFailed

### Community 67 - "Run Tests"
Cohesion: 0.20
Nodes (16): check_test_environment(), main(), Show coverage results if available., Main test runner function., Run a command and return success status., Run all tests with coverage reporting and JUnit XML output., Run a specific test module., Run only integration tests. (+8 more)

### Community 68 - "Integration"
Cohesion: 0.16
Nodes (9): asyncio, parametrize, The decoded sysparm_query value from a captured request URL., The outbound query equals the caller's conditions — nothing appended. Domain…, Nothing is dropped after the response comes back. The URL assertions above…, create_private_task → make_nws_request(method=POST) → oauth_client…, search_records → query_table_by_text → make_nws_request → make_oauth_request., TestReadPipelineEndToEnd (+1 more)

### Community 69 - "Semantic Versioning"
Cohesion: 0.13
Nodes (16): Ampersand (&) Value Escape, Caret (^) Value Refusal, Domain Filtering Removal, encode_query_value / filter/value_encoding.py, Encoded-Query Value Boundary Contract, _has_operator_in_value Equals Limitation, KB Publish Fail-Closed Duplicate Check, Keep a Changelog Format (+8 more)

### Community 70 - "Query Validation"
Cohesion: 0.12
Nodes (8): Build a complete ServiceNow filter string with proper syntax. Args: priorities:…, Test building complete filter with priorities only., Test building complete filter with date range only., Test building complete filter with date period only., Test building complete filter with caller exclusions only., Test building complete filter with all components., Test that date_range takes precedence over date_period., Test that additional filters don't duplicate existing fields.

### Community 71 - "Query Intelligence"
Cohesion: 0.17
Nodes (9): Apply context-based filters (e.g., user preferences, previous queries)., Test context-based filter application., Test applying date range from context., Test applying single caller exclusion from context., Test applying multiple caller exclusions from context., Test applying exclude resolved from context., Test applying user-assigned filter from context., Test that empty context returns empty filters. (+1 more)

### Community 72 - "Query Intelligence (2)"
Cohesion: 0.17
Nodes (9): Parse language patterns and update filters., Test natural language pattern parsing., Test parsing critical/P1 patterns., Test parsing high/P2 patterns., Test parsing time-based patterns., Test parsing state patterns., Test parsing assignment patterns., Test parsing 'last N days' pattern with lambda. (+1 more)

### Community 73 - "Query Validation (2)"
Cohesion: 0.16
Nodes (10): Validate date range filter completeness and format., validate_date_range_filter(), Test date range filter validation functionality., Test validating proper BETWEEN syntax., Test validation warns about old comparison syntax., Test validation warns about BETWEEN without JavaScript functions., Test validation warns about missing @ separator., Test validation provides suggestion for Week 35 2025. (+2 more)

### Community 74 - "Kb Article Tools"
Cohesion: 0.23
Nodes (7): _handle_kb_error(), HTTPStatusError, _write_kb_article(), _make_http_status_error(), HTTPStatusError, TestHandleKbError, TestWriteKbArticle

### Community 75 - "Vtb Task Tools"
Cohesion: 0.29
Nodes (7): Send a write request through make_nws_request, mapping errors locally., _write_private_task(), _make_http_status_error(), asyncio, HTTPStatusError, Test the unified write helper that wraps make_nws_request., TestWritePrivateTask

### Community 76 - "Generic Table Tools Tests"
Cohesion: 0.12
Nodes (9): Test edge cases and error handling., Test priority parsing with special characters., Test building query with suffix operators., Test that encoding preserves important ServiceNow characters., Test exception handling in find_similar_records., Test getting records by priority with additional filters., Test exception handling in get_records_by_priority., Test exception handling in query_table_with_generic_filters. (+1 more)

### Community 77 - "CMDB Tools Module"
Cohesion: 0.15
Nodes (15): get_sla_details v3 Bug Fix, SLA Tool Consolidation (Sprint 2), 05 AI Intelligence Flow Diagram, 06 SLA Architecture Flow Diagram, CMDB Tools Module, KB Article Write Tools, make_nws_request Dispatcher, VTB Private Task CRUD Tools (+7 more)

### Community 78 - "No Stdout Pollution"
Cohesion: 0.19
Nodes (14): expr, _find_offending_prints(), _is_stderr_target(), _iter_runtime_modules(), Path, Lint guard: server runtime code must never print to stdout. MCP stdio transport…, Self-check: the AST scanner must NOT flag stderr-routed prints., True when the ``file=`` argument resolves to ``sys.stderr``. (+6 more)

### Community 79 - "Generic Table Tools"
Cohesion: 0.19
Nodes (9): Pre-validate input to prevent ReDoS attacks., _validate_regex_input(), Test ReDoS (Regular Expression Denial of Service) protection., Test validation accepts valid strings., Test validation rejects non-strings., Test validation rejects overly long strings., Test validation rejects strings with too many spaces., Test validation with edge case strings. (+1 more)

### Community 80 - "05-Ai-Intelligence-Flow"
Cohesion: 0.19
Nodes (14): filter Intelligence-Builder Backref Discipline, filter/ Package Pipeline, Intelligent Query Tools, NL Filter Intelligence Document, ServiceNowQueryBuilder, QueryExplainer, QueryIntelligence Regex NL Parser, get_query_syntax_help Tool (+6 more)

### Community 81 - "E2E Tests PROMPTS"
Cohesion: 0.15
Nodes (14): find_similar Tool, search_records Tool, Search and Query Flow Document, Paginated Request with ORDERBYDESC, query_table_by_text Engine, Similarity Search Path, Intelligence Confidence Metadata, intelligent_search Tool (+6 more)

### Community 82 - "Query Intelligence (3)"
Cohesion: 0.15
Nodes (9): get_filter_templates(), Get all available filter templates., Comprehensive tests for filter/intelligence.py (was query_intelligence.py…, Test filter template functionality., Test that FILTER_TEMPLATES constant is properly defined., Test that all expected templates exist., Test that templates have proper structure., Test convenience function for getting templates. (+1 more)

### Community 83 - "Query Validation (3)"
Cohesion: 0.19
Nodes (9): Main filter validation function using dedicated helpers., validate_query_filters(), Test the main validate_query_filters function., Test validating empty filters., Test validating filters with priority only., Test validating filters with date only., Test validating filters with both priority and date issues., Test that validation ignores other (non-validated, non-reference) fields… (+1 more)

### Community 84 - "Generic Table Tools (2)"
Cohesion: 0.15
Nodes (9): build_and_validate_smart_filter(), Build and validate an intelligent filter without executing the query. This is…, Test intelligent query functions., Test intelligent querying with results., Test intelligent querying with fallback to text search., Test explaining filter query., Test building and validating smart filter., Test building smart filter when no filters generated. (+1 more)

### Community 85 - "Generic Table Tools (3)"
Cohesion: 0.22
Nodes (8): _inject_sort_order(), Inject a sort directive into the URL's sysparm_query if no ORDERBY is present.…, Test _inject_sort_order() helper., Test sort directive is appended to existing sysparm_query., Test URL is returned unchanged when ORDERBY already exists., Test sysparm_query is created when URL has no query param., Test sort is appended correctly to a multi-condition query., TestInjectSortOrder

### Community 86 - "oauth/ Package"
Cohesion: 0.32
Nodes (13): filter/ Package, http_layer/ Package, Intelligence–Builder Backref Discipline, oauth/ Package, Pooled HTTP Client (oauth/http_pool.py), Release 4.0.0 — Architectural Refactor, 4.1.0 Work — Shim Deletion (Not a Shipped Tag), GET Token-Optimization Invariants (+5 more)

### Community 87 - "Query Intelligence (4)"
Cohesion: 0.21
Nodes (7): Return (issue, suggestion) if the date filter is open-ended., Return (issues, suggestions) for the given filter dict., Test QueryExplainer functionality., Test detection of incomplete date range., Test that complete date range has no issue., Test analyzing filters with multiple issues., TestQueryExplainer

### Community 88 - "Utils.Py"
Cohesion: 0.21
Nodes (10): Natural-language to ServiceNow filter conversion. Pure NL parsing — does not…, Pydantic models and result containers for the filter pipeline., _extract_content_keywords(), extract_keywords(), _extract_record_numbers(), Extract relevant keywords from input text using lightweight regex patterns.…, Extract ServiceNow record numbers from text., Extract content keywords using basic text processing. (+2 more)

### Community 89 - "Http Layer Errors"
Cohesion: 0.23
Nodes (6): classify_read_failure(), Map a read-path exception onto the error vocabulary. ``TimeoutError`` covers…, ServiceNowOAuthClient raises ValueError('Missing OAuth configuration').…, anyio.fail_after raises the builtin TimeoutError, not an httpx one., Unreachable host is retryable, but it is not a deadline expiry., TestClassifyTransportFailures

### Community 90 - "Generic Tool Wrappers"
Cohesion: 0.26
Nodes (8): filter_records(), OptJsonList, Query a ServiceNow table with field-value filters. Supports suffix operators…, asyncio, Test filter_records generic tool., Verify vtb_task works through generic filter (ServiceNow API path)., sys_updated_on is a DETAIL_FIELDS entry for incident; filter_records must pass…, TestFilterRecords

### Community 91 - "Integration Tests"
Cohesion: 0.15
Nodes (7): End-to-end integration tests that exercise real product code paths. These tests…, Catch import-time errors and circular imports across the codebase., HTTPStatusError raised at the OAuth boundary surfaces as a domain error string., Tools.py is the MCP entrypoint — registration must stay coherent., TestErrorPropagationEndToEnd, TestModuleImports, TestToolRegistry

### Community 92 - "Query Intelligence (5)"
Cohesion: 0.21
Nodes (7): Handle exclusion filters with intelligent name-to-ID mapping., Test exclusion filter handling., Test exclusion of known entity LogicMonitor., Test exclusion of LogicMonitor Integration (with spaces)., Test exclusion of unknown entity., Test field mapping for exclusions., TestExclusionFilters

### Community 93 - "Query Intelligence (6)"
Cohesion: 0.21
Nodes (7): Merge two priority values with OR syntax., Test priority filter handling., Test merging same priority values., Test merging different priority values., Test merging into existing OR filter., Test that duplicate priorities are not added., TestPriorityFilters

### Community 94 - "Query Validation (4)"
Cohesion: 0.23
Nodes (6): True if the value already expresses an operator (so it is not a bare match)., Warn when a reference field is filtered by a bare display value. Reference…, validate_reference_field(), _value_carries_operator(), validate_reference_field flags bare reference-field display values., TestReferenceFieldValidation

### Community 95 - "Http Layer Url Builder"
Cohesion: 0.21
Nodes (10): HTTP layer for the ServiceNow REST API — v4.0 Sprint 3 split. The v3…, encode_query_string(), ensure_query_encoded(), URL construction for ServiceNow read requests. Owns the two read-path mutations…, Percent-encode an assembled encoded-query string for a URL. Idempotent: an…, Ensure ``sysparm_query`` value in URL is percent-encoded for ServiceNow.…, Re-encoding an already-encoded URL changes nothing. The property the old…, The premise of the refusal, asserted rather than assumed. Percent-encode ``^``… (+2 more)

### Community 96 - "Url"
Cohesion: 0.17
Nodes (11): author, name, description, display_name, long_description, manifest_version, name, repository (+3 more)

### Community 97 - "Kb Article Tools (2)"
Cohesion: 0.24
Nodes (6): _get_kb_article_sys_id(), Return the article's sys_id, or None if no such article exists. None means…, Re-read the draft sys_id between publish attempts, best effort. ServiceNow…, _refresh_draft_sys_id(), Decision (d): None means absent, so a failed read must NOT return None. The old…, TestGetKbArticleSysId

### Community 98 - "Generic Table Tools Tests (2)"
Cohesion: 0.17
Nodes (7): Test caller exclusion parsing., Test parsing known caller (logicmonitor)., Test parsing single sys_id., Test parsing comma-separated sys_ids., Test parsing already formatted exclusion., Test parsing empty input., TestCallerExclusions

### Community 99 - "Query Validation Tests"
Cohesion: 0.17
Nodes (7): Test edge cases and error handling scenarios., Test ServiceNowQueryBuilder handles None inputs gracefully., Test ServiceNowQueryBuilder handles empty lists gracefully., Test priority filter validation with empty string., Test debug_query_construction handles None inputs., Test pagination params with edge values., TestEdgeCasesAndErrorHandling

### Community 100 - "Query Validation (5)"
Cohesion: 0.20
Nodes (5): Build ServiceNow relative date filter with proper BETWEEN syntax., Test building relative date filter for last 7 days., Test building relative date filter with unknown period (fallback)., Test building relative date filter for last week., Test building relative date filter for today.

### Community 101 - "Filter Value Encoding"
Cohesion: 0.20
Nodes (7): Filter pipeline — ServiceNow query construction, validation, NL parsing,…, QueryValueError, Per-value encoding boundary for ServiceNow encoded queries (v4.4.1). One half…, A caller value cannot be carried by ServiceNow's encoded-query syntax. Raised…, The §3.1 failure shape. Consumers return this straight to the client., _truncate(), ValueError

### Community 102 - "Http Layer Errors (2)"
Cohesion: 0.24
Nodes (5): asyncio, Derived from the CODE, not from a list. The list was wrong once already. The…, The headline bug: a 30s deadline must never look like a missing record., Empty is success. Deciding it means not-found is the consumer's job., TestReadFailuresPropagate

### Community 103 - "Pyproject Sync"
Cohesion: 0.36
Nodes (10): _load_manifest(), _load_pyproject(), _main_version(), Packaging-consistency tests for the .mcpb bundle sources. These guard the…, _requirements_entries(), test_manifest_entry_point_exists(), test_manifest_env_mapping_covers_required_config(), test_requirements_mirrored_in_pyproject() (+2 more)

### Community 104 - "Run"
Cohesion: 0.20
Nodes (10): args, command, server, entry_point, mcp_config, type, --directory, ${__dirname} (+2 more)

### Community 105 - "Cmdb Citype Validation"
Cohesion: 0.29
Nodes (6): _ci_type_error(), Return an error message if ci_type is not a usable cmdb_ci* table, else None.…, parametrize, The old bare prefix check accepted this; the shape check does not., re.match with `$` accepts one trailing newline; fullmatch does not., TestCiTypePolicy

### Community 106 - "Vtb Task Tools (2)"
Cohesion: 0.20
Nodes (5): _get_task_sys_id(), Get the sys_id for a task by its number, or None if no such task exists. None…, Test successful sys_id retrieval., Test sys_id retrieval when task not found., Test sys_id retrieval with invalid response.

### Community 107 - "Generic Table Tools Tests (3)"
Cohesion: 0.20
Nodes (6): Test that a custom sort directive is respected., Test that sort is not injected when default_sort is empty., Test that an existing ORDERBY in the URL is not replaced., Test that _make_paginated_request injects sort order., Test that default sort order is injected into paginated requests., TestPaginationSortIntegration

### Community 108 - "Query Intelligence Tests"
Cohesion: 0.20
Nodes (6): Test edge cases and error conditions., Test handling of empty query., Test handling of whitespace-only query., Test handling when no keywords can be extracted., Test merging priority that already has complete syntax., TestEdgeCases

### Community 109 - "01-Architecture-Overview"
Cohesion: 0.22
Nodes (9): Architecture Overview Document, AuthMiddleware SSE Bearer, FastMCP Server Core, Stdout JSON-RPC Stderr Logs Invariant, tools.py Tool Registration, stdio and SSE Transport, SSE Auth Independent of ServiceNow OAuth, AuditMiddleware Structured Logging (+1 more)

### Community 110 - "Query Validation (6)"
Cohesion: 0.31
Nodes (5): Build OR filter for multiple priorities., Test the ServiceNowQueryBuilder class methods., Test building priority filter with single priority., Test building priority filter with empty list., TestServiceNowQueryBuilder

### Community 111 - "Filter Explainer"
Cohesion: 0.25
Nodes (6): explain_existing_filter(), Any, Explain what an existing filter does., Explain what an existing filter does and suggest improvements., Test basic filter explanation., Test explaining filter with issues.

### Community 112 - "Oauth Client"
Cohesion: 0.25
Nodes (5): Any, AsyncClient, Response, Make an authenticated request to ServiceNow API. Delegates to RequestExecutor;…, Test the OAuth connection by making a simple API call.

### Community 113 - "Cmdb Citype Validation (2)"
Cohesion: 0.31
Nodes (5): Search Configuration Items by multiple attributes. Args: name: CI name/hostname…, search_cis_by_attributes(), The headline bug: never query cmdb_ci when the caller named another table., Absent is not invalid — no ci_type means "search all CIs"., TestSearchCisByAttributes

### Community 114 - "Consolidated Tools"
Cohesion: 0.31
Nodes (4): _pick_canonical_kb_row(), De-duplicate kb_knowledge rows by `number`, keeping the highest-priority…, De-dup helper picks highest-priority workflow_state per number., TestPickCanonicalKbRow

### Community 115 - "Kb Article Tools (3)"
Cohesion: 0.31
Nodes (5): _get_kb_article_meta(), Fetch sys_id + short_description in one GET — avoids a second round-trip in…, The shape a failed GET now arrives in for this module (v4.4 Tier 0.3)., TestGetKbArticleMeta, _timeout()

### Community 116 - "Kb Article Tools (4)"
Cohesion: 0.31
Nodes (5): Return the published row for *article_number*, or None if not yet published.…, _verify_kb_published(), _verify_kb_published is the source of truth for publish success., None means "no Published row yet"; a failed read is not that. Conflating them…, TestVerifyKbPublished

### Community 117 - "Vtb Task Tools (3)"
Cohesion: 0.31
Nodes (5): Extract the inner result payload from a write response., _unwrap_write_response(), Test the response unwrapper helper., An empty write response cannot establish that the write landed., TestUnwrapWriteResponse

### Community 118 - "Oauth Client Enhanced Tests"
Cohesion: 0.25
Nodes (5): Test custom exception classes., Test that OAuth error inherits from Exception., Test that AuthenticationError inherits from OAuthError., Test that ConnectionError inherits from OAuthError., TestServiceNowOAuthExceptions

### Community 119 - "Query Intelligence (7)"
Cohesion: 0.25
Nodes (4): Calculate date contribution to size factor., Test date factor with no date filter., Test date factor for today only., Test date factor for last week.

### Community 120 - "Query Intelligence (8)"
Cohesion: 0.25
Nodes (4): Calculate priority contribution to size factor., Test priority factor with no priority filter., Test priority factor with P1., Test priority factor with OR (reduces selectivity).

### Community 121 - "Query Intelligence (9)"
Cohesion: 0.39
Nodes (4): Determine size category from factors., Test result size estimation., Test size category determination for small result set., TestResultSizeEstimation

### Community 122 - "Table Tools Generic Table Tools"
Cohesion: 0.25
Nodes (7): _iso_range_from_month_names(), _month_name_to_num(), _parse_year_at_end_format(), Resolve an English month name (full or 3+ letter abbrev) to its 1-12 number., Build an (ISO start, ISO end) date tuple from month-name components. Returns…, Parse 'Month DD to Month DD YYYY' format (year at end). Complexity: 3, Test parsing 'Month DD to Month DD YYYY' format.

### Community 123 - "Generic Table Tools (4)"
Cohesion: 0.25
Nodes (5): _parse_week_format(), Parse 'Week X YYYY' format. Complexity: 3, Test parsing invalid week format returns None., Test parsing valid week format., Test parsing 'week X of YYYY' format.

### Community 124 - "Filtering Tests"
Cohesion: 0.25
Nodes (5): Specific tests for ServiceNowQueryBuilder class., Test QueryBuilder initialization., Test OR filter building., Test NOT EQUALS filter building., TestServiceNowQueryBuilder

### Community 125 - "Generic Table Tools Tests (4)"
Cohesion: 0.25
Nodes (5): Test TableFilterParams model., Test creating params with filters., Test creating params with fields., Test creating empty params., TestTableFilterParams

### Community 126 - "Oauth Client (2)"
Cohesion: 0.39
Nodes (3): dict, patch, TestOAuthClientExtended

### Community 127 - "Query Intelligence Tests (2)"
Cohesion: 0.25
Nodes (5): Test exclusion pattern parsing., Test parsing 'exclude caller' patterns., Test parsing 'without caller' patterns., Test that queries without exclusions return None., TestExclusionPatternParsing

### Community 128 - "Query Value Encoding Tests"
Cohesion: 0.14
Nodes (8): An `int` arriving from the JSON boundary must still interpolate. MCP clients…, The message echoes the value; a 5000-character description must not fill it., Cross-module scan for the write-target class specifically. The handler scan…, Derived from the code, not from a list of handlers someone maintained. Same…, test_a_long_value_is_truncated_in_the_refusal_message(), test_a_non_string_value_passes_through_instead_of_raising(), test_every_terminal_condition_handler_escapes_its_value(), test_no_module_interpolates_a_record_number_unescaped()

### Community 129 - "Token Footprint Tests (2)"
Cohesion: 0.25
Nodes (5): Lock budget constants — accidental relaxation should fail review., Curated 7-field view must be at most ~15% over standard ESSENTIAL list., Performance preset has 11 fields vs essential's 6; budget reflects that., A sys_id lookup must never need more than ~200 tokens (1 row)., TestSLATokenBudgetConstants

### Community 130 - "Consolidated Tools (2)"
Cohesion: 0.38
Nodes (4): _get_error_message(), Get table-specific error message with cognitive complexity < 15., Test helper functions., TestHelperFunctions

### Community 131 - "Generic Tool Wrappers (2)"
Cohesion: 0.38
Nodes (4): Search records in a ServiceNow table by text similarity. Tokenises *query* into…, search_records(), Test search_records generic tool., TestSearchRecords

### Community 132 - "Mcp Tools Tests"
Cohesion: 0.29
Nodes (4): Test private task tools with CRUD operations., Test creating a new private task., Test updating an existing private task., TestPrivateTaskTools

### Community 133 - "Oauth Tests"
Cohesion: 0.33
Nodes (4): Test OAuth token handling and validation., Test validation of valid OAuth token format., Test token expiration logic., TestOAuthTokenHandling

### Community 134 - "Filter Builder"
Cohesion: 0.33
Nodes (4): ServiceNow query-string builder. Static helpers that emit syntactically-correct…, Helper class for building ServiceNow queries with proper syntax., ServiceNowQueryBuilder, Set up test fixtures.

### Community 135 - "Filter Builder (2)"
Cohesion: 0.33
Nodes (3): Build date range filter for ServiceNow using proper BETWEEN syntax., Test proper BETWEEN syntax generation., Test building date range filter with proper BETWEEN syntax.

### Community 136 - "Query Intelligence (10)"
Cohesion: 0.33
Nodes (3): Return (issue, suggestion) if the priority filter has comma syntax., Test detection of comma-separated priority issue., Test that correct priority filter has no issue.

### Community 137 - "Query Intelligence (11)"
Cohesion: 0.33
Nodes (3): Provide rough estimate of expected result size., Test size estimation for empty filters., Test size estimation with filters.

### Community 138 - "Type"
Cohesion: 0.33
Nodes (6): description, required, title, type, user_config, client_id

### Community 139 - "Type (2)"
Cohesion: 0.33
Nodes (6): description, required, sensitive, title, type, client_secret

### Community 140 - "Env"
Cohesion: 0.33
Nodes (6): MCP_TRANSPORT, SERVICENOW_AUTH_TYPE, SERVICENOW_CLIENT_ID, SERVICENOW_CLIENT_SECRET, SERVICENOW_INSTANCE, env

### Community 141 - "Cmdb"
Cohesion: 0.33
Nodes (6): keywords, cmdb, incident, itsm, knowledge-base, servicenow

### Community 142 - "Personal Mcp Servicenow Main"
Cohesion: 0.47
Nodes (5): main(), parse_args(), Parse command line arguments., Run interactive setup wizard., run_setup()

### Community 143 - "Generic Table Tools (5)"
Cohesion: 0.33
Nodes (4): _parse_between_format(), Parse 'between Month DD, YYYY and Month DD, YYYY' format. Complexity: 3, Test parsing 'between...and' format., Test parsing invalid between format.

### Community 144 - "Generic Table Tools (6)"
Cohesion: 0.33
Nodes (4): _parse_iso_date_range(), Parse 'YYYY-MM-DD to YYYY-MM-DD' format. Complexity: 2, Test parsing ISO date range., Test parsing invalid ISO format returns None.

### Community 145 - "Cli Tests"
Cohesion: 0.33
Nodes (5): Tests for CLI argument handling., --help should print usage and exit 0., --version should print version and exit 0., test_help_flag(), test_version_flag()

### Community 146 - "Query Value Encoding Tests (2)"
Cohesion: 0.33
Nodes (3): `^NQ` discards every condition before it, so a scoped query becomes a table…, Why the check runs before the handlers rather than inside the encoder.…, TestNewQueryResetRefusal

### Community 147 - "CMDB Tools (6)"
Cohesion: 0.50
Nodes (5): CMDB Probe Failure Semantics, Partial Read Keeps Rows, Read-Failure Contract (ServiceNowRequestError), Table_Tools/read_helpers.py, CMDB Tools (6)

### Community 149 - "Type (3)"
Cohesion: 0.40
Nodes (5): description, required, title, type, servicenow_instance

### Community 150 - "Table Tools Vtb Task Tools"
Cohesion: 0.40
Nodes (4): _handle_http_error(), HTTPStatusError, Handle HTTP errors consistently., parametrize

### Community 151 - "Conftest"
Cohesion: 0.40
Nodes (4): fixture, Shared pytest fixtures. The v4.2 connection-pooling refactor introduced a…, Drop the cached pooled client before and after each test., _reset_http_pool()

### Community 152 - "Bitbucket CI Pipeline"
Cohesion: 0.50
Nodes (4): Bitbucket CI Pipeline, pytest Coverage CI Step, SonarCloud Quality Scan, pytest Dev Test Stack

### Community 153 - "Filter Explainer (2)"
Cohesion: 0.50
Nodes (3): QueryExplainer, Filter explanation + result-size estimation. Wraps QueryIntelligence's…, Explains existing filters and suggests improvements.

### Community 154 - "Win32"
Cohesion: 0.50
Nodes (4): compatibility, platforms, darwin, win32

## Knowledge Gaps
- **84 isolated node(s):** `PayPal Sponsor Funding`, `MCPB Bundle Artifact`, `Architecture Overview Document`, `stdio and SSE Transport`, `OAuth Authentication Flow Document` (+79 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ServiceNowRequestError` connect `Constants and Error Codes` to `Generic Table Query Engine`, `OAuth Client Facade`, `OAuth Connection Tests`, `Auth and KB Test Tools`, `HTTP Layer Encoding Tests`, `Request Dispatcher Parser`, `Request Dispatcher Singleton`, `KB Article Write Tools`, `Similar Records Engine`, `KB Batch Publish Helpers`, `Publish Knowledge Tests`, `Request Executor 401 Retry`, `KB Duplicate Check`, `CMDB Search Helpers`, `CI Types and Failure Paths`, `Publish With Verify`, `Retire Knowledge Article`, `VTB Update Private Task`, `Typed Read Kb`, `Kb Article Tools`, `Vtb Task Tools`, `Http Layer Errors`, `Kb Article Tools (2)`, `Http Layer Errors (2)`, `Kb Article Tools (3)`, `Kb Article Tools (4)`, `Vtb Task Tools (3)`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Why does `QueryValidationResult` connect `Filter Validation Result` to `NL Intelligence Tests`, `Encoded Query Value Escape`, `SQL Equivalent Explainer`, `Filter Validator Analysis`, `Query Validation (2)`, `Priority Filter Validation`, `Query Intelligence Tests`, `Query Validation Helpers`, `Query Intelligence (3)`, `Query Validation (3)`, `Result Count Validation`, `Utils.Py`, `Query Validation (4)`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Why does `QueryIntelligence` connect `SQL Equivalent Explainer` to `Query Intelligence`, `Query Intelligence (2)`, `Consolidated Tools Suite`, `Query Intelligence (3)`, `Query Intelligence NL Parse`, `Query Explainer`, `Filter Validation Result`, `Utils.Py`, `Filter Explainer (2)`, `get record Tool Wrappers`, `Query Intelligence (5)`, `Query Intelligence (6)`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 50 inferred relationships involving `ServiceNowRequestError` (e.g. with `ServiceNowAuthenticationError` and `ServiceNowAuthorizationError`) actually correct?**
  _`ServiceNowRequestError` has 50 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `ServiceNowOAuthClient` (e.g. with `RequestExecutor` and `TokenStore`) actually correct?**
  _`ServiceNowOAuthClient` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 49 inferred relationships involving `ErrorCode` (e.g. with `ServiceNowAuthenticationError` and `ServiceNowAuthorizationError`) actually correct?**
  _`ErrorCode` has 49 INFERRED edges - model-reasoned connections that need verification._
- **What connects `PayPal Sponsor Funding`, `MCPB Bundle Artifact`, `Architecture Overview Document` to the rest of the system?**
  _84 weakly-connected nodes found - possible documentation gaps or missing edges._