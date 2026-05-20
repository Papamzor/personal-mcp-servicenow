# Architecture Refactor Plan

Status: planning · Source: graphify analysis (2026-05-20) · Target release: v3.1

## Why

Graphify run on commit 9de7894 surfaced three god-node clusters that violate Single Responsibility, inflate the MCP tool count, and produce duplicated filter logic. The full report lives at `graphify-out/GRAPH_REPORT.md`. This document captures the three refactors as independently-shippable sprints.

| Sprint | Theme | God nodes removed | Tool count delta | Risk |
|--------|-------|--------------------|------------------|------|
| 1 | Filter pipeline consolidation | 4 (QueryValidationResult, QueryIntelligence, TableFilterParams, ServiceNowQueryBuilder) | 0 | Medium — touches imports across 4 modules |
| 2 | SLA tool collapse | 1 (TableFilterParams cross-community bridge weakens) | -5 (10 → 5 SLA tools, 37 → 32 total) | Low — internal dispatch only |
| 3 | OAuth + HTTP layer split | 2 (ServiceNowOAuthClient, make_nws_request) | 0 | Medium — touches every read+write code path |

Sprints are independent. Recommended order: 2 → 1 → 3 (Sprint 2 is lowest risk and proves the refactor discipline; Sprint 1 lays groundwork for Sprint 3 by clarifying what `make_nws_request` should remain responsible for).

---

## Sprint 1 — Filter pipeline consolidation

### Problem

Three modules and three Pydantic models implement one logical concern (build + validate + explain a ServiceNow filter):

- `query_validation.py` — `ServiceNowQueryBuilder` (static builders), `QueryValidationResult`, `validate_*_filter()` funcs
- `query_intelligence.py` — `QueryIntelligence` (NL parsing), `QueryExplainer` (only reachable via `explain_existing_filter()` wrapper), `build_smart_filter`, `_validate_and_improve_filters`
- `Table_Tools/generic_table_tools.py` — `TableFilterParams`, `SmartQueryParams` (Pydantic models trapped inside the query engine module)

Cross-module leaks:
- `query_intelligence.py:337` reaches back into `query_validation.ServiceNowQueryBuilder.build_priority_or_filter` — intelligence layer depends on validation module for construction
- `QueryExplainer` class hidden behind a wrapper function — symptom of unclear encapsulation
- Stale tests in `test-results.xml` reference removed methods (`build_not_equals_filter`, `build_or_filter`) on `ServiceNowQueryBuilder` — schema drift

Graph community map: c17 (Query Validation Models), c23 (TableFilterParams + SLA), c32 (Smart Filter Builder), c41 (ServiceNowQueryBuilder), c113 (validate funcs) all overlap.

### Target structure

```
filter/
  __init__.py          # public API: re-exports
  models.py            # TableFilterParams, SmartQueryParams, QueryValidationResult
  builder.py           # ServiceNowQueryBuilder (was in query_validation.py)
  validator.py         # validate_query_filters, validate_priority_filter, validate_date_range_filter
  intelligence.py      # QueryIntelligence (NL parse, no backref to builder)
  explainer.py         # QueryExplainer + explain_existing_filter wrapper
```

### Steps

1. Create `filter/` package skeleton with empty `__init__.py`.
2. Move 3 Pydantic models (`TableFilterParams`, `SmartQueryParams`, `QueryValidationResult`) into `filter/models.py`. Keep field signatures identical.
3. Move `ServiceNowQueryBuilder` static class from `query_validation.py` → `filter/builder.py`.
4. Move validator funcs (`validate_query_filters`, `validate_priority_filter`, `validate_date_range_filter`, helpers) → `filter/validator.py`.
5. Move `QueryIntelligence` class → `filter/intelligence.py`. Break backref to builder: validator should apply corrections, not parser.
6. Move `QueryExplainer` + `explain_existing_filter` → `filter/explainer.py`.
7. In `filter/__init__.py`, re-export the public API: `TableFilterParams`, `SmartQueryParams`, `QueryValidationResult`, `QueryIntelligence`, `validate_query_filters`, `build_smart_filter`, `explain_existing_filter`, `ServiceNowQueryBuilder`.
8. Update imports in `Table_Tools/generic_table_tools.py`, `Table_Tools/consolidated_tools.py`, `Table_Tools/intelligent_query_tools.py`, all CMDB + VTB tool modules.
9. Replace old module files (`query_validation.py`, `query_intelligence.py`) with thin re-export shims for one release cycle, then delete in v3.2.
10. Fix stale tests: either restore `build_not_equals_filter` + `build_or_filter` methods or delete the tests that reference them.
11. Run full test suite + coverage. Target: no coverage regression (currently ≥30% on new lines).

### Acceptance

- `query_validation.py` and `query_intelligence.py` either deleted or contain only `from filter.X import *` lines
- No backref from `filter/intelligence.py` to `filter/builder.py`
- Pydantic models import path: `from filter.models import TableFilterParams`
- Stale `ServiceNowQueryBuilder` test failures removed from `test-results.xml`
- Graphify shows c17/c23/c32/c41/c113 collapsed into one community in `filter/`
- **Token gate**: response token counts for `search_records`, `filter_records`, `get_record_summary`, `get_priority_incidents`, and `explain_existing_filter` are ≤ baseline (no regression). `ESSENTIAL_FIELDS` / `DETAIL_FIELDS` allowlists still applied at every read entry point.

### Out of scope

- Renaming `ServiceNowQueryBuilder` — keep name, only relocate
- Removing `SmartQueryParams` even if redundant with `TableFilterParams` — defer to Sprint 1b
- Touching `Table_Tools/generic_table_tools.py` internals beyond import updates

---

## Sprint 2 — SLA tool collapse

### Problem

`Table_Tools/consolidated_tools.py:311-394` exposes 10 SLA-related MCP tools (registered at `tools.py:14-16, 48-50`). 8 of them are parameterized variants over the same code path (`query_table_with_filters("task_sla", TableFilterParams(filters=...))`). Redundancies:

- `get_breached_slas(days=7)` and `get_recent_breached_slas(days=1)` — identical filter shape, only default differs
- `get_breaching_slas(60)` is a strict subset of `get_active_slas` with extra constraints
- `get_critical_sla_status()` is a hardcoded preset of `get_active_slas` with priority + percentage thresholds

CLAUDE.md notes "37 tools" — bloated MCP discoverability surface for LLM clients.

Two SLA tools use distinct code paths and stay separate:
- `similar_slas_for_text(text)` — text search via `query_table_by_text`
- `get_sla_details(sys_id)` — sys_id lookup via `get_record_details` (**v3.0 bug — see below**)

**v3.0 bug discovered during baseline capture (2026-05-20):**
`get_sla_details(sys_id)` delegates to `get_record_details("task_sla", sys_id)` which builds a `number={sys_id}` filter. The `task_sla` table has no `number` field (per CLAUDE.md), so ServiceNow silently ignores the filter and returns the full default page — 10,000 rows / ~1.2M tokens. A correctly-scoped `sys_id={sys_id}` lookup returns 1 row / ~69 tokens (99.99% reduction). Sprint 2 must fix this when replacing the tool: route through `query_table_with_filters("task_sla", TableFilterParams(filters={"sys_id": sla_sys_id}))` or equivalent.

### Target structure

5 SLA tools instead of 10:

| Tool | Replaces | Filter shape |
|------|----------|--------------|
| `similar_slas_for_text(text)` | — (unchanged) | text search path |
| `get_sla_details(sys_id)` | — (unchanged) | sys_id path |
| `query_slas_by_task(task_number)` | `get_slas_for_task` (rename) | `{task.number: X}` |
| `query_slas_by_status(status, days?, threshold_minutes?, stage?, extra_filters?)` | `get_breaching_slas`, `get_breached_slas`, `get_slas_by_stage`, `get_active_slas`, `get_recent_breached_slas`, `get_critical_sla_status` | preset enum dispatch |
| `query_slas_custom(filters, fields?, days?)` | `get_sla_performance_summary` + escape hatch | arbitrary filter dict |

`status` enum values: `"active" \| "breached" \| "breaching" \| "critical" \| "by_stage"`. Internal dispatcher builds the appropriate filter dict + invokes `query_table_with_filters("task_sla", params)`.

### Steps

1. Add three new tools in `Table_Tools/consolidated_tools.py`: `query_slas_by_task`, `query_slas_by_status`, `query_slas_custom`. Internally call existing helpers OR inline the filter-dict construction.
2. Add `_dispatch_sla_status_filter(status, days, threshold_minutes, stage, extra_filters)` helper that returns the right filter dict per status enum value.
3. Update `tools.py` import list: remove `get_breaching_slas, get_breached_slas, get_slas_by_stage, get_active_slas, get_sla_performance_summary, get_recent_breached_slas, get_critical_sla_status, get_slas_for_task` from both the import line (14-16) and the registration list (48-50).
4. Add new tools to the import + registration: `query_slas_by_task, query_slas_by_status, query_slas_custom`.
5. Delete the 8 collapsed functions from `consolidated_tools.py`.
6. Migrate tests in `tests/test_consolidated_tools.py` — each old `get_*_slas` test rewritten to call `query_slas_by_status(status=...)` with matching enum value. Assert filter dict equivalence.
7. Update `CLAUDE.md` tool inventory table (currently shows 37 tools).
8. Update `Diagrams & Documentation/01-architecture-overview.md` if it lists SLA tools.

### Acceptance

- Tool count in `tools.py` registration drops from 37 to 32
- All previously-failing SLA scenarios (breaching, breached, critical, etc.) still callable via `query_slas_by_status(status=...)`
- No filter-dict shape changes — same ServiceNow API queries emitted
- Tests in `test_consolidated_tools.py` exercise each enum value of `status`
- **Token gate (baseline + per-call)**:
  - Establish `v4.0/token_baseline.json` for the 10 v3.x SLA tools before deleting any.
  - `query_slas_by_status(status="critical")` returns same 7-field curated list as old `get_critical_sla_status()` — assert in unit test.
  - `query_slas_by_status(status="performance" | "by_stage" | ...)` matches old field sets per status preset.
  - `query_slas_custom(filters, fields=None)` defaults `fields` to `ESSENTIAL_FIELDS["task_sla"]` — do not return all columns by default.
  - `tests/test_token_footprint.py` introduced and wired into CI as soft gate.

### Out of scope

- Dropping `similar_slas_for_text` or `get_sla_details` — keep distinct code paths
- Renaming `task_sla` table or changing field names
- Touching priority-incident tooling (Sprint 1 scope)

---

## Sprint 3 — OAuth + HTTP layer split

### Problem

Two highest-betweenness nodes in the graph:

- `make_nws_request()` (`service_now_api_oauth.py:69-98`) — betweenness 0.217. Bridges OAuth HTTP Layer (c3), Table Query Engine (c8), and 3 other communities. Mixes URL building + response transformation + GET/write dispatch in one module.
- `ServiceNowOAuthClient` (`oauth_client.py:31-211`) — 66 edges. Mixes config validation + basic auth + token lifecycle + bearer headers + request execution + retry policy + connection test.

CLAUDE.md write-path comment confirms intentional reuse of `make_nws_request` for non-GET methods — single function dispatches read vs write, blurring layer boundaries.

### Target structure

```
http_layer/
  __init__.py
  url_builder.py        # _ensure_query_encoded, _add_default_params
  response_parser.py    # _extract_field_value, _process_item_dict, _extract_display_values
  request_dispatcher.py # make_nws_request (thin orchestrator)

oauth/
  __init__.py
  exceptions.py         # ServiceNowOAuthError, AuthenticationError, ConnectionError, AuthorizationError
  token_store.py        # token cache + request + lock + lifecycle
  auth_headers.py       # basic auth + bearer headers
  request_executor.py   # make_authenticated_request + retry on 401
  client.py             # ServiceNowOAuthClient = orchestrator façade (composes the 3 above)
  singleton.py          # get_oauth_client, make_oauth_request
```

The `ServiceNowOAuthClient` class remains in `oauth/client.py` as a façade that composes `TokenStore`, `AuthHeaderProvider`, and `RequestExecutor`. This preserves the public API and lets existing tests keep patching `ServiceNowOAuthClient.*` methods. Internally each subsystem is small and unit-testable in isolation.

### Steps

1. Create `oauth/` package. Move 4 exception classes → `oauth/exceptions.py`.
2. Create `oauth/token_store.py` with `TokenStore` class containing `_access_token`, `_token_expires_at`, `_token_lock`, `_request_access_token`, `_get_valid_token`, `_clear_token_cache`. Inject `instance_url`, `client_id`, `client_secret` via constructor.
3. Create `oauth/auth_headers.py` with `AuthHeaderProvider` class. Depends on `TokenStore`. Methods: `get_basic_auth_header()`, `get_bearer_headers()` (was `get_auth_headers`).
4. Create `oauth/request_executor.py` with `RequestExecutor` class. Depends on `AuthHeaderProvider`. Methods: `make_authenticated_request(method, url, raise_for_status, **kwargs)`, `_retry_with_fresh_token`, `_process_response`.
5. Refactor `ServiceNowOAuthClient` in `oauth/client.py` to a thin facade: `__init__` validates env vars, instantiates `TokenStore` → `AuthHeaderProvider` → `RequestExecutor`, exposes `make_authenticated_request`, `test_connection`, `get_auth_headers` as delegate methods. Existing call sites unchanged.
6. Move `get_oauth_client` + `make_oauth_request` → `oauth/singleton.py`. Old import path `from oauth_client import get_oauth_client` continues to work via thin shim.
7. Create `http_layer/` package. Move `_ensure_query_encoded`, `_add_default_params` → `http_layer/url_builder.py`.
8. Move `_extract_field_value`, `_process_item_dict`, `_extract_display_values` → `http_layer/response_parser.py`.
9. Move `make_nws_request` → `http_layer/request_dispatcher.py`. Function shrinks to ~15 lines: dispatch on `method`, GET branch calls `url_builder` + `response_parser`, write branch delegates directly to `oauth.singleton.get_oauth_client()`.
10. `service_now_api_oauth.py` becomes a re-export shim: `from http_layer.request_dispatcher import make_nws_request; from http_layer import test_oauth_connection, get_auth_info`. Same public API.
11. Update imports across all consumers: `Table_Tools/generic_table_tools.py`, `Table_Tools/vtb_task_tools.py`, all read paths. Existing `from service_now_api_oauth import make_nws_request` keeps working via shim.
12. Add unit tests for `TokenStore`, `AuthHeaderProvider`, `RequestExecutor` in isolation. Mock `httpx.AsyncClient` at the subsystem boundary.
13. Verify existing 401-retry behaviour still triggers via integration test.
14. Update CLAUDE.md architecture diagram (currently shows `service_now_api_oauth.py → oauth_client.py → httpx`).

### Acceptance

- `oauth_client.py` and `service_now_api_oauth.py` are ≤ 30-line shims OR deleted (with shim in `__init__.py`)
- Each subsystem (`TokenStore`, `AuthHeaderProvider`, `RequestExecutor`) testable in isolation without instantiating `ServiceNowOAuthClient`
- 401-retry flow still works end-to-end (test against a mock 401 response)
- No call site changes for read path: `make_nws_request(url)` signature unchanged
- No call site changes for write path: `make_nws_request(url, method='POST', json_data=...)` signature unchanged
- Graphify shows `ServiceNowOAuthClient` betweenness < 0.10 after refactor
- **Token gate (highest risk sprint)**:
  - GET path still applies `sysparm_exclude_reference_link=true`, `sysparm_no_count=true`, `sysparm_display_value=true` via `http_layer/url_builder.py`. Verify via outgoing-URL assertion in unit test.
  - GET path still calls `_extract_display_values` after response. Verify via response-shape assertion in unit test.
  - Write path (POST/PATCH/DELETE) does NOT call `_add_default_params` or `_extract_display_values`. Add explicit negative unit test — invoke `make_nws_request(url, method='POST', json_data={...})` and assert URL is unchanged + response is raw.
  - Run full token-baseline regression battery; every read response token count must be ≤ pre-Sprint-3 baseline. Zero regressions tolerated — this sprint moves the most token-critical functions.

### Out of scope

- Switching from `httpx.AsyncClient(verify=True)` to a shared client (perf optimization)
- Adding new auth flows (only OAuth 2.0 client credentials supported in v3.x)
- Moving exception handling out of `RequestExecutor` (status → domain error mapping stays inside subsystem)

---

## Cross-cutting concerns

### Token-optimization invariant (non-negotiable)

ServiceNow MCP responses flow directly into the LLM client's context window. Every refactor must preserve or improve the current per-call token footprint. This is the single hardest constraint on the release.

**Existing optimizations that must stay intact:**

| Optimization | Where | What it does | Risk surface |
|--------------|-------|--------------|--------------|
| `sysparm_exclude_reference_link=true` | `_add_default_params()` in `service_now_api_oauth.py` | Strips `link` URLs from every reference field (largest single saving) | Sprint 3 (function relocates) |
| `sysparm_no_count=true` | `_add_default_params()` | Skips SELECT COUNT, avoids count metadata in response | Sprint 3 |
| `sysparm_display_value=true` + display flattening | `_extract_display_values()` | Replaces `{display_value: X, value: Y}` dicts with scalars | Sprint 3 |
| Per-table field allowlists | `ESSENTIAL_FIELDS` / `DETAIL_FIELDS` in `constants.py` | Limits returned fields per tool path (list vs detail views) | Sprints 1, 2 |
| Category exclusion filtering | `_apply_incident_category_filter()`, `_apply_sc_catalog_filter()` | Drops irrelevant incident/RITM categories at query time | Sprint 1 |
| Deterministic sort + paginated fetch | `_make_paginated_request()` | Avoids over-fetching; sort prevents duplicate rows across pages | Sprint 1 |

**Per-sprint token gates (must pass before PR merge into `release/v4.0`):**

1. **Baseline capture** — before Sprint 2 starts, record token counts for a fixed query battery against the live ServiceNow instance: one query per supported table, both list view and detail view, plus the 10 SLA tools. Persist results to `v4.0/token_baseline.json` (gitignored — use `-f`).
2. **Per-sprint regression check** — at the end of each sprint, re-run the same query battery. Assert: every call's response token count is ≤ baseline + 0% (no growth). Persist the diff to the sprint PR description.
3. **Sprint 2 specific** — `query_slas_by_status(status="critical")` must return the same field set as the old `get_critical_sla_status()` (curated 7-field list). `query_slas_custom(filters)` MUST default to `ESSENTIAL_FIELDS` for `task_sla` when `fields=None` — do not return all columns by default.
4. **Sprint 3 specific** — `_add_default_params` and `_extract_display_values` must remain on the GET path only. Write path (POST/PATCH/DELETE) must NOT apply these — write payloads are small and changing their shape would break vtb_task CRUD callers. Add explicit unit test: invoking `make_nws_request(url, method='POST')` must not call into `_add_default_params` or `_extract_display_values`.
5. **Sprint 1 specific** — `filter/explainer.py` response payload (the result of `explain_existing_filter`) must keep its current shape and field count. Don't add verbose metadata for LLM convenience — explanation is for tool callers, not for context window inflation.

**Token budget tooling:**

Add `tests/test_token_footprint.py` (Sprint 2 deliverable) — uses recorded HTTP fixtures + `tiktoken` (cl100k_base) to assert response payload tokenizes to ≤ a per-tool threshold. Wire into CI as a soft gate first, hard gate before v4.0 ships.

### Test coverage gate

CI gate is ≥30% on new lines (per `MEMORY.md`). All three sprints add new modules — each new file needs at least smoke tests to clear the gate.

### Backwards compatibility

Sprints 1 and 3 leave shim modules (`query_validation.py`, `query_intelligence.py`, `service_now_api_oauth.py`, `oauth_client.py`) as re-export façades for one release. Delete in v3.2 after consumers migrate.

Sprint 2 has no shim path — tools removed from MCP registration are immediately unavailable to clients. Update client documentation before merging.

### Documentation updates

Each sprint updates:
- `CLAUDE.md` — architecture section, tool inventory table
- `Diagrams & Documentation/01-architecture-overview.md` — module map
- `graphify-out/` — regenerate after each sprint via `graphify update .`

### Branch strategy

Per `MEMORY.md` convention: `feature/v3.1_filter-pipeline` (Sprint 1), `feature/v3.1_sla-collapse` (Sprint 2), `feature/v3.1_oauth-split` (Sprint 3). PRs into `release/v3.1`. Sonar gate on new-lines coverage ≥30%.

---

## Decisions (resolved 2026-05-20)

1. Sprint order: 2 → 1 → 3.
2. Sprint 2 MCP tool removal — accepted as breaking change in v4.0 (major release).
3. Sprint 3 subsystem unit tests — adopt `pytest-asyncio` for new modules.
4. Sprint 1 stale test failures — delete tests for `build_not_equals_filter` and `build_or_filter` (no production caller; methods stay removed).

## Out-of-band release note

`remote/feature/v3.1_docker-cloud-hosting` (GitHub-only branch) lands in a v3.1 release, not rebased onto v4.0. v3.1 ships independently before or in parallel with v4.0.
