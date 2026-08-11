# Graph Report - personal-mcp-servicenow  (2026-08-11)

## Corpus Check
- 97 files · ~94,710 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2819 nodes · 5535 edges · 133 communities (123 shown, 10 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 399 edges (avg confidence: 0.59)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `778e2d4e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ServiceNowOAuthClient
- asyncio
- generic_table_tools.py
- TestQueryBuilding
- ServiceNowRequestError
- query_table_with_filters
- ErrorCode
- config_loader.py
- test_date_utils.py
- ValueError
- consolidated_tools.py
- TestHealthCheckTool
- TestServiceNowAPI
- build_date_filter
- test_security_sanitization.py
- make_nws_request
- test_tool_selection.py
- test_oauth.py
- test_query_value_encoding.py
- test_tool_registry.py
- health_check
- asyncio
- test_oauth_client_enhanced.py
- QueryValidationResult
- test_param_coercion.py
- asyncio
- _Capture
- kb_article_tools.py
- validate_date_format
- error_response
- KbDuplicateCheckInconclusive
- test_failure_shape_conforms
- TestServiceNowFiltering
- build_last_n_days_filter
- TestCMDBTools
- ._do_request_access_token
- validate_and_correct_filters
- test_tool_response_contract.py
- TokenStore
- build_mcpb.py
- TestProbeFailuresAreNotAbsence
- asyncio
- validate_priority_filter
- asyncio
- test_typed_read_cmdb_tools.py
- TestPriorityParsing
- validator.py
- TestUtilityFunctions
- TableSpec
- filter_records
- Architecture Documentation Index (v4.3 Diagrams)
- OAuth 2.0 Client Credentials Flow
- validate_result_count
- _publish_with_verify
- asyncio
- test_token_footprint.py
- query_slas_by_status Presets
- get_ci_details
- normalize_date_to_full_format
- create_private_task
- _prepare_task_create_data
- update_private_task
- TestServiceNowOAuthClientInit
- TestDateParsing
- TestTextSearchTokenizerImmunity
- TestKeySetConsistency
- update_knowledge_article
- run_tests.py
- test_integration.py
- Personal MCP ServiceNow Project
- TestServiceNowQueryBuilder
- Migration Guide: v4.x → v5.0 "Boron"
- _build_priority_result_message
- validate_date_range_filter
- TestDoubleEncoding
- _write_private_task
- get_records_by_priority
- 39 MCP Tools Inventory
- test_no_stdout_pollution.py
- _validate_regex_input
- generic_table_tools Query Engine
- Generic Tool Wrappers
- TestSpecWellFormed
- test_query_validation.py
- MCPB Build Guide
- _inject_sort_order
- oauth/ Package
- get_yesterday_range
- extract_keywords
- TestDateFilterIntegration
- asyncio
- TestOptJsonDict
- TestOptJsonList
- TestDerivationFidelity
- _table_of
- test_a_caret_would_have_produced_two_conditions
- manifest.json
- retire_knowledge_article
- TestCallerExclusions
- TestEdgeCasesAndErrorHandling
- _FakeOAuthClient
- TestReadFailuresPropagate
- test_pyproject_sync.py
- args
- _ci_type_error
- constants.py
- TestPaginationSortIntegration
- FastMCP Server Core
- Any
- test_kb_article_tools.py
- _verify_kb_published
- test_vtb_task_tools.py
- TestServiceNowOAuthExceptions
- ServiceNowQueryBuilder
- TestTableFilterParams
- TestOAuthClientExtended
- TestSLATokenBudgetConstants
- TestPrivateTaskTools
- client_id
- client_secret
- env
- keywords
- test_cli.py
- TestNewQueryResetRefusal
- Read-Failure Contract (ServiceNowRequestError)
- servicenow_instance
- _reset_http_pool
- Bitbucket CI Pipeline
- platforms
- tests/__init__.py
- TestUpdatePrivateTask
- PayPal Sponsor Funding
- personal-mcp-servicenow

## God Nodes (most connected - your core abstractions)
1. `ServiceNowRequestError` - 99 edges
2. `ErrorCode` - 72 edges
3. `ServiceNowOAuthClient` - 59 edges
4. `_send()` - 41 edges
5. `KbDuplicateCheckInconclusive` - 39 edges
6. `_check_kb_duplicates()` - 38 edges
7. `query_table_with_filters()` - 36 edges
8. `TokenStore` - 36 edges
9. `make_nws_request()` - 35 edges
10. `error_response()` - 34 edges

## Surprising Connections (you probably didn't know these)
- `03 Tool Organization Diagram` --semantically_similar_to--> `39 MCP Tools Inventory`  [INFERRED] [semantically similar]
  Diagrams & Documentation/README.md → README.md
- `SLA Token Optimization Strategy` --semantically_similar_to--> `GET Token-Optimization Invariants`  [INFERRED] [semantically similar]
  Diagrams & Documentation/06-sla-architecture-flow.md → CHANGELOG.md
- `Personal MCP ServiceNow Integration Server` --semantically_similar_to--> `Personal MCP ServiceNow Project`  [INFERRED] [semantically similar]
  README.md → CHANGELOG.md
- `SLA Management Tools (5)` --semantically_similar_to--> `SLA Tool Consolidation (Sprint 2)`  [INFERRED] [semantically similar]
  README.md → CHANGELOG.md
- `Claude Desktop .mcpb Easy Install` --semantically_similar_to--> `Claude Desktop Extension (.mcpb) Packaging`  [INFERRED] [semantically similar]
  README.md → CHANGELOG.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **v4.0 Package Split (filter + http_layer + oauth)** — changelog_filter_package, changelog_http_layer_package, changelog_oauth_package, changelog_release_4_0_0 [EXTRACTED 1.00]
- **Encoded-Query Value Guard Layers (4.4.1)** — changelog_encode_query_value, changelog_caret_refusal, changelog_ampersand_escape, changelog_nq_refusal, changelog_structural_vs_terminal_handlers, changelog_encoded_query_value_boundary [EXTRACTED 1.00]
- **End-to-End Layered Request Path** — readme_fastmcp, readme_generic_table_tools, changelog_filter_package, changelog_http_layer_package, changelog_oauth_package, readme_servicenow_rest_api [EXTRACTED 1.00]
- **GET Read-Path Pipeline** — diagrams_documentation_01_architecture_overview_generic_table_tools, diagrams_documentation_01_architecture_overview_make_nws_request, diagrams_documentation_04_similarity_search_flow_url_builder, diagrams_documentation_04_similarity_search_flow_response_parser, diagrams_documentation_02_oauth_request_executor [EXTRACTED 1.00]
- **OAuth Authentication Stack** — diagrams_documentation_02_oauth_singleton, diagrams_documentation_02_oauth_client_facade, diagrams_documentation_02_oauth_token_store, diagrams_documentation_02_oauth_request_executor, diagrams_documentation_02_oauth_http_pool, diagrams_documentation_02_oauth_client_credentials [EXTRACTED 1.00]

## Communities (133 total, 10 thin omitted)

### Community 0 - "ServiceNowOAuthClient"
Cohesion: 0.05
Nodes (39): Return Authorization + JSON headers for an API request. Inlined (rather than…, OAuth 2.0 Client Credentials implementation for ServiceNow. Composes three…, ServiceNowOAuthClient, setter, asyncio, dict, Test Basic Auth header generation., Test access token request functionality. (+31 more)

### Community 1 - "asyncio"
Cohesion: 0.07
Nodes (25): PartialPageReadError, Exception, A page after the first failed; the rows already collected are attached.…, _assert_plain_failure(), asyncio, Otherwise every `except ServiceNowRequestError` arm would eat the rows., Two good pages then a failure keeps 500 rows, not just the last page., Narrowing the except must not remove the catch-all for real bugs. (+17 more)

### Community 2 - "generic_table_tools.py"
Cohesion: 0.07
Nodes (45): encode_query_value(), QueryValueError, Per-value encoding boundary for ServiceNow encoded queries (v4.4.1). One half…, Escape one caller-supplied value for use inside a ``sysparm_query``. Args:…, A caller value cannot be carried by ServiceNow's encoded-query syntax. Raised…, Build a refusal from a message template in ``constants``. Keeps the value echo…, The §3.1 failure shape. Consumers return this straight to the client., _truncate() (+37 more)

### Community 3 - "TestQueryBuilding"
Cohesion: 0.03
Nodes (40): _build_query_string(), _handle_bare_or_value_condition(), _has_operator_in_value(), Check if value already contains a comparison operator or ServiceNow text…, Handle values with ^OR where the first segment is a bare value (missing field…, Build the complete query string from filters. Raises: QueryValueError: a filter…, Test query building functions., Test detecting operators in value. (+32 more)

### Community 4 - "ServiceNowRequestError"
Cohesion: 0.09
Nodes (24): _from_decode(), _from_oauth_auth(), _from_oauth_connection(), _from_oauth_forbidden(), _from_status_error(), _from_timeout(), _from_transport(), Any (+16 more)

### Community 5 - "query_table_with_filters"
Cohesion: 0.08
Nodes (25): BaseModel, Generic filter parameters for table queries., TableFilterParams, query_table_with_filters(), Generic function to query table with custom filters and fields. Supports…, asyncio, Test async table operation functions., Test querying table by text with results. (+17 more)

### Community 6 - "ErrorCode"
Cohesion: 0.08
Nodes (32): datetime, classify_read_failure(), ErrorCode, Map a read-path exception onto the error vocabulary. ``TimeoutError`` covers…, The complete failure vocabulary. Adding a code is a contract change., Exception, OAuth-domain exception hierarchy., Exception raised when authentication fails. (+24 more)

### Community 7 - "config_loader.py"
Cohesion: 0.06
Nodes (42): ConfigError, get_config_dir(), get_config_file_path(), get_setup_instructions(), load_config(), load_config_from_env(), load_config_from_file(), Any (+34 more)

### Community 8 - "test_date_utils.py"
Cohesion: 0.08
Nodes (22): get_current_month_range(), get_last_n_days_range(), get_this_week_range(), get_today_range(), Date utilities for ServiceNow MCP incident queries. Provides date validation,…, Get start and end dates for the current calendar month. Returns: Tuple of…, Get start and end dates for the last N days (including today). Args: days:…, Get start (Monday) and end (Sunday) of the current week. Returns: Tuple of… (+14 more)

### Community 9 - "ValueError"
Cohesion: 0.22
Nodes (11): coerce_json_dict(), coerce_json_list(), Any, Param-boundary JSON coercion for MCP tool signatures. LLM-driven MCP clients…, Peel repeated JSON-string layers (handles single- AND double-encoded input).…, Coerce a (possibly double-encoded) stringified JSON array to a native list., Coerce a (possibly double-encoded) stringified JSON object to a native dict., _unwrap_json_str() (+3 more)

### Community 10 - "consolidated_tools.py"
Cohesion: 0.06
Nodes (33): _build_metadata(), _build_sla_status_filter(), _format_deduped_kb_row(), _get_error_message(), get_kb_articles_by_state(), _merge_filters(), _pick_canonical_kb_row(), Any (+25 more)

### Community 11 - "TestHealthCheckTool"
Cohesion: 0.20
Nodes (8): patch, Test the consolidated diagnostic tool (v5.0: 5 auth tools -> health_check)., A reachable instance reports connection ok., probe_table returns sample field names., Test the surviving knowledge read tool (v5.0: smart-KB reads culled)., Test the version-collapsing KB state rollup., TestHealthCheckTool, TestKnowledgeBaseTools

### Community 12 - "TestServiceNowAPI"
Cohesion: 0.05
Nodes (25): patch, Test extracting display values from non-dict input., Test that URLs without sysparm_query pass through unchanged., Test that spaces in query values are percent-encoded., Test that ServiceNow operators (=, ^, <, >, etc.) are preserved., Test that # in query is encoded to prevent URL fragment issues., Test that already-encoded URLs are not double-encoded., Test that other URL parameters are not affected by encoding. (+17 more)

### Community 13 - "build_date_filter"
Cohesion: 0.14
Nodes (12): build_date_filter(), Build ServiceNow date filter using simple >= and <= operators. This replaces…, Test date filter building., Test filter with both start and end dates., Test filter with only start date., Test filter with only end date., Test filter with no dates returns None., Test filter with both None returns None. (+4 more)

### Community 14 - "test_security_sanitization.py"
Cohesion: 0.09
Nodes (34): AuditMiddleware, Middleware, MiddlewareContext, Audit logging middleware for MCP tool calls. Emits one structured JSON log line…, _sanitize(), _summarize(), _user_from_headers(), AuthMiddleware (+26 more)

### Community 15 - "make_nws_request"
Cohesion: 0.06
Nodes (40): HTTP layer for the ServiceNow REST API — v4.0 Sprint 3 split. The v3…, get_auth_info(), _get_typed(), make_nws_request(), Any, Read/write request dispatcher for the ServiceNow REST API. This is the v4.0…, The GET pipeline, with failures raised as ``ServiceNowRequestError``. An empty…, Test OAuth connection and return status. (+32 more)

### Community 16 - "test_tool_selection.py"
Cohesion: 0.07
Nodes (29): _evaluate(), evaluation(), _plausible_paths(), _profiles(), fixture, parametrize, _rank(), Golden intent set — tool-selection baseline (v4.4 Tier 0.1). Measures whether… (+21 more)

### Community 17 - "test_oauth.py"
Cohesion: 0.05
Nodes (27): dict, patch, Test OAuth client creation fails with missing environment variables., Test API client integration with OAuth., Test that get_auth_info correctly detects OAuth configuration., Test get_auth_info when OAuth credentials are not available., Test OAuth token retrieval with mocked client., Test OAuth token handling and validation. (+19 more)

### Community 18 - "test_query_value_encoding.py"
Cohesion: 0.06
Nodes (52): _probe_ci_table(), Any, Search Configuration Items by multiple attributes. TABLES: cmdb_ci (or a given…, Fetch a CI by number from one table; return the first row, or None if absent.…, search_cis_by_attributes(), _query_via_generic(), v4.4.1 — the encoded-query value boundary, asserted against what ServiceNow…, Re-encoding an already-encoded URL changes nothing. The property the old… (+44 more)

### Community 19 - "test_tool_registry.py"
Cohesion: 0.09
Nodes (21): asyncio, Tool-guidance registry + docstring-footer injection (v5.0 "Boron" Tier 3.3).…, register_tools fails loudly on a tool with no guidance., A guidance entry with a blank field fails at the gate, not just in unit tests —…, The registry and the registered surface must match exactly., The registered docstring carries exactly one generated guidance footer., FastMCP serves only the pre-Args text as the description, so the guidance MUST…, The guidance must reach the WIRE, not just inspect.getdoc. FastMCP builds the… (+13 more)

### Community 20 - "health_check"
Cohesion: 0.10
Nodes (15): asyncio, fixture, Guards the premise of test_table_outside_the_allowlist_costs_no_request., health_check reports the classified failure through the real dispatcher. If a…, The point of a diagnostic is to name the right failure., TestConnectivityProbe, TestEndToEndThroughTheRealDispatcher, TestSchemaProbe (+7 more)

### Community 21 - "asyncio"
Cohesion: 0.09
Nodes (16): OptJsonDict, get_priority_incidents(), query_slas_by_status(), Get incidents filtered by priority value, with an optional date window. TABLES:…, Query SLA records by a named status preset. TABLES: task_sla only. SIDE EFFECT:…, asyncio, Test SLA tool functions., v4.0 fix: routes via sys_id={sys_id}, not the broken number={sys_id}. (+8 more)

### Community 22 - "test_oauth_client_enhanced.py"
Cohesion: 0.09
Nodes (23): get_oauth_client(), _hydrate_env_from_config(), make_oauth_request(), Any, Module-level OAuth client singleton + convenience request helpers. Canonical…, Populate SERVICENOW_* env vars from the setup-wizard config file. The OAuth…, Get or create the global OAuth client instance., Convenience function for making OAuth-authenticated GET requests. Propagates… (+15 more)

### Community 23 - "QueryValidationResult"
Cohesion: 0.11
Nodes (13): QueryValidationResult, Container for query validation results., Add a warning message., Add a suggestion for improvement., True if the query is invalid or has warnings., Test the QueryValidationResult class., Test initializing valid QueryValidationResult., Test initializing invalid QueryValidationResult. (+5 more)

### Community 24 - "test_param_coercion.py"
Cohesion: 0.17
Nodes (3): Tests for param_coercion.py — JSON-string coercion at the MCP tool param…, TestJsonDict, TestJsonList

### Community 25 - "asyncio"
Cohesion: 0.06
Nodes (26): publish_knowledge_article(), Publish ONE knowledge article via the ServiceNow workflow endpoint. TABLES:…, TestPublishKnowledgeArticle, _assert_plain_failure(), asyncio, parametrize, The guard must not have become so strict that nothing can publish., `[]` must mean "checked, clear" and nothing else. (+18 more)

### Community 26 - "_Capture"
Cohesion: 0.11
Nodes (16): _Capture, asyncio, parametrize, A free-text search on task_sla must dot-walk task.short_description. task_sla…, A bare short_description condition is the silently-dropped filter., query_table_by_text resolves the search field from the table. The bug once…, A caller that forgets search_field must still get a valid query., The caller's conditions from a captured URL, sort clause removed. Splitting the… (+8 more)

### Community 27 - "kb_article_tools.py"
Cohesion: 0.11
Nodes (25): _call_kb_publish_workflow(), _call_kb_workflow(), _check_single_kb_duplicate(), _dedup_query_defect(), _duplicate_check_inconclusive(), _duplicate_row_inconclusive(), _fire_publish(), _handle_kb_error() (+17 more)

### Community 28 - "validate_date_format"
Cohesion: 0.10
Nodes (16): Validate date format is either "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS". Args:…, validate_date_format(), Test date format validation., Test valid YYYY-MM-DD format., Test valid YYYY-MM-DD HH:MM:SS format., Test valid midnight time., Test valid end of day time., Test invalid MM-DD-YYYY format. (+8 more)

### Community 29 - "error_response"
Cohesion: 0.05
Nodes (52): The field a free-text search must target for *table_name*., text_search_field_for(), _build_similar_ci_response(), quick_ci_search(), Build the list-contract response for similar CIs. Complexity: 2, Quick search for CIs by name, IP, or number (OR across all three). TABLES:…, _exclude_original_record(), find_similar_records() (+44 more)

### Community 30 - "KbDuplicateCheckInconclusive"
Cohesion: 0.11
Nodes (14): KbDuplicateCheckInconclusive, _normalize_publish_result(), _outcome_error_message(), BaseException, Exception, Message for an exception that escaped a per-article coroutine., Normalize publish_knowledge_article output into a flat batch-result row. Four…, The duplicate check could not produce a trustworthy answer. Distinct from "no… (+6 more)

### Community 31 - "test_failure_shape_conforms"
Cohesion: 0.17
Nodes (15): Discard the cached token. Used by the 401-retry path., assert_contract(), _assert_error_shape(), _invoke(), asyncio, fixture, parametrize, Patch the dispatcher's read + write seams. `mode` picks success/failure. (+7 more)

### Community 32 - "TestServiceNowFiltering"
Cohesion: 0.06
Nodes (21): _handle_priority_condition(), _parse_priority_list(), Parse priority list and convert to proper OR syntax. Handles formats like: -…, Handle priority list parsing., patch, Test multiple caller exclusions by sys_id., Test that URL encoding preserves JavaScript functions., Test ServiceNowQueryBuilder query validation. (+13 more)

### Community 33 - "build_last_n_days_filter"
Cohesion: 0.16
Nodes (11): _sla_filter_breached(), _sla_filter_performance(), build_last_n_days_filter(), Build ServiceNow filter for records from the last N days. This replaces the…, Test build_last_n_days_filter helper function., Test filter uses sys_created_on by default., Test filter with custom date field., Test filter for last 1 day. (+3 more)

### Community 34 - "TestCMDBTools"
Cohesion: 0.04
Nodes (25): Test finding CIs with invalid type., Test searching CIs by name attribute., Test searching CIs by IP address attribute., Test searching CIs by multiple attributes., Test successful CI details retrieval., Test suite for CMDB tools functionality., Test CI details retrieval for non-existent CI., Test finding similar CIs for a given CI. (+17 more)

### Community 35 - "._do_request_access_token"
Cohesion: 0.14
Nodes (11): _close_pool_atexit(), get_pooled_client(), AsyncClient, Process-wide pooled ``httpx.AsyncClient`` for all ServiceNow traffic. Before…, Return the shared keep-alive client, creating it on first use., Close the pooled client and drop the reference. Idempotent., Best-effort close on interpreter exit to avoid unclosed-client warnings., shutdown_http_client() (+3 more)

### Community 36 - "validate_and_correct_filters"
Cohesion: 0.33
Nodes (6): _correct_date(), _correct_priority(), Return (corrected_value, suggestion_or_None) for a priority field., Return (corrected_value, suggestion_or_None) for a sys_created_on field., Validate filters and auto-correct common syntax issues. Returns a result with…, validate_and_correct_filters()

### Community 37 - "test_tool_response_contract.py"
Cohesion: 0.09
Nodes (32): get_all_ci_types(), Get all available CI types/classes in the CMDB. TABLES: sys_db_object (live…, get_sla_details(), query_slas_by_task(), Get one SLA record by its sys_id (task_sla lookup). TABLES: task_sla only. SIDE…, Get every SLA record attached to one task, addressed by task number. TABLES:…, find_similar(), get_record() (+24 more)

### Community 38 - "TokenStore"
Cohesion: 0.08
Nodes (21): AuthHeaderSource, ServiceNowOAuthClient — orchestrator façade. Composes ``TokenStore`` +…, Any, AsyncClient, Response, Authenticated HTTP request execution with 401 retry. Owns the actual…, Drop the cached token, re-authenticate, retry once., Make authenticated HTTP requests with token-refresh on 401. (+13 more)

### Community 39 - "build_mcpb.py"
Cohesion: 0.15
Nodes (22): assert_no_leaks(), assert_versions_aligned(), clean_staging(), copy_package_dirs(), copy_root_files(), fail(), main(), Path (+14 more)

### Community 40 - "TestProbeFailuresAreNotAbsence"
Cohesion: 0.21
Nodes (7): _by_table(), The headline bug: one timed-out probe attributing a CI to the wrong table., cmdb_ci_server times out; the base cmdb_ci row must NOT be the answer., A higher-priority table already decided; later failures are irrelevant., A real bug must not be laundered into a not-found record., Fake make_nws_request that answers per table name in the URL., TestProbeFailuresAreNotAbsence

### Community 41 - "asyncio"
Cohesion: 0.12
Nodes (12): JsonList, _check_kb_duplicates(), publish_knowledge_articles(), Return KB articles matching short_description exactly across live workflow…, Check for duplicate KB articles without publishing. TABLES: kb_knowledge only.…, Publish MULTIPLE KB articles in one tool call (batch). TABLES: kb_knowledge…, asyncio, The headline fix: [] means "checked, clear" and nothing else. The old test… (+4 more)

### Community 42 - "validate_priority_filter"
Cohesion: 0.11
Nodes (16): _has_comma_syntax_issue(), _has_or_format_issue(), Check if priority filter has comma syntax issue., Check if OR syntax is missing priority= prefix., Check if numeric format suggestion should be added., Validate priority filter syntax with enhanced debugging., _should_suggest_numeric_format(), validate_priority_filter() (+8 more)

### Community 43 - "asyncio"
Cohesion: 0.15
Nodes (13): _extract_ci_search_attributes(), _filter_and_limit_ci_results(), Extract search attributes from CI data. Complexity: 4, Filter out original CI and limit results. Complexity: 3, Find Configuration Items similar to a given CI, by shared attributes. TABLES:…, similar_cis_for_ci(), _assert_empty_list(), asyncio (+5 more)

### Community 44 - "test_typed_read_cmdb_tools.py"
Cohesion: 0.15
Nodes (8): _assert_internal(), _assert_plain_failure(), Typed read failures + response contract in the CMDB tools. v4.4 Tier 0.3 gave…, Failures reach this module through the real dispatcher, gather included., A bare-except catch-all: INTERNAL carrying the module's base text., Narrowing the except must not remove the catch-all for real bugs., TestEndToEndThroughTheRealDispatcher, TestSingleRequestReads

### Community 45 - "TestPriorityParsing"
Cohesion: 0.08
Nodes (18): _clean_priority_input(), _normalize_priority_value(), _process_comma_separated_priorities(), Convert P-notation to number (e.g., 'P1' -> '1', '2' -> '2')., Clean brackets, quotes from priority input., Process comma-separated priority list into OR syntax. Structural overall — the…, Test priority parsing functions., Test normalizing P-notation. (+10 more)

### Community 46 - "validator.py"
Cohesion: 0.07
Nodes (32): Filter pipeline — ServiceNow query construction, validation, value escaping.…, Pydantic models and result containers for the filter pipeline., _analyze_caller_exclusion(), _analyze_date_filtering(), _analyze_javascript_functions(), _analyze_original_filters(), _analyze_priority_filtering(), _analyze_url_encoding() (+24 more)

### Community 47 - "TestUtilityFunctions"
Cohesion: 0.11
Nodes (14): build_pagination_params(), Build pagination parameters for ServiceNow queries., Provide suggestions for query improvements., suggest_query_improvements(), Test utility and helper functions., Test cross verification function structure., Test building pagination parameters with defaults., Test building pagination parameters with custom values. (+6 more)

### Community 48 - "TableSpec"
Cohesion: 0.19
Nodes (8): One spec per supported table — the single source of truth (v5.0 "Boron" Tier…, Everything the server needs to know about one ServiceNow table. `number_field`…, True when the table can be addressed by a record number., _spec(), TableSpec, TableSpec consistency (v5.0 "Boron" Tier 3.2). The scattered per-table dicts…, __post_init__ refuses number_field / number_prefix desync, and the registry is…, TestConstructionInvariants

### Community 49 - "filter_records"
Cohesion: 0.22
Nodes (7): filter_records(), OptJsonList, Query a ServiceNow table with field-value filters. SIDE EFFECT: read-only.…, Dot-walking is how `task_sla` is queried at all — it must survive., The reachable surface, not just the internal function. v5.0: filter_records is…, A filters dict's KEYS come from the caller and nothing validated them.…, TestFieldNamesAreCallerSuppliedToo

### Community 50 - "Architecture Documentation Index (v4.3 Diagrams)"
Cohesion: 0.13
Nodes (20): Claude Desktop Extension (.mcpb) Packaging, OR-Combined LIKE Text Query, Release 4.3.0 — mcpb Packaging and Performance, SSE Transport Authentication, 01 Architecture Overview Diagram, Architecture Documentation Index (v4.3 Diagrams), Distribution via .mcpb or Docker SSE, 04 Similarity Search Flow Diagram (+12 more)

### Community 51 - "OAuth 2.0 Client Credentials Flow"
Cohesion: 0.18
Nodes (14): OAuth Authentication Flow Document, OAuth 2.0 Client Credentials Flow, ServiceNowOAuthClient Facade, oauth/http_pool Shared Client, RequestExecutor 401 Retry, oauth/singleton Process-Wide Client, TOKEN_REFRESH_BUFFER_MINUTES, TokenStore Cache and Refresh (+6 more)

### Community 52 - "validate_result_count"
Cohesion: 0.14
Nodes (13): _is_high_priority_query(), Check if query is for high-priority (P1/P2) records., Validate incident result count against expected baselines., Validate if result count seems reasonable for the query., _validate_incident_result_count(), validate_result_count(), Test result count validation functionality., Test validation passes for normal incident count. (+5 more)

### Community 53 - "_publish_with_verify"
Cohesion: 0.10
Nodes (16): _publish_with_verify(), Fire the publish workflow then verify by polling for a Published row. Treats…, Fire-and-verify orchestrator — verify is the only success signal., The main bug class: POST times out, SN still committed the publish., Regression: anyio.fail_after raises builtin TimeoutError, not…, When fire keeps raising HTTPStatusError and verify never finds Published, the…, TestPublishWithVerify, _no_sleep() (+8 more)

### Community 54 - "asyncio"
Cohesion: 0.09
Nodes (30): assert_no_smuggled_parameter(), What ServiceNow's condition parser actually receives, modelled for tests.…, The parameters ServiceNow's servlet layer would see, percent-decoded., The decoded ``sysparm_query`` split into conditions on ``^``., The one condition beginning with *prefix*, with the prefix stripped. Raises if…, No URL parameter appeared that the caller did not ask for. The signature of the…, servicenow_conditions(), servicenow_params() (+22 more)

### Community 55 - "test_token_footprint.py"
Cohesion: 0.12
Nodes (21): _count_tokens(), _list_envelope_overhead(), asyncio, parametrize, Token-footprint regression tests for v4.0 SLA tools. The Sprint 2 acceptance…, Patch query_table_with_filters to return `response`, then call the tool., Per-tool token budgets — must not regress structurally., v3 bug returned 10K rows; v4 must return 1. (+13 more)

### Community 56 - "query_slas_by_status Presets"
Cohesion: 0.29
Nodes (8): query_slas_by_status Presets, SLA Token Optimization Strategy, E2E SLA Preset Prompts, Migration Guide v3 to v4, v3→v4 SLA Tool Name Mapping, v4.1 Test Patch Target Migration, HTTP Token-Budget Invariants Tests, tiktoken Token Footprint Tests

### Community 57 - "get_ci_details"
Cohesion: 0.11
Nodes (19): find_cis_by_type(), get_ci_details(), Get comprehensive details for a specific Configuration Item by number. TABLES:…, Find all Configuration Items of a specific type/class. TABLES: any cmdb_ci*…, _Capture, asyncio, ci_type validation across the CMDB tools (v4.4 Tier 0.6). The bug:…, The headline bug: never query cmdb_ci when the caller named another table. (+11 more)

### Community 58 - "normalize_date_to_full_format"
Cohesion: 0.19
Nodes (9): normalize_date_to_full_format(), Normalize date string to full format with time component. Args: date_string:…, Test date normalization., Test normalizing simple date for start (adds 00:00:00)., Test normalizing simple date for end (adds 23:59:59)., Test full datetime is unchanged for start., Test full datetime is unchanged for end., Test midnight datetime is preserved. (+1 more)

### Community 59 - "create_private_task"
Cohesion: 0.24
Nodes (7): create_private_task(), Create a NEW private task (vtb_task) record. TABLES: vtb_task only (the sole…, Test create_private_task function with OAuth authentication., Test successful private task creation., Test task creation fails without short_description., Test task creation with all optional fields., TestCreatePrivateTask

### Community 60 - "_prepare_task_create_data"
Cohesion: 0.24
Nodes (7): _prepare_task_create_data(), Prepare and validate data for task creation., Test task data preparation function., Test preparing task data with minimal required fields., Test preparing task data with optional fields., Test that extra fields not in optional list are ignored., TestTaskDataPreparation

### Community 61 - "update_private_task"
Cohesion: 0.21
Nodes (10): Update / change an EXISTING private task (vtb_task), addressed by number.…, update_private_task(), _assert_plain_failure(), asyncio, fixture, Decision (b): absent is still absent, and the message is unchanged., A rejected field must not cost a round trip., A failed lookup reaches `update_private_task` through the real dispatcher.… (+2 more)

### Community 62 - "TestServiceNowOAuthClientInit"
Cohesion: 0.20
Nodes (6): Test OAuth client initialization., Test initialization with valid configuration., Test initialization fails when SERVICENOW_INSTANCE is missing., Test initialization fails when CLIENT_ID is missing., Test initialization fails when CLIENT_SECRET is missing., TestServiceNowOAuthClientInit

### Community 63 - "TestDateParsing"
Cohesion: 0.04
Nodes (44): _iso_range_from_month_names(), _month_name_to_num(), _parse_between_format(), _parse_cross_month_range(), _parse_date_range_from_text(), _parse_iso_date_range(), _parse_month_range_format(), _parse_week_format() (+36 more)

### Community 64 - "TestTextSearchTokenizerImmunity"
Cohesion: 0.29
Nodes (4): `query_table_by_text` is safe by accident, so the accident is pinned.…, Pins the mechanism, not just today's outputs. A test that only checks sample…, Covers the record-number branch too, which has its own patterns.…, TestTextSearchTokenizerImmunity

### Community 65 - "TestKeySetConsistency"
Cohesion: 0.18
Nodes (4): Every derived view covers exactly the TABLE_SPECS table set., The task_sla foot-gun is derived from number_field, not a hand list., TestKeySetConsistency, TestStructuralIdentityGuard

### Community 66 - "update_knowledge_article"
Cohesion: 0.36
Nodes (3): Update fields on a knowledge article by article number (e.g. KB0001234).…, update_knowledge_article(), TestUpdateKnowledgeArticle

### Community 67 - "run_tests.py"
Cohesion: 0.20
Nodes (16): check_test_environment(), main(), Show coverage results if available., Main test runner function., Run a command and return success status., Run all tests with coverage reporting and JUnit XML output., Run a specific test module., Run only integration tests. (+8 more)

### Community 68 - "test_integration.py"
Cohesion: 0.09
Nodes (16): asyncio, parametrize, End-to-end integration tests that exercise real product code paths. These tests…, The decoded sysparm_query value from a captured request URL., The outbound query equals the caller's conditions — nothing appended. Domain…, Nothing is dropped after the response comes back. The URL assertions above…, create_private_task → make_nws_request(method=POST) → oauth_client…, Catch import-time errors and circular imports across the codebase. (+8 more)

### Community 69 - "Personal MCP ServiceNow Project"
Cohesion: 0.13
Nodes (16): Ampersand (&) Value Escape, Caret (^) Value Refusal, Domain Filtering Removal, encode_query_value / filter/value_encoding.py, Encoded-Query Value Boundary Contract, _has_operator_in_value Equals Limitation, KB Publish Fail-Closed Duplicate Check, Keep a Changelog Format (+8 more)

### Community 70 - "TestServiceNowQueryBuilder"
Cohesion: 0.07
Nodes (22): Build OR filter for multiple priorities., Build date range filter for ServiceNow using proper BETWEEN syntax., Build ServiceNow relative date filter with proper BETWEEN syntax., Build a complete ServiceNow filter string with proper syntax. Args: priorities:…, Test building relative date filter for this week., Test building relative date filter for last 7 days., Test building relative date filter with unknown period (fallback)., Test building complete filter with priorities only. (+14 more)

### Community 71 - "Migration Guide: v4.x → v5.0 "Boron""
Cohesion: 0.25
Nodes (7): 1. Removed tools and their replacements, 2. Response contract — every tool, 3. `get_priority_incidents` — dropped `**kwargs`, 4. Nothing else changed for callers, Client changes you will actually feel, Migration Guide: v4.x → v5.0 "Boron", Two sanctioned exceptions

### Community 72 - "_build_priority_result_message"
Cohesion: 0.36
Nodes (4): _build_priority_result_message(), Build human-readable result message for priority queries., Test the result message builder., TestBuildPriorityResultMessage

### Community 73 - "validate_date_range_filter"
Cohesion: 0.19
Nodes (9): Validate date range filter completeness and format., validate_date_range_filter(), Test date range filter validation functionality., Test validating proper BETWEEN syntax., Test validation warns about old comparison syntax., Test validation warns about BETWEEN without JavaScript functions., Test validation warns about missing @ separator., Test validation provides suggestion for Week 35 2025. (+1 more)

### Community 75 - "_write_private_task"
Cohesion: 0.29
Nodes (7): Send a write request through make_nws_request, mapping errors locally., _write_private_task(), _make_http_status_error(), asyncio, HTTPStatusError, Test the unified write helper that wraps make_nws_request., TestWritePrivateTask

### Community 76 - "get_records_by_priority"
Cohesion: 0.09
Nodes (16): get_records_by_priority(), Generic function to get records by priority for any table that supports…, Test edge cases and error handling., Test priority parsing with special characters., Test building query with suffix operators., Test that encoding preserves important ServiceNow characters., Test exception handling in find_similar_records., Test getting records by priority with additional filters. (+8 more)

### Community 77 - "39 MCP Tools Inventory"
Cohesion: 0.15
Nodes (15): get_sla_details v3 Bug Fix, SLA Tool Consolidation (Sprint 2), 05 AI Intelligence Flow Diagram, 06 SLA Architecture Flow Diagram, CMDB Tools Module, KB Article Write Tools, make_nws_request Dispatcher, VTB Private Task CRUD Tools (+7 more)

### Community 78 - "test_no_stdout_pollution.py"
Cohesion: 0.19
Nodes (14): expr, _find_offending_prints(), _is_stderr_target(), _iter_runtime_modules(), Path, Lint guard: server runtime code must never print to stdout. MCP stdio transport…, Self-check: the AST scanner must NOT flag stderr-routed prints., True when the ``file=`` argument resolves to ``sys.stderr``. (+6 more)

### Community 79 - "_validate_regex_input"
Cohesion: 0.17
Nodes (10): Pre-validate input to prevent ReDoS attacks., _validate_regex_input(), Test ReDoS (Regular Expression Denial of Service) protection., Test validation accepts valid strings., Test validation rejects non-strings., Test validation rejects overly long strings., Test validation rejects strings with too many spaces., Test validation rejects strings with too many dashes. (+2 more)

### Community 80 - "generic_table_tools Query Engine"
Cohesion: 0.17
Nodes (12): filter Intelligence-Builder Backref Discipline, consolidated_tools Module, filter/ Package Pipeline, generic_table_tools Query Engine, Intelligent Query Tools, filter_records Tool, pydantic Validation Dependency, ServiceNow Query Syntax Guide (+4 more)

### Community 81 - "Generic Tool Wrappers"
Cohesion: 0.11
Nodes (18): Generic Tool Wrappers, TABLE_CONFIGS Supported Tables, Tool Organization Document, Table Extensibility via TABLE_CONFIGS, find_similar Tool, search_records Tool, v3 Generic Wrapper Consolidation, Search and Query Flow Document (+10 more)

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

### Community 87 - "get_yesterday_range"
Cohesion: 0.33
Nodes (4): get_yesterday_range(), Get start and end of yesterday (same date for both). Returns: Tuple of…, Test yesterday range returns previous day for both., Test yesterday range across year boundary.

### Community 88 - "extract_keywords"
Cohesion: 0.31
Nodes (8): _extract_content_keywords(), extract_keywords(), _extract_record_numbers(), Extract relevant keywords from input text using lightweight regex patterns.…, Extract ServiceNow record numbers from text., Extract content keywords using basic text processing., Refine input text for search queries., refine_query()

### Community 89 - "TestDateFilterIntegration"
Cohesion: 0.33
Nodes (4): Integration tests for date filter building with validation., Test complete workflow: validate -> normalize -> build filter., Verify filter doesn't use JavaScript syntax., TestDateFilterIntegration

### Community 90 - "asyncio"
Cohesion: 0.12
Nodes (11): asyncio, Verify vtb_task works through generic filter (ServiceNow API path)., sys_updated_on is a DETAIL_FIELDS entry for incident; filter_records must pass…, Test search_records generic tool., Test get_record generic tool., Test find_similar generic tool., Test filter_records generic tool., TestFilterRecords (+3 more)

### Community 94 - "_table_of"
Cohesion: 0.40
Nodes (3): Table segment of a ServiceNow Table API URL., Table segment of each captured URL., _table_of()

### Community 96 - "manifest.json"
Cohesion: 0.17
Nodes (11): author, name, description, display_name, long_description, manifest_version, name, repository (+3 more)

### Community 97 - "retire_knowledge_article"
Cohesion: 0.12
Nodes (11): _get_kb_article_sys_id(), Return the article's sys_id, or None if no such article exists. None means…, Re-read the draft sys_id between publish attempts, best effort. ServiceNow…, Retire a knowledge article via the ServiceNow workflow endpoint. TABLES:…, _refresh_draft_sys_id(), retire_knowledge_article(), Decision (d): None means absent, so a failed read must NOT return None. The old…, Verify write ops use make_nws_request write path (not GET path). (+3 more)

### Community 98 - "TestCallerExclusions"
Cohesion: 0.17
Nodes (7): Test caller exclusion parsing., Test parsing known caller (logicmonitor)., Test parsing single sys_id., Test parsing comma-separated sys_ids., Test parsing already formatted exclusion., Test parsing empty input., TestCallerExclusions

### Community 99 - "TestEdgeCasesAndErrorHandling"
Cohesion: 0.14
Nodes (8): Test edge cases and error handling scenarios., Test ServiceNowQueryBuilder handles None inputs gracefully., Test ServiceNowQueryBuilder handles empty lists gracefully., Test priority filter validation with empty string., Test date range filter validation with empty string., Test result count validation with edge values., Test debug_query_construction handles None inputs., TestEdgeCasesAndErrorHandling

### Community 102 - "TestReadFailuresPropagate"
Cohesion: 0.24
Nodes (5): asyncio, Derived from the CODE, not from a list. The list was wrong once already. The…, The headline bug: a 30s deadline must never look like a missing record., Empty is success. Deciding it means not-found is the consumer's job., TestReadFailuresPropagate

### Community 103 - "test_pyproject_sync.py"
Cohesion: 0.20
Nodes (17): _load_build_mcpb(), _load_manifest(), _load_pyproject(), _local_top_level_names(), _main_version(), Path, Packaging-consistency tests for the .mcpb bundle sources. These guard the…, Every repo-local module a staged root file imports must itself be staged. The… (+9 more)

### Community 104 - "args"
Cohesion: 0.20
Nodes (10): args, command, server, entry_point, mcp_config, type, --directory, ${__dirname} (+2 more)

### Community 105 - "_ci_type_error"
Cohesion: 0.29
Nodes (6): _ci_type_error(), Return an error message if ci_type is not a usable cmdb_ci* table, else None.…, parametrize, The old bare prefix check accepted this; the shape check does not., re.match with `$` accepts one trailing newline; fullmatch does not., TestCiTypePolicy

### Community 106 - "constants.py"
Cohesion: 0.13
Nodes (12): Constants used throughout the ServiceNow MCP server., _get_task_sys_id(), Private task (vtb_task) CRUD. Read-failure contract (v4.4 Tier 0.3). A failed…, Get the sys_id for a task by its number, or None if no such task exists. None…, Typed read failures in the private-task tools (v4.4 Tier 0.3, PR D). The module…, TestReadFailureStillRaisesAtTheHelperBoundary, Test sys_id retrieval function., Test successful sys_id retrieval. (+4 more)

### Community 107 - "TestPaginationSortIntegration"
Cohesion: 0.20
Nodes (6): Test that _make_paginated_request injects sort order., Test that default sort order is injected into paginated requests., Test that a custom sort directive is respected., Test that sort is not injected when default_sort is empty., Test that an existing ORDERBY in the URL is not replaced., TestPaginationSortIntegration

### Community 109 - "FastMCP Server Core"
Cohesion: 0.22
Nodes (9): Architecture Overview Document, AuthMiddleware SSE Bearer, FastMCP Server Core, Stdout JSON-RPC Stderr Logs Invariant, tools.py Tool Registration, stdio and SSE Transport, SSE Auth Independent of ServiceNow OAuth, AuditMiddleware Structured Logging (+1 more)

### Community 112 - "Any"
Cohesion: 0.22
Nodes (5): Any, AsyncClient, Response, Make an authenticated request to ServiceNow API. Delegates to RequestExecutor;…, Test the OAuth connection by making a simple API call.

### Community 115 - "test_kb_article_tools.py"
Cohesion: 0.13
Nodes (11): _get_kb_article_meta(), Fetch sys_id + short_description in one GET — avoids a second round-trip in…, _unwrap_kb_write_response(), _write_kb_article(), Tests for kb_article_tools.py — KB article write path (update / publish /…, The shape a failed GET now arrives in for this module (v4.4 Tier 0.3)., An empty write response cannot establish that the write landed., TestGetKbArticleMeta (+3 more)

### Community 116 - "_verify_kb_published"
Cohesion: 0.31
Nodes (5): Return the published row for *article_number*, or None if not yet published.…, _verify_kb_published(), _verify_kb_published is the source of truth for publish success., None means "no Published row yet"; a failed read is not that. Conflating them…, TestVerifyKbPublished

### Community 117 - "test_vtb_task_tools.py"
Cohesion: 0.12
Nodes (16): _handle_http_error(), Any, HTTPStatusError, Map an HTTP error to the {"error": {code, message}} contract shape., Extract the inner result payload into the §3.1 write shape., _unwrap_write_response(), Extract the single-record write payload into the §3.1 write shape. Confirmed…, unwrap_write_response() (+8 more)

### Community 118 - "TestServiceNowOAuthExceptions"
Cohesion: 0.20
Nodes (6): Test custom exception classes., Test that OAuth error inherits from Exception., Test that AuthenticationError inherits from OAuthError., Test that ConnectionError inherits from OAuthError., Test that AuthorizationError inherits from OAuthError., TestServiceNowOAuthExceptions

### Community 124 - "ServiceNowQueryBuilder"
Cohesion: 0.11
Nodes (12): ServiceNow query-string builder. Static helpers that emit syntactically-correct…, Helper class for building ServiceNow queries with proper syntax., Build exclusion filter for multiple IDs using NOT EQUALS., ServiceNowQueryBuilder, Specific tests for ServiceNowQueryBuilder class., Set up test fixtures., Test QueryBuilder initialization., Test OR filter building. (+4 more)

### Community 125 - "TestTableFilterParams"
Cohesion: 0.25
Nodes (5): Test TableFilterParams model., Test creating params with filters., Test creating params with fields., Test creating empty params., TestTableFilterParams

### Community 126 - "TestOAuthClientExtended"
Cohesion: 0.39
Nodes (3): dict, patch, TestOAuthClientExtended

### Community 129 - "TestSLATokenBudgetConstants"
Cohesion: 0.25
Nodes (5): Lock budget constants — accidental relaxation should fail review., Curated 7-field view must be at most ~15% over standard ESSENTIAL list., Performance preset has 11 fields vs essential's 6; budget reflects that., A sys_id lookup must never need more than ~200 tokens (1 row)., TestSLATokenBudgetConstants

### Community 132 - "TestPrivateTaskTools"
Cohesion: 0.25
Nodes (5): Test updating an existing private task., Test private task tools with CRUD operations., Set up test fixtures., Test creating a new private task., TestPrivateTaskTools

### Community 138 - "client_id"
Cohesion: 0.33
Nodes (6): description, required, title, type, user_config, client_id

### Community 139 - "client_secret"
Cohesion: 0.33
Nodes (6): description, required, sensitive, title, type, client_secret

### Community 140 - "env"
Cohesion: 0.33
Nodes (6): MCP_TRANSPORT, SERVICENOW_AUTH_TYPE, SERVICENOW_CLIENT_ID, SERVICENOW_CLIENT_SECRET, SERVICENOW_INSTANCE, env

### Community 141 - "keywords"
Cohesion: 0.33
Nodes (6): keywords, cmdb, incident, itsm, knowledge-base, servicenow

### Community 145 - "test_cli.py"
Cohesion: 0.33
Nodes (5): Tests for CLI argument handling., --help should print usage and exit 0., --version should print version and exit 0., test_help_flag(), test_version_flag()

### Community 146 - "TestNewQueryResetRefusal"
Cohesion: 0.33
Nodes (3): `^NQ` discards every condition before it, so a scoped query becomes a table…, Why the check runs before the handlers rather than inside the encoder.…, TestNewQueryResetRefusal

### Community 147 - "Read-Failure Contract (ServiceNowRequestError)"
Cohesion: 0.50
Nodes (5): CMDB Probe Failure Semantics, Partial Read Keeps Rows, Read-Failure Contract (ServiceNowRequestError), Table_Tools/read_helpers.py, CMDB Tools (6)

### Community 149 - "servicenow_instance"
Cohesion: 0.40
Nodes (5): description, required, title, type, servicenow_instance

### Community 151 - "_reset_http_pool"
Cohesion: 0.40
Nodes (4): fixture, Shared pytest fixtures. The v4.2 connection-pooling refactor introduced a…, Drop the cached pooled client before and after each test., _reset_http_pool()

### Community 152 - "Bitbucket CI Pipeline"
Cohesion: 0.50
Nodes (4): Bitbucket CI Pipeline, pytest Coverage CI Step, SonarCloud Quality Scan, pytest Dev Test Stack

### Community 154 - "platforms"
Cohesion: 0.50
Nodes (4): compatibility, platforms, darwin, win32

### Community 159 - "TestUpdatePrivateTask"
Cohesion: 0.25
Nodes (5): Test update_private_task function with OAuth authentication., Test successful private task update., Test update fails without update data., Test update fails when task not found., TestUpdatePrivateTask

## Knowledge Gaps
- **88 isolated node(s):** `manifest_version`, `name`, `display_name`, `version`, `description` (+83 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ServiceNowRequestError` connect `ServiceNowRequestError` to `asyncio`, `generic_table_tools.py`, `ErrorCode`, `TestServiceNowAPI`, `make_nws_request`, `health_check`, `asyncio`, `kb_article_tools.py`, `error_response`, `KbDuplicateCheckInconclusive`, `TestUpdatePrivateTask`, `test_tool_response_contract.py`, `TokenStore`, `TestProbeFailuresAreNotAbsence`, `asyncio`, `asyncio`, `test_typed_read_cmdb_tools.py`, `_publish_with_verify`, `create_private_task`, `_prepare_task_create_data`, `update_private_task`, `update_knowledge_article`, `_write_private_task`, `retire_knowledge_article`, `_FakeOAuthClient`, `TestReadFailuresPropagate`, `constants.py`, `test_kb_article_tools.py`, `_verify_kb_published`, `test_vtb_task_tools.py`?**
  _High betweenness centrality (0.150) - this node is a cross-community bridge._
- **Why does `make_nws_request()` connect `make_nws_request` to `retire_knowledge_article`, `generic_table_tools.py`, `ServiceNowRequestError`, `test_tool_response_contract.py`, `asyncio`, `constants.py`, `_write_private_task`, `TestServiceNowAPI`, `test_query_value_encoding.py`, `test_kb_article_tools.py`, `_verify_kb_published`, `health_check`, `test_oauth_client_enhanced.py`, `get_ci_details`, `kb_article_tools.py`, `error_response`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Why does `ErrorCode` connect `ErrorCode` to `asyncio`, `generic_table_tools.py`, `ServiceNowRequestError`, `make_nws_request`, `health_check`, `asyncio`, `kb_article_tools.py`, `error_response`, `KbDuplicateCheckInconclusive`, `TestUpdatePrivateTask`, `test_tool_response_contract.py`, `TokenStore`, `TestProbeFailuresAreNotAbsence`, `asyncio`, `asyncio`, `test_typed_read_cmdb_tools.py`, `_publish_with_verify`, `create_private_task`, `_prepare_task_create_data`, `update_private_task`, `update_knowledge_article`, `_write_private_task`, `retire_knowledge_article`, `_FakeOAuthClient`, `TestReadFailuresPropagate`, `constants.py`, `test_kb_article_tools.py`, `_verify_kb_published`, `test_vtb_task_tools.py`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 59 inferred relationships involving `ServiceNowRequestError` (e.g. with `ServiceNowAuthenticationError` and `ServiceNowAuthorizationError`) actually correct?**
  _`ServiceNowRequestError` has 59 INFERRED edges - model-reasoned connections that need verification._
- **Are the 59 inferred relationships involving `ErrorCode` (e.g. with `QueryValueError` and `ServiceNowAuthenticationError`) actually correct?**
  _`ErrorCode` has 59 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `ServiceNowOAuthClient` (e.g. with `RequestExecutor` and `TokenStore`) actually correct?**
  _`ServiceNowOAuthClient` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `manifest_version`, `name`, `display_name` to the rest of the system?**
  _88 weakly-connected nodes found - possible documentation gaps or missing edges._