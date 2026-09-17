# Graph Report - personal-mcp-servicenow  (2026-09-17)

## Corpus Check
- 99 files · ~98,268 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 5, .properties 1, .lock 1)

## Summary
- 2986 nodes · 5845 edges · 144 communities (136 shown, 8 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 298 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5b03d506`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- dict
- asyncio
- generic_table_tools.py
- TestQueryBuilding
- ServiceNowRequestError
- query_table_with_filters
- classify_read_failure
- config_loader.py
- TestDateRangeHelpers
- get_kb_articles_by_state
- test_consolidated_tools.py
- get_priority_incidents
- TestServiceNowAPI
- build_date_filter
- test_security_sanitization.py
- request_dispatcher.py
- test_tool_selection.py
- dict
- test_query_value_encoding.py
- test_tool_registry.py
- health_check
- asyncio
- .test_process_response
- QueryValidationResult
- param_coercion.py
- asyncio
- _Capture
- kb_article_tools.py
- validate_date_format
- get_record_details
- test_typed_read_kb_article_tools.py
- test_failure_shape_conforms
- TestServiceNowFiltering
- build_last_n_days_filter
- TestCMDBTools
- typing
- validate_and_correct_filters
- test_tool_response_contract.py
- RequestExecutor
- build_mcpb.py
- ErrorCode
- asyncio
- validate_priority_filter
- make_nws_request
- asyncio
- test_generic_table_tools.py
- validator.py
- TestUtilityFunctions
- TableSpec
- .test_ordinary_and_dot_walked_field_names_are_accepted
- Architecture Documentation Index (v4.3 Diagrams)
- OAuth 2.0 Client Credentials Flow
- validate_result_count
- _publish_with_verify
- asyncio
- asyncio
- Migration Guide v3 to v4
- get_ci_details
- normalize_date_to_full_format
- TestCreatePrivateTask
- .transport
- update_private_task
- TestServiceNowOAuthClientInit
- TestDateParsing
- check_kb_duplicates
- _has_operator_in_value
- publish_knowledge_articles
- run_tests.py
- .test_query_is_exactly_the_caller_conditions
- Personal MCP ServiceNow Project
- TestServiceNowQueryBuilder
- publish_knowledge_article
- _build_priority_result_message
- validate_date_range_filter
- asyncio
- _write_private_task
- get_records_by_priority
- 39 MCP Tools Inventory
- test_no_stdout_pollution.py
- _validate_regex_input
- generic_table_tools Query Engine
- Generic Tool Wrappers
- query_slas_custom
- test_query_validation.py
- MCPB Build Guide
- _inject_sort_order
- oauth/ Package
- test_date_utils.py
- extract_keywords
- TestDateFilterIntegration
- filter_records
- _normalize_publish_result
- .test_write_path_propagates_raise_for_status
- os
- TestTokenManagement
- TestEndToEndThroughTheRealDispatcher
- manifest.json
- retire_knowledge_article
- _parse_caller_exclusions
- TestEdgeCasesAndErrorHandling
- _is_complete_servicenow_filter
- TestCMDBToolsValidation
- TestReadFailuresPropagate
- test_pyproject_sync.py
- .test_read_only_hint_is_served
- _ci_type_error
- TestTaskSysIdRetrieval
- _make_paginated_request
- TestCMDBToolsIntegration
- FastMCP Server Core
- TestRetryWithFreshToken
- TestOAuthTokenHandling
- ServiceNowOAuthClient
- TestOAuthEnvironmentSetup
- .test_register_tools_rejects_blank_guidance_field
- test_kb_article_tools.py
- _get_kb_article_meta
- test_vtb_task_tools.py
- test_oauth_client_enhanced.py
- TestGoldenSetIntegrity
- TestSelectionBaseline
- TestFooterInjection
- .test_test_connection_failure
- TestModuleImports
- ServiceNowQueryBuilder
- TestTableFilterParams
- TestOAuthClientExtended
- TestGuidanceCoverage
- .test_get_basic_auth_header
- TestSLATokenBudgetConstants
- .test_make_authenticated_request_raises_on_non_401
- test_no_module_interpolates_a_record_number_unescaped
- TestPrivateTaskTools
- test_every_terminal_condition_handler_escapes_its_value
- test_encoding_a_value_is_idempotent_through_the_transport
- test_cli.py
- TestNewQueryResetRefusal
- consolidated_tools.py
- _reset_http_pool
- Bitbucket CI Pipeline
- tests/__init__.py
- TestUpdatePrivateTask
- PayPal Sponsor Funding
- personal-mcp-servicenow

## God Nodes (most connected - your core abstractions)
1. `ServiceNowOAuthClient` - 59 edges
2. `ServiceNowRequestError` - 54 edges
3. `ErrorCode` - 43 edges
4. `get_kb_articles_by_state()` - 42 edges
5. `_send()` - 42 edges
6. `query_table_with_filters()` - 36 edges
7. `make_nws_request()` - 36 edges
8. `error_response()` - 35 edges
9. `encode_query_value()` - 35 edges
10. `get_priority_incidents()` - 34 edges

## Surprising Connections (you probably didn't know these)
- `3. `get_priority_incidents` — dropped `**kwargs`` --references--> `get_priority_incidents()`  [INFERRED]
  MIGRATION_v4_to_v5.md → Table_Tools/consolidated_tools.py
- ``query_slas_by_status` presets` --references--> `query_slas_by_status()`  [INFERRED]
  Diagrams & Documentation/05-sla-architecture-flow.md → Table_Tools/consolidated_tools.py
- `Two sanctioned exceptions` --references--> `health_check()`  [INFERRED]
  MIGRATION_v4_to_v5.md → utility_tools.py
- `03 Tool Organization Diagram` --semantically_similar_to--> `39 MCP Tools Inventory`  [INFERRED] [semantically similar]
  Diagrams & Documentation/README.md → README.md
- `Client changes you will actually feel` --references--> `get_ci_details()`  [INFERRED]
  MIGRATION_v4_to_v5.md → Table_Tools/cmdb_tools.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **v4.0 Package Split (filter + http_layer + oauth)** — changelog_filter_package, changelog_http_layer_package, changelog_oauth_package, changelog_release_4_0_0 [EXTRACTED 1.00]
- **Encoded-Query Value Guard Layers (4.4.1)** — changelog_encode_query_value, changelog_caret_refusal, changelog_ampersand_escape, changelog_nq_refusal, changelog_structural_vs_terminal_handlers, changelog_encoded_query_value_boundary [EXTRACTED 1.00]
- **End-to-End Layered Request Path** — readme_fastmcp, readme_generic_table_tools, changelog_filter_package, changelog_http_layer_package, changelog_oauth_package, readme_servicenow_rest_api [EXTRACTED 1.00]
- **GET Read-Path Pipeline** — diagrams_documentation_01_architecture_overview_generic_table_tools, diagrams_documentation_01_architecture_overview_make_nws_request, diagrams_documentation_04_similarity_search_flow_url_builder, diagrams_documentation_04_similarity_search_flow_response_parser, diagrams_documentation_02_oauth_request_executor [EXTRACTED 1.00]
- **OAuth Authentication Stack** — diagrams_documentation_02_oauth_singleton, diagrams_documentation_02_oauth_client_facade, diagrams_documentation_02_oauth_token_store, diagrams_documentation_02_oauth_request_executor, diagrams_documentation_02_oauth_http_pool, diagrams_documentation_02_oauth_client_credentials [EXTRACTED 1.00]

## Communities (144 total, 8 thin omitted)

### Community 0 - "dict"
Cohesion: 0.11
Nodes (14): dict, Test access token request functionality., Test successful token request., Test token request with 401 authentication error., Test token request with 403 authorization error., Test token request with 500 server error., Test token request with connection error., Test token request with timeout error. (+6 more)

### Community 1 - "asyncio"
Cohesion: 0.14
Nodes (13): find_similar_records(), Generic function to find similar records based on a given record's description.…, _assert_plain_failure(), asyncio, `except Exception: return CONNECTION_ERROR` must not become a 4th dialect., A re-wrapper must not relabel a failure as an empty result set., A partial set filtered down to nothing must not answer "no matches". Two pages…, The complete-read case is untouched: empty stays not-found. (+5 more)

### Community 2 - "generic_table_tools.py"
Cohesion: 0.09
Nodes (28): The field a free-text search must target for *table_name*., text_search_field_for(), encode_query_value(), QueryValueError, Escape one caller-supplied value for use inside a ``sysparm_query``. Args:…, A caller value cannot be carried by ServiceNow's encoded-query syntax. Raised…, Build a refusal from a message template in ``constants``. Keeps the value echo…, The §3.1 failure shape. Consumers return this straight to the client. (+20 more)

### Community 3 - "TestQueryBuilding"
Cohesion: 0.05
Nodes (30): _build_priority_filter(), _build_query_condition(), _build_query_string(), _normalize_operator(), Helper function to build OR-based priority filter with cognitive complexity <…, Rewrite GlideRecord-only operators to their encoded-query equivalents.…, Build a single query condition based on field and value., Build the complete query string from filters. Raises: QueryValueError: a filter… (+22 more)

### Community 4 - "ServiceNowRequestError"
Cohesion: 0.11
Nodes (20): _from_decode(), _from_oauth_auth(), _from_oauth_connection(), _from_oauth_forbidden(), _from_status_error(), _from_timeout(), _from_transport(), Any (+12 more)

### Community 5 - "query_table_with_filters"
Cohesion: 0.08
Nodes (23): BaseModel, Generic filter parameters for table queries., TableFilterParams, query_table_with_filters(), Generic function to query table with custom filters and fields. Supports…, asyncio, Test async table operation functions., Test querying table by text with results. (+15 more)

### Community 6 - "classify_read_failure"
Cohesion: 0.10
Nodes (17): classify_read_failure(), Map a read-path exception onto the error vocabulary. ``TimeoutError`` covers…, HTTPStatusError, parametrize, Tests for the typed read-path failure surface (v4.4 Tier 0.3). Three contracts…, ServiceNowOAuthClient raises ValueError('Missing OAuth configuration').…, A token-endpoint failure means what the same failure on the table API means., Same semantic failure, two transports — one code. (+9 more)

### Community 7 - "config_loader.py"
Cohesion: 0.05
Nodes (47): argparse, ConfigError, get_config_dir(), get_config_file_path(), get_setup_instructions(), load_config(), load_config_from_env(), load_config_from_file() (+39 more)

### Community 8 - "TestDateRangeHelpers"
Cohesion: 0.09
Nodes (18): get_current_month_range(), get_last_n_days_range(), get_this_week_range(), Get start and end dates for the current calendar month. Returns: Tuple of…, Get start and end dates for the last N days (including today). Args: days:…, Get start (Monday) and end (Sunday) of the current week. Returns: Tuple of…, Test convenience date range functions., Test current month range calculation for January. (+10 more)

### Community 9 - "get_kb_articles_by_state"
Cohesion: 0.12
Nodes (19): get_kb_articles_by_state(), List kb_knowledge articles de-duplicated by article number. TABLES:…, asyncio, parametrize, Regression tests for the `get_kb_articles_by_state` dedup/truncation defects.…, `published` is rank 0, so membership and equality coincide there. This is why…, Defect 2: truncating the raw scan must never produce a wrong state., `max_results` shapes OUTPUT; the raw scan runs to its own ceiling. The live… (+11 more)

### Community 10 - "test_consolidated_tools.py"
Cohesion: 0.12
Nodes (12): _build_sla_status_filter(), _get_error_message(), _pick_canonical_kb_row(), De-duplicate kb_knowledge rows by `number`, keeping the highest-priority…, Get table-specific error message with cognitive complexity < 15., Translate an SLA status preset into a (filter_dict, fields) pair., Tests for consolidated_tools.py — priority incidents, knowledge-specific, and…, De-dup helper picks highest-priority workflow_state per number. (+4 more)

### Community 11 - "get_priority_incidents"
Cohesion: 0.11
Nodes (16): OptJsonDict, _build_metadata(), get_priority_incidents(), _merge_filters(), Any, Get incidents filtered by priority value, with an optional date window. TABLES:…, Validate a date parameter and return an error dict if invalid, or None if valid., Merge additional filters and the date window into one filter dict. (+8 more)

### Community 12 - "TestServiceNowAPI"
Cohesion: 0.05
Nodes (25): patch, Test extracting display values from non-dict input., Test that URLs without sysparm_query pass through unchanged., Test that spaces in query values are percent-encoded., Test that ServiceNow operators (=, ^, <, >, etc.) are preserved., Test that # in query is encoded to prevent URL fragment issues., Test that already-encoded URLs are not double-encoded., Test that other URL parameters are not affected by encoding. (+17 more)

### Community 13 - "build_date_filter"
Cohesion: 0.14
Nodes (12): build_date_filter(), Build ServiceNow date filter using simple >= and <= operators. This replaces…, Test date filter building., Test filter with both start and end dates., Test filter with only start date., Test filter with only end date., Test filter with no dates returns None., Test filter with both None returns None. (+4 more)

### Community 14 - "test_security_sanitization.py"
Cohesion: 0.09
Nodes (31): AuditMiddleware, Middleware, MiddlewareContext, Audit logging middleware for MCP tool calls. Emits one structured JSON log line…, _sanitize(), _summarize(), _user_from_headers(), AuthMiddleware (+23 more)

### Community 15 - "request_dispatcher.py"
Cohesion: 0.07
Nodes (34): Per-value encoding boundary for ServiceNow encoded queries (v4.4.1). One half…, hashlib, HTTP layer for the ServiceNow REST API — v4.0 Sprint 3 split. The v3…, _get_typed(), Any, Read/write request dispatcher for the ServiceNow REST API. This is the v4.0…, The GET pipeline, with failures raised as ``ServiceNowRequestError``. An empty…, Test OAuth connection and return status. (+26 more)

### Community 16 - "test_tool_selection.py"
Cohesion: 0.13
Nodes (22): _evaluate(), evaluation(), _plausible_paths(), _profiles(), fixture, parametrize, _rank(), Golden intent set — tool-selection baseline (v4.4 Tier 0.1). Measures whether… (+14 more)

### Community 17 - "dict"
Cohesion: 0.09
Nodes (17): dict, patch, Test OAuth client creation fails with missing environment variables., Test API client integration with OAuth., Test that get_auth_info correctly detects OAuth configuration., Test get_auth_info when OAuth credentials are not available., Test OAuth token retrieval with mocked client., Test OAuth error handling scenarios. (+9 more)

### Community 18 - "test_query_value_encoding.py"
Cohesion: 0.06
Nodes (52): _bounded(), _probe_ci_table(), Fetch a CI by number from one table; return the first row, or None if absent.…, _get_task_sys_id(), Get the sys_id for a task by its number, or None if no such task exists. None…, _query_via_generic(), v4.4.1 — the encoded-query value boundary, asserted against what ServiceNow…, No encoding can carry it: ServiceNow splits on the DECODED value. (+44 more)

### Community 19 - "test_tool_registry.py"
Cohesion: 0.23
Nodes (12): inspect, re, Tool-guidance registry + docstring-footer injection (v5.0 "Boron" Tier 3.3).…, apply_guidance(), guidance_footer(), Tool selection guidance — structured, injected into docstrings (v5.0 Tier 3.3).…, The selection guidance for one tool. All four fields are required. `read_only`…, The canonical three-line guidance block generated from a tool's guidance. (+4 more)

### Community 20 - "health_check"
Cohesion: 0.07
Nodes (24): get_auth_info(), Get information about current authentication method., patch, Test the consolidated diagnostic tool (v5.0: 5 auth tools -> health_check)., A reachable instance reports connection ok., probe_table returns sample field names., TestHealthCheckTool, asyncio (+16 more)

### Community 21 - "asyncio"
Cohesion: 0.13
Nodes (9): query_slas_by_status(), Query SLA records by a named status preset. TABLES: task_sla only. SIDE EFFECT:…, asyncio, `truncated` is about the OUTPUT cap; a capped raw scan is a separate flag.…, Test SLA tool functions., v4.0 fix: routes via sys_id={sys_id}, not the broken number={sys_id}., Token-budget invariant: 'critical' returns 7-field curated view, not full row., TestGetKbArticlesByState (+1 more)

### Community 22 - ".test_process_response"
Cohesion: 0.50
Nodes (3): Test response processing., Test processing successful response., TestProcessResponse

### Community 23 - "QueryValidationResult"
Cohesion: 0.11
Nodes (13): QueryValidationResult, Container for query validation results., Add a warning message., Add a suggestion for improvement., True if the query is invalid or has warnings., Test the QueryValidationResult class., Test initializing valid QueryValidationResult., Test initializing invalid QueryValidationResult. (+5 more)

### Community 24 - "param_coercion.py"
Cohesion: 0.05
Nodes (16): coerce_json_dict(), coerce_json_list(), Any, Param-boundary JSON coercion for MCP tool signatures. LLM-driven MCP clients…, Peel repeated JSON-string layers (handles single- AND double-encoded input).…, Coerce a (possibly double-encoded) stringified JSON array to a native list., Coerce a (possibly double-encoded) stringified JSON object to a native dict., _unwrap_json_str() (+8 more)

### Community 25 - "asyncio"
Cohesion: 0.09
Nodes (17): _assert_plain_failure(), asyncio, parametrize, `[]` must mean "checked, clear" and nothing else., A '^' in the title splits the encoded query, silently widening it. Encoding…, v4.4.1: '&' was a transport defect, not an unrepresentable value. The encoder…, The quiet one, fixed: '%XY' used to be decoded on its way out. v4.4.0 searched…, No false positives: an ordinary "50% off" title is checked, not refused. (+9 more)

### Community 26 - "_Capture"
Cohesion: 0.13
Nodes (14): _Capture, asyncio, parametrize, A free-text search on task_sla must dot-walk task.short_description. task_sla…, A bare short_description condition is the silently-dropped filter., query_table_by_text resolves the search field from the table. The bug once…, A caller that forgets search_field must still get a valid query., The caller's conditions from a captured URL, sort clause removed. Splitting the… (+6 more)

### Community 27 - "kb_article_tools.py"
Cohesion: 0.14
Nodes (21): anyio, filter, http_layer, structlog, _dedup_query_defect(), Knowledge-article reads and writes. Read-failure contract (v4.4 Tier 0.3). A…, Why the dedup query would not faithfully carry *short_description*, if so.…, The minimal tool response contract (v5.0 "Boron", plan §3.1). The target shapes… (+13 more)

### Community 28 - "validate_date_format"
Cohesion: 0.10
Nodes (16): Validate date format is either "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS". Args:…, validate_date_format(), Test date format validation., Test valid YYYY-MM-DD format., Test valid YYYY-MM-DD HH:MM:SS format., Test valid midnight time., Test valid end of day time., Test invalid MM-DD-YYYY format. (+8 more)

### Community 29 - "get_record_details"
Cohesion: 0.08
Nodes (21): get_record_description(), get_record_details(), _is_safe_record_number(), Reject record numbers that carry query operators/whitespace instead of a plain…, Internal: fetch a record's short_description, in the §3.1 single-record shape.…, Get one record's DETAIL_FIELDS, in the single-record contract shape. Returns…, Single-record read shape (§3.1): {"record": row|None}. A successful read with…, _record_envelope() (+13 more)

### Community 30 - "test_typed_read_kb_article_tools.py"
Cohesion: 0.20
Nodes (9): KbDuplicateCheckInconclusive, _outcome_error_message(), BaseException, Exception, Message for an exception that escaped a per-article coroutine., The duplicate check could not produce a trustworthy answer. Distinct from "no…, Typed read failures in the KB article tools (v4.4 Tier 0.3, PR C). A failed GET…, Per-exception-type messages for anything that escapes a batch coroutine. Both… (+1 more)

### Community 31 - "test_failure_shape_conforms"
Cohesion: 0.11
Nodes (18): assert_contract(), _assert_error_shape(), _FakeOAuthClient, _invoke(), asyncio, fixture, parametrize, Patch the dispatcher's read + write seams. `mode` picks success/failure. (+10 more)

### Community 32 - "TestServiceNowFiltering"
Cohesion: 0.07
Nodes (18): _encode_query_string(), URL encode query string while preserving ServiceNow JavaScript functions and…, patch, Test multiple caller exclusions by sys_id., Test that URL encoding preserves JavaScript functions., Test ServiceNowQueryBuilder query validation., Test TableFilterParams object creation and validation., Test combined filtering with mocked API call. (+10 more)

### Community 33 - "build_last_n_days_filter"
Cohesion: 0.16
Nodes (11): _sla_filter_breached(), _sla_filter_performance(), build_last_n_days_filter(), Build ServiceNow filter for records from the last N days. This replaces the…, Test build_last_n_days_filter helper function., Test filter uses sys_created_on by default., Test filter with custom date field., Test filter for last 1 day. (+3 more)

### Community 34 - "TestCMDBTools"
Cohesion: 0.08
Nodes (14): Test finding CIs with invalid type., Test searching CIs by name attribute., Test searching CIs by IP address attribute., Test searching CIs by multiple attributes., Test successful CI details retrieval., Test suite for CMDB tools functionality., Test CI details retrieval for non-existent CI., Test finding similar CIs for a given CI. (+6 more)

### Community 35 - "typing"
Cohesion: 0.11
Nodes (22): asyncio, atexit, Constants used throughout the ServiceNow MCP server., dotenv, httpx, json, ServiceNowOAuthClient — orchestrator façade. Composes ``TokenStore`` +…, _close_pool_atexit() (+14 more)

### Community 36 - "validate_and_correct_filters"
Cohesion: 0.33
Nodes (6): _correct_date(), _correct_priority(), Return (corrected_value, suggestion_or_None) for a priority field., Return (corrected_value, suggestion_or_None) for a sys_created_on field., Validate filters and auto-correct common syntax issues. Returns a result with…, validate_and_correct_filters()

### Community 37 - "test_tool_response_contract.py"
Cohesion: 0.08
Nodes (27): `get_sla_details` bug fix, v3 → v4 mapping (for older clients), fastmcp, 1. Removed tools and their replacements, Client changes you will actually feel, get_sla_details(), query_slas_by_task(), Get one SLA record by its sys_id (task_sla lookup). TABLES: task_sla only. SIDE… (+19 more)

### Community 38 - "RequestExecutor"
Cohesion: 0.11
Nodes (16): AuthHeaderSource, Any, AsyncClient, Response, Drop the cached token, re-authenticate, retry once., Make authenticated HTTP requests with token-refresh on 401., Make an authenticated request to ServiceNow API. When…, Decode a successful response payload. (+8 more)

### Community 39 - "build_mcpb.py"
Cohesion: 0.14
Nodes (23): assert_no_leaks(), assert_versions_aligned(), clean_staging(), copy_package_dirs(), copy_root_files(), fail(), main(), Path (+15 more)

### Community 40 - "ErrorCode"
Cohesion: 0.13
Nodes (17): ErrorCode, The complete failure vocabulary. Adding a code is a contract change., _partial_envelope(), PartialPageReadError, Exception, query_table_by_text(), Generic function to query any ServiceNow table by text similarity. Builds ONE…, A page after the first failed; the rows already collected are attached.… (+9 more)

### Community 41 - "asyncio"
Cohesion: 0.13
Nodes (11): _check_kb_duplicates(), _get_kb_article_sys_id(), Return the article's sys_id, or None if no such article exists. None means…, Update fields on a knowledge article by article number (e.g. KB0001234).…, update_knowledge_article(), asyncio, Decision (d): None means absent, so a failed read must NOT return None. The old…, The headline fix: [] means "checked, clear" and nothing else. The old test… (+3 more)

### Community 42 - "validate_priority_filter"
Cohesion: 0.11
Nodes (16): _has_comma_syntax_issue(), _has_or_format_issue(), Check if priority filter has comma syntax issue., Check if OR syntax is missing priority= prefix., Check if numeric format suggestion should be added., Validate priority filter syntax with enhanced debugging., _should_suggest_numeric_format(), validate_priority_filter() (+8 more)

### Community 43 - "make_nws_request"
Cohesion: 0.13
Nodes (19): make_nws_request(), Make a request to the ServiceNow API using OAuth 2.0 authentication. For GET…, _build_similar_ci_response(), _extract_ci_search_attributes(), _filter_and_limit_ci_results(), Any, quick_ci_search(), ServiceNow CMDB (Configuration Management Database) Tools Provides CI… (+11 more)

### Community 44 - "asyncio"
Cohesion: 0.07
Nodes (27): get_all_ci_types(), Find Configuration Items similar to a given CI, by shared attributes. TABLES:…, Get all available CI types/classes in the CMDB. TABLES: sys_db_object (live…, similar_cis_for_ci(), _assert_empty_list(), _assert_internal(), _assert_plain_failure(), _by_table() (+19 more)

### Community 45 - "test_generic_table_tools.py"
Cohesion: 0.07
Nodes (26): _clean_priority_input(), _format_single_priority(), _handle_priority_condition(), _normalize_priority_value(), _parse_priority_list(), _process_comma_separated_priorities(), Convert P-notation to number (e.g., 'P1' -> '1', '2' -> '2')., Clean brackets, quotes from priority input. (+18 more)

### Community 46 - "validator.py"
Cohesion: 0.07
Nodes (34): Filter pipeline — ServiceNow query construction, validation, value escaping.…, Pydantic models and result containers for the filter pipeline., _analyze_caller_exclusion(), _analyze_date_filtering(), _analyze_javascript_functions(), _analyze_original_filters(), _analyze_priority_filtering(), _analyze_url_encoding() (+26 more)

### Community 47 - "TestUtilityFunctions"
Cohesion: 0.13
Nodes (11): Provide suggestions for query improvements., suggest_query_improvements(), Test utility and helper functions., Test cross verification function structure., Test building pagination parameters with defaults., Test building pagination parameters with custom values., Test suggestions for zero results., Test suggestions for low priority query results. (+3 more)

### Community 48 - "TableSpec"
Cohesion: 0.05
Nodes (24): dataclasses, 2. Response contract — every tool, 3. `get_priority_incidents` — dropped `**kwargs`, 4. Nothing else changed for callers, Migration Guide: v4.x → v5.0 "Boron", Two sanctioned exceptions, One spec per supported table — the single source of truth (v5.0 "Boron" Tier…, Everything the server needs to know about one ServiceNow table. `number_field`… (+16 more)

### Community 49 - ".test_ordinary_and_dot_walked_field_names_are_accepted"
Cohesion: 0.33
Nodes (4): Dot-walking is how `task_sla` is queried at all — it must survive., The second assembly path has to repeat the check, not inherit it., A filters dict's KEYS come from the caller and nothing validated them.…, TestFieldNamesAreCallerSuppliedToo

### Community 50 - "Architecture Documentation Index (v4.3 Diagrams)"
Cohesion: 0.11
Nodes (22): Claude Desktop Extension (.mcpb) Packaging, OR-Combined LIKE Text Query, Release 4.3.0 — mcpb Packaging and Performance, SSE Transport Authentication, 05 AI Intelligence Flow Diagram, 01 Architecture Overview Diagram, Architecture Documentation Index (v4.3 Diagrams), Distribution via .mcpb or Docker SSE (+14 more)

### Community 51 - "OAuth 2.0 Client Credentials Flow"
Cohesion: 0.18
Nodes (14): OAuth Authentication Flow Document, OAuth 2.0 Client Credentials Flow, ServiceNowOAuthClient Facade, oauth/http_pool Shared Client, RequestExecutor 401 Retry, oauth/singleton Process-Wide Client, TOKEN_REFRESH_BUFFER_MINUTES, TokenStore Cache and Refresh (+6 more)

### Community 52 - "validate_result_count"
Cohesion: 0.14
Nodes (13): _is_high_priority_query(), Check if query is for high-priority (P1/P2) records., Validate incident result count against expected baselines., Validate if result count seems reasonable for the query., _validate_incident_result_count(), validate_result_count(), Test result count validation functionality., Test validation passes for normal incident count. (+5 more)

### Community 53 - "_publish_with_verify"
Cohesion: 0.09
Nodes (20): _call_kb_publish_workflow(), _fire_publish(), _publish_failure(), _publish_unconfirmed(), _publish_with_verify(), Any, Fire the publish workflow. Returns None on success, or a fire-time failure. A…, Fire the publish workflow then verify by polling for a Published row. Treats… (+12 more)

### Community 54 - "asyncio"
Cohesion: 0.08
Nodes (31): assert_no_smuggled_parameter(), What ServiceNow's condition parser actually receives, modelled for tests.…, The parameters ServiceNow's servlet layer would see, percent-decoded., The decoded ``sysparm_query`` split into conditions on ``^``., The one condition beginning with *prefix*, with the prefix stripped. Raises if…, No URL parameter appeared that the caller did not ask for. The signature of the…, servicenow_conditions(), servicenow_params() (+23 more)

### Community 55 - "asyncio"
Cohesion: 0.17
Nodes (15): _count_tokens(), _list_envelope_overhead(), asyncio, parametrize, Patch query_table_with_filters to return `response`, then call the tool., Per-tool token budgets — must not regress structurally., v3 bug returned 10K rows; v4 must return 1., Critical preset budget is tight because the field list is curated. (+7 more)

### Community 56 - "Migration Guide v3 to v4"
Cohesion: 0.25
Nodes (7): Tool Organization Document, v3 Generic Wrapper Consolidation, Migration Guide v3 to v4, v3→v4 SLA Tool Name Mapping, v4.1 Test Patch Target Migration, HTTP Token-Budget Invariants Tests, tiktoken Token Footprint Tests

### Community 57 - "get_ci_details"
Cohesion: 0.10
Nodes (24): find_cis_by_type(), get_ci_details(), Search Configuration Items by multiple attributes. TABLES: cmdb_ci (or a given…, Get comprehensive details for a specific Configuration Item by number. TABLES:…, Find all Configuration Items of a specific type/class. TABLES: any cmdb_ci*…, search_cis_by_attributes(), _Capture, asyncio (+16 more)

### Community 58 - "normalize_date_to_full_format"
Cohesion: 0.19
Nodes (9): normalize_date_to_full_format(), Normalize date string to full format with time component. Args: date_string:…, Test date normalization., Test normalizing simple date for start (adds 00:00:00)., Test normalizing simple date for end (adds 23:59:59)., Test full datetime is unchanged for start., Test full datetime is unchanged for end., Test midnight datetime is preserved. (+1 more)

### Community 59 - "TestCreatePrivateTask"
Cohesion: 0.25
Nodes (5): Test create_private_task function with OAuth authentication., Test successful private task creation., Test task creation fails without short_description., Test task creation with all optional fields., TestCreatePrivateTask

### Community 60 - ".transport"
Cohesion: 0.11
Nodes (11): _no_sleep(), fixture, The retry path is for a verify that positively says "not published yet"., The refresh between attempts is best effort, not a reason to abort., A failed read reaches the publish guard through the real dispatcher. These…, Fake the transport under the real dispatcher; record every write., GET handler: meta resolves, the dedup query does whatever `dedup` says., TestEndToEndThroughTheRealDispatcher (+3 more)

### Community 61 - "update_private_task"
Cohesion: 0.21
Nodes (9): Update / change an EXISTING private task (vtb_task), addressed by number.…, update_private_task(), _assert_plain_failure(), asyncio, Typed read failures in the private-task tools (v4.4 Tier 0.3, PR D). The module…, Decision (b): absent is still absent, and the message is unchanged., A rejected field must not cost a round trip., TestPreWriteLookup (+1 more)

### Community 62 - "TestServiceNowOAuthClientInit"
Cohesion: 0.20
Nodes (6): Test OAuth client initialization., Test initialization with valid configuration., Test initialization fails when SERVICENOW_INSTANCE is missing., Test initialization fails when CLIENT_ID is missing., Test initialization fails when CLIENT_SECRET is missing., TestServiceNowOAuthClientInit

### Community 63 - "TestDateParsing"
Cohesion: 0.04
Nodes (44): _iso_range_from_month_names(), _month_name_to_num(), _parse_between_format(), _parse_cross_month_range(), _parse_date_range_from_text(), _parse_iso_date_range(), _parse_month_range_format(), _parse_week_format() (+36 more)

### Community 64 - "check_kb_duplicates"
Cohesion: 0.12
Nodes (12): check_kb_duplicates(), _bounded(), _check_single_kb_duplicate(), _duplicate_row_inconclusive(), Return KB articles matching short_description exactly across live workflow…, A row for an article whose duplicate status could not be determined.…, Lookup meta then check duplicates for one article. Used by check_kb_duplicates…, Check for duplicate KB articles without publishing. TABLES: kb_knowledge only.… (+4 more)

### Community 65 - "_has_operator_in_value"
Cohesion: 0.09
Nodes (13): _handle_bare_or_value_condition(), _has_operator_in_value(), Check if value already contains a comparison operator or ServiceNow text…, Handle values with ^OR where the first segment is a bare value (missing field…, Test detecting operators in value., Test detecting ServiceNow text/date operators at start of value., Test non-operator values., Newly recognized encoded-query operators are detected. (+5 more)

### Community 66 - "publish_knowledge_articles"
Cohesion: 0.13
Nodes (11): JsonList, publish_knowledge_articles(), _bounded(), Zip gathered outcomes back onto their article numbers, exceptions included.…, Publish MULTIPLE KB articles in one tool call (batch). TABLES: kb_knowledge…, _rows_from_outcomes(), Verify Semaphore prevents more than `concurrency` in-flight publishes., TestPublishKnowledgeArticles (+3 more)

### Community 67 - "run_tests.py"
Cohesion: 0.17
Nodes (18): pathlib, check_test_environment(), main(), Show coverage results if available., Main test runner function., Run a command and return success status., Test runner script for ServiceNow MCP unittest suite. This script runs all…, Run all tests with coverage reporting and JUnit XML output. (+10 more)

### Community 68 - ".test_query_is_exactly_the_caller_conditions"
Cohesion: 0.12
Nodes (12): asyncio, parametrize, The decoded sysparm_query value from a captured request URL., The outbound query equals the caller's conditions — nothing appended. Domain…, Nothing is dropped after the response comes back. The URL assertions above…, create_private_task → make_nws_request(method=POST) → oauth_client…, HTTPStatusError at the OAuth boundary surfaces as an {"error": {code, message}}…, search_records → query_table_by_text → make_nws_request → make_oauth_request. (+4 more)

### Community 69 - "Personal MCP ServiceNow Project"
Cohesion: 0.13
Nodes (16): Ampersand (&) Value Escape, Caret (^) Value Refusal, Domain Filtering Removal, encode_query_value / filter/value_encoding.py, Encoded-Query Value Boundary Contract, _has_operator_in_value Equals Limitation, KB Publish Fail-Closed Duplicate Check, Keep a Changelog Format (+8 more)

### Community 70 - "TestServiceNowQueryBuilder"
Cohesion: 0.07
Nodes (21): Build OR filter for multiple priorities., Build ServiceNow relative date filter with proper BETWEEN syntax., Build a complete ServiceNow filter string with proper syntax. Args: priorities:…, Test relative date filtering using ServiceNowQueryBuilder., Test building relative date filter for this week., Test building relative date filter for last 7 days., Test building relative date filter with unknown period (fallback)., Test building complete filter with priorities only. (+13 more)

### Community 71 - "publish_knowledge_article"
Cohesion: 0.16
Nodes (9): _duplicate_check_inconclusive(), publish_knowledge_article(), Publish ONE knowledge article via the ServiceNow workflow endpoint. TABLES:…, Refuse the publish because the duplicate check could not answer. Same `success:…, TestPublishKnowledgeArticle, The guard must not have become so strict that nothing can publish., A publish requires a duplicate check that positively came back clear., The headline bug. A timeout in the guard must not become permission. (+1 more)

### Community 72 - "_build_priority_result_message"
Cohesion: 0.36
Nodes (4): _build_priority_result_message(), Build human-readable result message for priority queries., Test the result message builder., TestBuildPriorityResultMessage

### Community 73 - "validate_date_range_filter"
Cohesion: 0.19
Nodes (9): Validate date range filter completeness and format., validate_date_range_filter(), Test date range filter validation functionality., Test validating proper BETWEEN syntax., Test validation warns about old comparison syntax., Test validation warns about BETWEEN without JavaScript functions., Test validation warns about missing @ separator., Test validation provides suggestion for Week 35 2025. (+1 more)

### Community 74 - "asyncio"
Cohesion: 0.15
Nodes (10): asyncio, Test making authenticated API requests., Test successful authenticated request., Test authenticated request with 401 and successful retry., Test authenticated request with non-401 HTTP error., Test authenticated request with connection error., Test authenticated request with timeout., Test authenticated request with JSON decode error. (+2 more)

### Community 75 - "_write_private_task"
Cohesion: 0.29
Nodes (7): Send a write request through make_nws_request, mapping errors locally., _write_private_task(), _make_http_status_error(), asyncio, HTTPStatusError, Test the unified write helper that wraps make_nws_request., TestWritePrivateTask

### Community 76 - "get_records_by_priority"
Cohesion: 0.09
Nodes (19): _exclude_original_record(), _first_short_description(), _format_priority_results(), get_records_by_priority(), Any, Format paginated results into the list-contract shape. Empty is success., Generic function to get records by priority for any table that supports…, List-contract response for a text search. No rows is success (empty list),… (+11 more)

### Community 77 - "39 MCP Tools Inventory"
Cohesion: 0.15
Nodes (15): CMDB Probe Failure Semantics, get_sla_details v3 Bug Fix, SLA Tool Consolidation (Sprint 2), 06 SLA Architecture Flow Diagram, CMDB Tools Module, KB Article Write Tools, make_nws_request Dispatcher, VTB Private Task CRUD Tools (+7 more)

### Community 78 - "test_no_stdout_pollution.py"
Cohesion: 0.17
Nodes (15): ast, expr, _find_offending_prints(), _is_stderr_target(), _iter_runtime_modules(), Path, Lint guard: server runtime code must never print to stdout. MCP stdio transport…, Self-check: the AST scanner must NOT flag stderr-routed prints. (+7 more)

### Community 79 - "_validate_regex_input"
Cohesion: 0.17
Nodes (10): Pre-validate input to prevent ReDoS attacks., _validate_regex_input(), Test ReDoS (Regular Expression Denial of Service) protection., Test validation accepts valid strings., Test validation rejects non-strings., Test validation rejects overly long strings., Test validation rejects strings with too many spaces., Test validation rejects strings with too many dashes. (+2 more)

### Community 80 - "generic_table_tools Query Engine"
Cohesion: 0.17
Nodes (12): filter Intelligence-Builder Backref Discipline, consolidated_tools Module, filter/ Package Pipeline, generic_table_tools Query Engine, Intelligent Query Tools, filter_records Tool, pydantic Validation Dependency, ServiceNow Query Syntax Guide (+4 more)

### Community 81 - "Generic Tool Wrappers"
Cohesion: 0.14
Nodes (14): Generic Tool Wrappers, TABLE_CONFIGS Supported Tables, Table Extensibility via TABLE_CONFIGS, find_similar Tool, search_records Tool, Search and Query Flow Document, Paginated Request with ORDERBYDESC, query_table_by_text Engine (+6 more)

### Community 82 - "query_slas_custom"
Cohesion: 0.12
Nodes (16): Architecture diagram, Business scenarios (call patterns), Daily operations, Design goals, Fully custom, Incident-linked, Operational flows (v5 tool names), `query_slas_by_status` presets (+8 more)

### Community 83 - "test_query_validation.py"
Cohesion: 0.10
Nodes (16): Main filter validation function using dedicated helpers., True if the value already expresses an operator (so it is not a bare match)., Warn when a reference field is filtered by a bare display value. Reference…, validate_query_filters(), validate_reference_field(), _value_carries_operator(), Comprehensive tests for the filter/ package (was query_validation.py before…, Test the main validate_query_filters function. (+8 more)

### Community 84 - "MCPB Build Guide"
Cohesion: 0.33
Nodes (6): MCPB Build Guide, MCPB Staging Whitelist Packaging, MCPB server.type uv Runtime, Three-Way Version Sync, GitHub Actions MCPB Release Workflow, MCPB Bundle Artifact

### Community 85 - "_inject_sort_order"
Cohesion: 0.17
Nodes (10): _inject_sort_order(), Inject a sort directive into the URL's sysparm_query if no ORDERBY is present.…, Test _inject_sort_order() helper., Test sort directive is appended to existing sysparm_query., Test URL is returned unchanged when ORDERBY already exists., Test sysparm_query is created when URL has no query param., Test sysparm_query is created when URL has no params at all., Test sort is appended correctly to a multi-condition query. (+2 more)

### Community 86 - "oauth/ Package"
Cohesion: 0.32
Nodes (13): filter/ Package, http_layer/ Package, Intelligence–Builder Backref Discipline, oauth/ Package, Pooled HTTP Client (oauth/http_pool.py), Release 4.0.0 — Architectural Refactor, 4.1.0 Work — Shim Deletion (Not a Shipped Tag), GET Token-Optimization Invariants (+5 more)

### Community 87 - "test_date_utils.py"
Cohesion: 0.18
Nodes (9): logging, get_today_range(), get_yesterday_range(), Date utilities for ServiceNow MCP incident queries. Provides date validation,…, Get start and end of today (same date for both). Returns: Tuple of (start_date,…, Get start and end of yesterday (same date for both). Returns: Tuple of…, Tests for date utilities module. Tests date validation, normalization, and date…, Test yesterday range returns previous day for both. (+1 more)

### Community 88 - "extract_keywords"
Cohesion: 0.16
Nodes (12): `query_table_by_text` is safe by accident, so the accident is pinned.…, Pins the mechanism, not just today's outputs. A test that only checks sample…, Covers the record-number branch too, which has its own patterns.…, TestTextSearchTokenizerImmunity, _extract_content_keywords(), extract_keywords(), _extract_record_numbers(), Extract relevant keywords from input text using lightweight regex patterns.… (+4 more)

### Community 89 - "TestDateFilterIntegration"
Cohesion: 0.33
Nodes (4): Integration tests for date filter building with validation., Test complete workflow: validate -> normalize -> build filter., Verify filter doesn't use JavaScript syntax., TestDateFilterIntegration

### Community 90 - "filter_records"
Cohesion: 0.06
Nodes (37): pytest, filter_records(), find_similar(), get_record(), Any, OptJsonList, Generic MCP tool wrappers that replace 24 table-specific 1-line functions. Each…, Find records similar to an existing record (by short_description). TABLES:… (+29 more)

### Community 91 - "_normalize_publish_result"
Cohesion: 0.22
Nodes (5): _normalize_publish_result(), Normalize publish_knowledge_article output into a flat batch-result row. Four…, TestNormalizePublishResult, `published` is the fall-through, so every other shape must be caught first., TestNormalizePublishResultNeverInventsSuccess

### Community 92 - ".test_write_path_propagates_raise_for_status"
Cohesion: 0.18
Nodes (8): asyncio, GET path: encoding + perf params + display flattening all apply., Critical negative tests — write path MUST NOT touch read-path mutations. Per…, Write responses have a single-record shape; flattening would corrupt them.…, Write must pass ``raise_for_status=True`` so callers map status codes., TestMakeNwsRequestReadPath, TestMakeNwsRequestWritePath, fake_authenticated()

### Community 93 - "os"
Cohesion: 0.29
Nodes (7): os, sys, unittest version of CMDB CI Discovery & Search tools tests. Converted from…, unittest version of OAuth 2.0 implementation tests. Converted from…, unittest version of ServiceNow API tests. Tests the service_now_api_oauth.py…, unittest version of Utility Tools tests. v5.0 "Boron" (Tier 2): the five…, unittest

### Community 94 - "TestTokenManagement"
Cohesion: 0.17
Nodes (7): Test token caching and refresh functionality., Test getting token when none exists., Test using cached token when still valid., Test refreshing token when expired., Test getting authorization headers., Test clearing token cache., TestTokenManagement

### Community 95 - "TestEndToEndThroughTheRealDispatcher"
Cohesion: 0.24
Nodes (4): fixture, A failed lookup reaches `update_private_task` through the real dispatcher.…, TestEndToEndThroughTheRealDispatcher, install()

### Community 96 - "manifest.json"
Cohesion: 0.05
Nodes (43): author, name, description, required, title, type, description, required (+35 more)

### Community 97 - "retire_knowledge_article"
Cohesion: 0.20
Nodes (6): _call_kb_workflow(), Retire a knowledge article via the ServiceNow workflow endpoint. TABLES:…, retire_knowledge_article(), Verify write ops use make_nws_request write path (not GET path)., TestRetireKnowledgeArticle, TestRoutesThroughUnifiedPipeline

### Community 98 - "_parse_caller_exclusions"
Cohesion: 0.14
Nodes (12): _handle_caller_exclusion_condition(), _parse_caller_exclusions(), Parse caller exclusion list and convert to NOT EQUALS syntax. Handles formats…, Handle caller exclusions., Test handling of empty filter cases., Test caller exclusion parsing., Test parsing known caller (logicmonitor)., Test parsing single sys_id. (+4 more)

### Community 99 - "TestEdgeCasesAndErrorHandling"
Cohesion: 0.12
Nodes (9): Test edge cases and error handling scenarios., Test ServiceNowQueryBuilder handles None inputs gracefully., Test ServiceNowQueryBuilder handles empty lists gracefully., Test priority filter validation with empty string., Test date range filter validation with empty string., Test result count validation with edge values., Test debug_query_construction handles None inputs., Test pagination params with edge values. (+1 more)

### Community 100 - "_is_complete_servicenow_filter"
Cohesion: 0.20
Nodes (7): _handle_servicenow_filter_condition(), _is_complete_servicenow_filter(), Check if value is already a complete ServiceNow filter (e.g.,…, Handle complete ServiceNow filters. Structural, so guarded not escaped., Test detecting complete ServiceNow filters with ^OR and proper field=value…, Test non-complete filters., Test that values with ^OR but no field=value before ^OR are rejected. This is…

### Community 101 - "TestCMDBToolsValidation"
Cohesion: 0.20
Nodes (6): Test input validation and error handling for CMDB tools., Test CI number format validation., Test CI type parameter validation., Test search attributes parameter validation., Test search term validation for quick search., TestCMDBToolsValidation

### Community 102 - "TestReadFailuresPropagate"
Cohesion: 0.14
Nodes (6): asyncio, Derived from the CODE, not from a list. The list was wrong once already. The…, The headline bug: a 30s deadline must never look like a missing record., Empty is success. Deciding it means not-found is the consumer's job., TestReadFailuresPropagate, ok()

### Community 103 - "test_pyproject_sync.py"
Cohesion: 0.17
Nodes (19): importlib_util, _load_build_mcpb(), _load_manifest(), _load_pyproject(), _local_top_level_names(), _main_version(), Path, Packaging-consistency tests for the .mcpb bundle sources. These guard the… (+11 more)

### Community 104 - ".test_read_only_hint_is_served"
Cohesion: 0.25
Nodes (6): asyncio, `read_only` must agree with the docstring's SIDE EFFECT line and reach the wire…, The guidance must reach the WIRE, not just inspect.getdoc. FastMCP builds the…, search_records(), TestReadOnlyAnnotation, TestServedDescription

### Community 105 - "_ci_type_error"
Cohesion: 0.29
Nodes (6): _ci_type_error(), Return an error message if ci_type is not a usable cmdb_ci* table, else None.…, parametrize, The old bare prefix check accepted this; the shape check does not., re.match with `$` accepts one trailing newline; fullmatch does not., TestCiTypePolicy

### Community 106 - "TestTaskSysIdRetrieval"
Cohesion: 0.20
Nodes (6): Test sys_id retrieval function., Test successful sys_id retrieval., Test sys_id retrieval when task not found., Decision (d): None means absent, so a failed read must not return None. This…, Test sys_id retrieval with invalid response., TestTaskSysIdRetrieval

### Community 107 - "_make_paginated_request"
Cohesion: 0.13
Nodes (12): _make_paginated_request(), Make paginated requests to get complete result sets. Raises:…, Test that _make_paginated_request injects sort order., Test that default sort order is injected into paginated requests., Test that a custom sort directive is respected., Test that sort is not injected when default_sort is empty., Test that an existing ORDERBY in the URL is not replaced., TestPaginationSortIntegration (+4 more)

### Community 108 - "TestCMDBToolsIntegration"
Cohesion: 0.25
Nodes (5): Integration tests for CMDB tools workflow., Set up integration test fixtures., Test complete CMDB discovery workflow., Test complete CMDB search workflow., TestCMDBToolsIntegration

### Community 109 - "FastMCP Server Core"
Cohesion: 0.22
Nodes (9): Architecture Overview Document, AuthMiddleware SSE Bearer, FastMCP Server Core, Stdout JSON-RPC Stderr Logs Invariant, tools.py Tool Registration, stdio and SSE Transport, SSE Auth Independent of ServiceNow OAuth, AuditMiddleware Structured Logging (+1 more)

### Community 110 - "TestRetryWithFreshToken"
Cohesion: 0.25
Nodes (5): Test retry with fresh token functionality., Test successful retry with fresh token., Test retry with fresh token that fails., retry_with_fresh_token re-raises HTTPStatusError when raise_for_status=True., TestRetryWithFreshToken

### Community 111 - "TestOAuthTokenHandling"
Cohesion: 0.25
Nodes (5): Test OAuth token handling and validation., Test validation of valid OAuth token format., Test validation of malformed OAuth token., Test token expiration logic., TestOAuthTokenHandling

### Community 112 - "ServiceNowOAuthClient"
Cohesion: 0.13
Nodes (9): Any, AsyncClient, Response, Return Authorization + JSON headers for an API request. Inlined (rather than…, Make an authenticated request to ServiceNow API. Delegates to RequestExecutor;…, Test the OAuth connection by making a simple API call., OAuth 2.0 Client Credentials implementation for ServiceNow. Composes three…, ServiceNowOAuthClient (+1 more)

### Community 113 - "TestOAuthEnvironmentSetup"
Cohesion: 0.25
Nodes (5): Test OAuth environment variable configuration., Set up test fixtures., Test that required OAuth environment variables are configured., Test that environment variables have expected formats., TestOAuthEnvironmentSetup

### Community 114 - ".test_register_tools_rejects_blank_guidance_field"
Cohesion: 0.25
Nodes (3): register_tools fails loudly on a tool with no guidance., A guidance entry with a blank field fails at the gate, not just in unit tests —…, TestProtocolIsMandatory

### Community 115 - "test_kb_article_tools.py"
Cohesion: 0.15
Nodes (11): _handle_kb_error(), HTTPStatusError, _unwrap_kb_write_response(), _write_kb_article(), _make_http_status_error(), HTTPStatusError, Tests for kb_article_tools.py — KB article write path (update / publish /…, An empty write response cannot establish that the write landed. (+3 more)

### Community 116 - "_get_kb_article_meta"
Cohesion: 0.15
Nodes (10): _get_kb_article_meta(), Fetch sys_id + short_description in one GET — avoids a second round-trip in…, Return the published row for *article_number*, or None if not yet published.…, _verify_kb_published(), The shape a failed GET now arrives in for this module (v4.4 Tier 0.3)., _verify_kb_published is the source of truth for publish success., None means "no Published row yet"; a failed read is not that. Conflating them…, TestGetKbArticleMeta (+2 more)

### Community 117 - "test_vtb_task_tools.py"
Cohesion: 0.09
Nodes (21): _handle_http_error(), _prepare_task_create_data(), Any, HTTPStatusError, Map an HTTP error to the {"error": {code, message}} contract shape., Extract the inner result payload into the §3.1 write shape., Prepare and validate data for task creation., _unwrap_write_response() (+13 more)

### Community 118 - "test_oauth_client_enhanced.py"
Cohesion: 0.07
Nodes (34): datetime, oauth, Exception, OAuth-domain exception hierarchy., Exception raised when authentication fails., Exception raised when connection to ServiceNow fails., Exception raised when authorization is denied., Base exception for ServiceNow OAuth operations. (+26 more)

### Community 119 - "TestGoldenSetIntegrity"
Cohesion: 0.25
Nodes (3): The set is worthless if it drifts out of sync with the registry., Adding or renaming a tool must be a deliberate decision here., TestGoldenSetIntegrity

### Community 120 - "TestSelectionBaseline"
Cohesion: 0.25
Nodes (4): Ratchet: the surface may get more discriminating, never less., Total plausible paths across the set — the overlap metric of plan decision 3., Not an assertion — prints the per-intent table. Run with -s to read it., TestSelectionBaseline

### Community 121 - "TestFooterInjection"
Cohesion: 0.29
Nodes (3): The registered docstring carries exactly one generated guidance footer., FastMCP serves only the pre-Args text as the description, so the guidance MUST…, TestFooterInjection

### Community 122 - ".test_test_connection_failure"
Cohesion: 0.33
Nodes (4): Test connection testing functionality., Test successful connection test., Test failed connection test., TestConnectionTesting

### Community 124 - "ServiceNowQueryBuilder"
Cohesion: 0.07
Nodes (16): ServiceNow query-string builder. Static helpers that emit syntactically-correct…, Helper class for building ServiceNow queries with proper syntax., Build date range filter for ServiceNow using proper BETWEEN syntax., Build exclusion filter for multiple IDs using NOT EQUALS., ServiceNowQueryBuilder, Test proper BETWEEN syntax generation., Specific tests for ServiceNowQueryBuilder class., Set up test fixtures. (+8 more)

### Community 125 - "TestTableFilterParams"
Cohesion: 0.25
Nodes (5): Test TableFilterParams model., Test creating params with filters., Test creating params with fields., Test creating empty params., TestTableFilterParams

### Community 126 - "TestOAuthClientExtended"
Cohesion: 0.39
Nodes (3): dict, patch, TestOAuthClientExtended

### Community 128 - ".test_get_basic_auth_header"
Cohesion: 0.50
Nodes (3): Test Basic Auth header generation., Test Basic Auth header generation., TestBasicAuthHeader

### Community 129 - "TestSLATokenBudgetConstants"
Cohesion: 0.25
Nodes (5): Lock budget constants — accidental relaxation should fail review., Curated 7-field view must be at most ~15% over standard ESSENTIAL list., Performance preset has 11 fields vs essential's 6; budget reflects that., A sys_id lookup must never need more than ~200 tokens (1 row)., TestSLATokenBudgetConstants

### Community 130 - ".test_make_authenticated_request_raises_on_non_401"
Cohesion: 0.50
Nodes (3): raise_for_status=True surfaces HTTPStatusError from write operations., raise_for_status=True propagates 4xx/5xx errors instead of returning None., TestRaiseForStatusPropagation

### Community 132 - "TestPrivateTaskTools"
Cohesion: 0.25
Nodes (5): Test updating an existing private task., Test private task tools with CRUD operations., Set up test fixtures., Test creating a new private task., TestPrivateTaskTools

### Community 145 - "test_cli.py"
Cohesion: 0.29
Nodes (6): subprocess, Tests for CLI argument handling., --help should print usage and exit 0., --version should print version and exit 0., test_help_flag(), test_version_flag()

### Community 146 - "TestNewQueryResetRefusal"
Cohesion: 0.33
Nodes (3): `^NQ` discards every condition before it, so a scoped query becomes a table…, Why the check runs before the handlers rather than inside the encoder.…, TestNewQueryResetRefusal

### Community 147 - "consolidated_tools.py"
Cohesion: 0.14
Nodes (13): Partial Read Keeps Rows, Read-Failure Contract (ServiceNowRequestError), _format_deduped_kb_row(), _order_states(), Consolidated tools with unique logic that cannot be replaced by generic…, Distinct states in priority order (unknown states last, alphabetical)., Render a de-duplicated KB row in the public response shape., carry_partial() (+5 more)

### Community 151 - "_reset_http_pool"
Cohesion: 0.40
Nodes (4): fixture, Shared pytest fixtures. The v4.2 connection-pooling refactor introduced a…, Drop the cached pooled client before and after each test., _reset_http_pool()

### Community 152 - "Bitbucket CI Pipeline"
Cohesion: 0.50
Nodes (4): Bitbucket CI Pipeline, pytest Coverage CI Step, SonarCloud Quality Scan, pytest Dev Test Stack

### Community 159 - "TestUpdatePrivateTask"
Cohesion: 0.25
Nodes (5): Test update_private_task function with OAuth authentication., Test successful private task update., Test update fails without update data., Test update fails when task not found., TestUpdatePrivateTask

## Knowledge Gaps
- **82 isolated node(s):** `manifest_version`, `name`, `display_name`, `version`, `description` (+77 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1302 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Read-Failure Contract (ServiceNowRequestError)` connect `consolidated_tools.py` to `Personal MCP ServiceNow Project`, `39 MCP Tools Inventory`?**
  _High betweenness centrality (0.090) - this node is a cross-community bridge._
- **Why does `ServiceNowRequestError` connect `ServiceNowRequestError` to `generic_table_tools.py`, `classify_read_failure`, `TestServiceNowAPI`, `request_dispatcher.py`, `health_check`, `kb_article_tools.py`, `test_typed_read_kb_article_tools.py`, `test_failure_shape_conforms`, `test_tool_response_contract.py`, `ErrorCode`, `asyncio`, `make_nws_request`, `asyncio`, `_publish_with_verify`, `update_private_task`, `get_records_by_priority`, `os`, `TestReadFailuresPropagate`, `TestTaskSysIdRetrieval`, `_make_paginated_request`, `test_kb_article_tools.py`, `_get_kb_article_meta`, `test_vtb_task_tools.py`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Why does `39 MCP Tools Inventory` connect `39 MCP Tools Inventory` to `Personal MCP ServiceNow Project`, `FastMCP Server Core`, `generic_table_tools Query Engine`, `Generic Tool Wrappers`, `Architecture Documentation Index (v4.3 Diagrams)`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `ServiceNowOAuthClient` (e.g. with `RequestExecutor` and `TokenStore`) actually correct?**
  _`ServiceNowOAuthClient` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `ServiceNowRequestError` (e.g. with `TestClassifyTransportFailures` and `TestErrorVocabulary`) actually correct?**
  _`ServiceNowRequestError` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `ErrorCode` (e.g. with `QueryValueError` and `TestClassifyOAuthFailures`) actually correct?**
  _`ErrorCode` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `get_kb_articles_by_state()` (e.g. with `TableFilterParams` and `tools.py`) actually correct?**
  _`get_kb_articles_by_state()` has 2 INFERRED edges - model-reasoned connections that need verification._