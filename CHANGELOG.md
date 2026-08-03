# Changelog

All notable changes to the Personal MCP ServiceNow project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.3.0] - 2026-07-14

Backfilled 2026-08-03 from the 32 commits between the 4.1.0 work and the `v4.3.0` tag.

**On the missing 4.2.0:** there isn't one. The version string went `4.1.0` → `4.3.0` in a single
bump (the packaging commit), and no `v4.1.0` or `v4.2.0` tag was ever cut. The performance and
token work planned as "4.2" shipped inside 4.3.0 and is recorded below under its own heading
rather than as a fabricated 4.2.0 release. Retroactive tags were deliberately not created.

### Added

- **Claude Desktop Extension packaging** — the server builds as a `.mcpb` bundle. Version is
  3-way synced across `pyproject.toml`, `manifest.json` and `personal_mcp_servicenow_main.py`.
- **SSE transport authentication** — `MCP_SSE_AUTH_TOKEN` shared-secret bearer check in
  `auth_middleware.py`. SSE startup refuses to run without it unless `MCP_ALLOW_INSECURE_SSE`
  is set explicitly. Rejection messages never reveal whether a token was missing, malformed or
  wrong.
- **Log hardening** — URLs in stderr diagnostics are reduced to path plus a stable query hash,
  so a `sysparm_query` never reaches the logs.
- E2E MCP test prompts (`docs/E2E_TEST_PROMPTS.md`).

### Performance and token work (planned as 4.2, shipped in 4.3.0)

- **Pooled HTTP client** — one process-wide keep-alive `httpx.AsyncClient` (`oauth/http_pool.py`)
  shared by the request executor, the 401-retry and the token fetch. Previously every request
  paid a fresh TLS handshake.
- **One query instead of N** — `query_table_by_text` builds a single OR-combined LIKE query
  across all keywords (`short_descriptionLIKEa^ORshort_descriptionLIKEb`) instead of one serial
  request per keyword. Fewer round-trips *and* better recall: the old loop only ever matched a
  single keyword.
- **Concurrent CMDB probes** — `get_ci_details` probes candidate CI tables concurrently (bounded)
  instead of one at a time, preserving most-specific-first priority.
- **Debug payload opt-in** — `query_table_intelligently(debug=False)` no longer recomputes the
  debug extras on the default path.
- **Trimmed tool docstrings** — roughly 2k characters per session removed from the registered
  tool descriptions.
- Pre-compiled hot-path regexes; shared write-response helpers (`write_helpers.py`) for the KB
  and VTB paths; module-level condition-handler registry; dead helpers and a redundant
  `load_dotenv()` removed.

### Fixed

- **`LIKE`, not `CONTAINS`, in encoded queries.** `CONTAINS` is a GlideRecord scripting operator
  and is silently ignored inside a `sysparm_query` — it returned zero rows with no error. Also
  surfaces reference-field hints: `assignment_group`, `assigned_to`, `caller_id`, `cmdb_ci` and
  friends store sys_ids, so a bare display-value match silently matched nothing.
- **CMDB: valid CI types no longer rejected.** `find_cis_by_type` validated against a static
  table list that drifted from real instances and refused common classes such as
  `cmdb_ci_server`.
- **CMDB: user values percent-encoded** in CI search queries, so `#`, `+`, `%` or `?` in a name
  or location can no longer corrupt the query.
- **MCP parameter coercion** — some clients stringify and double-encode flat `List`/`Dict`
  parameters; `param_coercion.py` peels the layers at the tool boundary.
- **KB publish timeouts** — `anyio` `TimeoutError` is caught on the publish fire-timeout instead
  of escaping as an unhandled error; KB writes are now bounded, and stale pooled connections
  expire.
- Ticket detail field sets gain `sys_updated_on` and `opened_at`.
- Security sanitization sweep, P0 through P3, plus a linter-driven fix pass.
- Stale docstrings and a wrong date-explanation branch in the NL query path.

### Removed

- Nuitka binary builds dropped from the release workflow — `.mcpb` is the distribution path.
- graphify cache artifacts are no longer tracked.

## [4.1.0] - 2026-06-11

### BREAKING CHANGES

#### v4.0 backwards-compat shims deleted

The four re-export shim modules left in place for one release cycle are now removed:
`service_now_api_oauth.py`, `oauth_client.py`, `query_validation.py`, `query_intelligence.py`.

**Migration — import from the canonical packages directly:**
- `from service_now_api_oauth import make_nws_request, NWS_API_BASE, test_oauth_connection, get_auth_info` → `from http_layer import ...`
- `from oauth_client import ServiceNowOAuthClient, get_oauth_client, make_oauth_request` → `from oauth import ...`
- `from query_validation import ServiceNowQueryBuilder, validate_query_filters, ...` → `from filter import ...`
- `from query_intelligence import QueryIntelligence, get_filter_templates, ...` → `from filter import ...`

The process-wide OAuth singleton (`_oauth_client`, `get_oauth_client`, `make_oauth_request`) moved
from the deleted `oauth_client.py` to `oauth/singleton.py` (re-exported via `oauth/__init__.py`).
`http_layer/request_dispatcher.py` now imports the singleton at module level; the `sys.modules`-based
`_resolve_oauth_binding` indirection was removed.

**Test patch-target migration:**
- `patch("service_now_api_oauth.make_oauth_request")` → `patch("http_layer.request_dispatcher.make_oauth_request")`
- `patch("service_now_api_oauth.get_oauth_client")` → `patch("http_layer.request_dispatcher.get_oauth_client")`
- `patch("oauth_client.httpx.AsyncClient")` → `patch("oauth.singleton.httpx.AsyncClient")`
- `oauth_client._oauth_client = None` → `oauth.singleton._oauth_client = None`
- `patch("query_intelligence.*")` / `patch("query_validation.*")` → `patch("filter.intelligence.*")` / `patch("filter.validator.*")`

No production behaviour change: the GET read path (encoding + perf params + display flattening) and the
write path (bypass + `raise_for_status`) are unchanged. Full suite: 662 passed, 5 skipped (pre-existing).

#### SmartQueryParams removed (Sprint 1b)

`filter.SmartQueryParams` deleted — dead code. Defined and exported since v4.0 Sprint 1 but never
instantiated anywhere (zero call sites, zero tests). The NL query boundary is served by
`IntelligentQueryParams` in `Table_Tools/intelligent_query_tools.py`; the field-value boundary by
`filter.TableFilterParams`. The Sprint 1b "merge vs keep" question resolved to neither — the two
models address different concerns, and the NL one was simply unused.

## [4.0.0] - 2026-05-20

### BREAKING CHANGES

Architectural refactor surfaced by a graphify analysis of god-node clusters in the v3 codebase. Three sprints, each independently mergeable. Full migration guide in `MIGRATION_v3_to_v4.md`.

#### SLA tool consolidation (Sprint 2)

8 SLA tools collapsed into 3 new tools. Total tool count: **37 -> 32**.

**Removed (8 tools):**
- `get_slas_for_task`
- `get_breaching_slas`
- `get_breached_slas`
- `get_slas_by_stage`
- `get_active_slas`
- `get_sla_performance_summary`
- `get_recent_breached_slas`
- `get_critical_sla_status`

**Added (3 tools):**
- `query_slas_by_task(task_number)` — replaces `get_slas_for_task`
- `query_slas_by_status(status, days?, threshold_minutes?, stage?, extra_filters?)` — preset dispatcher for the 6 status-based tools. Status enum: `"active"`, `"breached"`, `"breaching"`, `"critical"`, `"by_stage"`, `"performance"`.
- `query_slas_custom(filters, fields?, days?)` — escape hatch. Defaults to `ESSENTIAL_FIELDS["task_sla"]` so it never returns all columns by default.

**Unchanged:**
- `similar_slas_for_text(text)`
- `get_sla_details(sys_id)` — **bug fix** included (see below)

#### get_sla_details v3 bug fix (Sprint 2)

v3 `get_sla_details(sys_id)` delegated to `get_record_details("task_sla", sys_id)` which built a `number={sys_id}` filter. The `task_sla` table has no `number` field, so the filter was silently ignored and the call returned the full default page — **10,000 rows / ~1.2 million tokens** — instead of the single record. v4 routes via `sys_id={sys_id}` directly, returning the single record (~69 tokens). **99.99% token reduction** for that tool.

### Added

#### Filter pipeline package (Sprint 1)

New `filter/` package consolidates filter construction, validation, NL parsing, and explanation:
- `filter/builder.py` — `ServiceNowQueryBuilder`
- `filter/validator.py` — `validate_query_filters`, `validate_and_correct_filters` (new), helpers
- `filter/intelligence.py` — `QueryIntelligence` (NL → filter, no backref to builder)
- `filter/explainer.py` — `QueryExplainer`, `explain_existing_filter`
- `filter/models.py` — `TableFilterParams`, `SmartQueryParams`, `QueryValidationResult`

#### HTTP layer package (Sprint 3)

New `http_layer/` package splits the v3 monolithic `make_nws_request`:
- `http_layer/url_builder.py` — `ensure_query_encoded`, `add_default_params` (GET-only)
- `http_layer/response_parser.py` — display-value flattening (GET-only)
- `http_layer/request_dispatcher.py` — `make_nws_request` orchestrator (~30 lines)

#### OAuth package (Sprint 3)

New `oauth/` package splits the v3 `ServiceNowOAuthClient`:
- `oauth/token_store.py` — token cache + refresh + injectable fetcher
- `oauth/request_executor.py` — authenticated HTTP + 401 retry
- `oauth/client.py` — `ServiceNowOAuthClient` façade
- `oauth/exceptions.py` — `ServiceNowOAuthError` + 3 subclasses

#### Token-optimization infrastructure

- `scripts/capture_sla_token_baseline.py` + `scripts/compare_sla_token_baseline.py` — live ServiceNow baseline and diff runners for SLA tools.
- `scripts/capture_read_path_baseline.py` — read-path baseline across all 7 tables. Validates four token-optimization URL invariants (`sysparm_exclude_reference_link`, `sysparm_no_count`, `sysparm_display_value`, sort order).
- `tests/test_token_footprint.py` — offline budget regression suite (`tiktoken` cl100k_base) for SLA tools.
- `tests/test_http_layer.py` — 13 tests locking the GET vs write divergence. **Three critical negative tests** prove POST/PATCH bypass the read-path mutations.

### Deprecated (deleted in v4.1)

Backwards-compat shims retain the v3 import paths and test-patch targets:
- `query_validation.py` — re-exports from `filter/`
- `query_intelligence.py` — re-exports from `filter/`
- `service_now_api_oauth.py` — re-exports from `http_layer/` + keeps `make_oauth_request` / `get_oauth_client` patch targets
- `oauth_client.py` — canonical home of the module-level singleton (`_oauth_client`, `get_oauth_client`, `make_oauth_request`) + `httpx` re-export

### Architecture

`filter/intelligence.py` no longer imports from `filter/builder.py`. Auto-correction logic that needs `ServiceNowQueryBuilder` lives in `filter/validator.validate_and_correct_filters` — the only module allowed to bridge NL parsing → query construction.

### Metrics

- Tool count: 32 (down from 37)
- Tests: 575 passing (up from 537)
- Overall coverage: ~83%
- `filter/` coverage: 98.16%
- `oauth/` + `http_layer/` coverage: 92.98%

---

## [2.0.0] - 2025-01-14

### 🚨 BREAKING CHANGES

This is a major architectural overhaul with significant breaking changes. See CHANGELOG entries below for v1.x → v2.0 migration notes.

#### **Deleted Files (Breaking Changes)**

- **REMOVED**: `Table_Tools/incident_tools.py` - Use `consolidated_tools.py` functions instead
- **REMOVED**: `Table_Tools/change_tools.py` - Use `consolidated_tools.py` functions instead
- **REMOVED**: `Table_Tools/kb_tools.py` - Use `consolidated_tools.py` functions instead
- **REMOVED**: `Table_Tools/ur_tools.py` - Use `consolidated_tools.py` functions instead

#### **Authentication Changes**

- **OAuth 2.0 Only**: Removed basic authentication fallback for enhanced security
- **Required Environment Variables**: `SERVICENOW_CLIENT_ID` and `SERVICENOW_CLIENT_SECRET` now mandatory

#### **API Changes**

- **Tool Registration**: Consolidated from 25+ individual tools to unified approach
- **Function Names**: All MCP tools now use snake_case naming convention
- **Return Types**: Standardized return formats across all functions

### 🚀 NEW FEATURES

#### **AI-Powered Natural Language Queries**

- **Intelligent Search**: `intelligent_search()` - Natural language to ServiceNow queries
- **Query Explanation**: `explain_servicenow_filters()` - AI explanations of what filters will do
- **Smart Filter Building**: `build_smart_servicenow_filter()` - Convert natural language to ServiceNow syntax
- **Predefined Templates**: `get_servicenow_filter_templates()` - Ready-to-use filter patterns
- **Query Examples**: `get_query_examples()` - Natural language query examples

#### **Enhanced Generic Table Operations**

- **Universal Functions**: `query_table_intelligently()` - AI-powered queries for any table
- **Advanced Filtering**: `query_table_with_filters()` with intelligent natural language parsing
- **Priority Queries**: `get_records_by_priority()` - Generic priority filtering for any table
- **Generic CRUD**: Complete Create, Read, Update operations for supported tables

#### **Natural Language Intelligence**

- **Date Range Parsing**:
  - "Week 35 2025" → Proper BETWEEN syntax with calculated dates
  - "August 25-31, 2025" → Month range parsing
  - "2025-08-25 to 2025-08-31" → ISO date range
- **Priority Parsing**:
  - "1,2" → "priority=1^ORpriority=2" (proper OR syntax)
  - "P1,P2" → "priority=1^ORpriority=2" (P-notation conversion)
- **Caller Exclusion Parsing**:
  - "logicmonitor" → Automatic sys_id lookup and exclusion

### 🛡️ SECURITY ENHANCEMENTS

#### **ReDoS Protection**

- **Input Validation**: Pre-validation of all text inputs to prevent malicious patterns
- **Timeout Protection**: `timeout_protection()` context manager for regex operations
- **Length Limits**: Automatic rejection of overly long input strings

#### **Enhanced Authentication**

- **OAuth 2.0 Exclusive**: Improved security through OAuth-only approach
- **Automatic Token Refresh**: Intelligent token management and expiration handling

### ⚡ PERFORMANCE IMPROVEMENTS

#### **Optimized Architecture**

- **Code Reduction**: Net reduction of 142 lines while adding significant functionality
- **Pagination**: `_make_paginated_request()` with configurable limits and complete result retrieval
- **Smart Caching**: Automatic token caching and reuse
- **Query Optimization**: Intelligent query building with handler registry pattern

#### **Enhanced API Integration**

- **URL Encoding Preservation**: Maintains ServiceNow JavaScript functions during encoding
- **Proper OR Syntax**: Correct ServiceNow query syntax for multiple priorities
- **JavaScript Date Functions**: Perfect BETWEEN syntax with ServiceNow date functions

### 📚 DOCUMENTATION & TESTING

#### **Comprehensive Documentation**

- **Architecture Diagrams**: Complete system architecture documentation
- **AI Intelligence Flow**: Detailed documentation of natural language processing
- **Tool Organization**: Clear mapping of all available tools and capabilities
- **API Examples**: Extensive examples of natural language queries

#### **Enhanced Testing**

- **Consolidated Tool Tests**: `Testing/test_consolidated_tools.py` with 417 new lines
- **Query Intelligence Tests**: Enhanced `Testing/test_query_intelligence.py`
- **Comprehensive Validation**: `Testing/test_filtering_fixes.py` with 100% success rate
- **CMDB Testing**: Updated `Testing/test_cmdb_tools.py`

### 🏗️ ARCHITECTURAL IMPROVEMENTS

#### **Code Quality Enhancements**

- **Cognitive Complexity Reduction**: All functions now under complexity limit ≤15
- **Helper Function Extraction**: Modular design with single-responsibility functions
- **Constants Consolidation**: Enhanced `constants.py` with centralized configuration
- **Error Message Standardization**: All duplicated literals moved to constants

#### **Maintainability**

- **Single Responsibility**: Clear separation of concerns across modules
- **Enhanced Testability**: Individual components can be tested independently
- **Modular Design**: Reusable functions with consistent interfaces

### 🔧 INFRASTRUCTURE

#### **New Dependencies**

- Enhanced `requirements.txt` with AI/ML processing capabilities
- Natural language processing support
- Advanced regex processing with safety features

#### **Tool Registration Optimization**

- **Streamlined Registration**: Unified tool registration in `tools.py`
- **Intelligent Query Tools**: 5 new AI-powered MCP tools
- **Zero Functional Regression**: All existing functionality maintained

### 📈 METRICS

- **Lines Added**: 2,781
- **Lines Removed**: 1,146
- **Net Change**: +1,635 lines of enhanced functionality
- **Files Modified**: 29
- **Files Deleted**: 4 (consolidated into generic functions)
- **Files Created**: 7 (documentation, tests, new features)

### 🔄 MIGRATION GUIDE

See the v2.0 section above for migration notes from v1.x to v2.0.

### 🙏 ACKNOWLEDGMENTS

This release represents one of the largest architectural changes in the project's history, implementing cutting-edge AI integration while maintaining zero functional regression.

---

## [1.0.0] - Previous Release

Previous release information maintained for historical reference.
