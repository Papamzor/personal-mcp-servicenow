# Migration Guide: v3.x → v4.0

v4.0 is a major release with breaking changes. Most of the churn is internal to the codebase — backwards-compat shims preserve the v3 Python import paths and test-patch targets. The breaking changes for MCP clients are limited to the SLA tool surface.

## 1. MCP clients — SLA tool changes (Sprint 2)

Eight SLA tools were collapsed into 3 new tools. If your client calls any of these names, update it.

### Removed tools and their replacements

| Removed v3 tool | v4 replacement |
|---|---|
| `get_slas_for_task(task_number)` | `query_slas_by_task(task_number)` |
| `get_breaching_slas(time_threshold_minutes)` | `query_slas_by_status("breaching", threshold_minutes=...)` |
| `get_breached_slas(filters, days)` | `query_slas_by_status("breached", days=..., extra_filters=...)` |
| `get_slas_by_stage(stage, additional_filters)` | `query_slas_by_status("by_stage", stage=..., extra_filters=...)` |
| `get_active_slas(filters)` | `query_slas_by_status("active", extra_filters=...)` |
| `get_sla_performance_summary(filters, days)` | `query_slas_by_status("performance", days=..., extra_filters=...)` |
| `get_recent_breached_slas(days)` | `query_slas_by_status("breached", days=1)` |
| `get_critical_sla_status()` | `query_slas_by_status("critical")` |

### Unchanged tools

- `similar_slas_for_text(input_text)`
- `get_sla_details(sla_sys_id)` — same signature, but internally fixed (see below)

### `get_sla_details` bug fix (no caller action needed)

`get_sla_details(sys_id)` in v3 was broken: it routed through `get_record_details("task_sla", sys_id)` which built a `number={sys_id}` filter, but `task_sla` has no `number` field. ServiceNow silently ignored the filter and returned the full default page (10,000 rows / ~1.2 million tokens). v4 routes via `sys_id={sys_id}` directly and returns the single record (~69 tokens).

If your client was working around this bug by ignoring the bloated response, the v4 fix returns the correct single record — your workaround can be removed.

### `query_slas_by_status` enum values

```python
SLA_STATUS_VALUES = ("active", "breached", "breaching", "critical", "by_stage", "performance")
```

Calling with an unrecognized status raises `ValueError`. `"by_stage"` requires the `stage` keyword argument.

The `"critical"` and `"performance"` presets return a curated field list (7 and 11 fields respectively) to preserve the v3 per-tool token budget.

### `query_slas_custom` field defaults

When called with `fields=None`, falls back to `ESSENTIAL_FIELDS["task_sla"]` — never returns all columns by default. Pass `fields=[...]` to override.

## 2. Python code — import path changes (optional)

All v3 import paths continue to work via backwards-compat shims. Updating to the new paths is optional in v4.0 and required in v4.1 when the shims are deleted.

### Recommended new paths

| v3 import | v4 import |
|---|---|
| `from query_validation import ServiceNowQueryBuilder, validate_query_filters` | `from filter import ServiceNowQueryBuilder, validate_query_filters` |
| `from query_intelligence import QueryIntelligence, explain_existing_filter` | `from filter import QueryIntelligence, explain_existing_filter` |
| `from Table_Tools.generic_table_tools import TableFilterParams, SmartQueryParams` | `from filter import TableFilterParams, SmartQueryParams` |
| `from service_now_api_oauth import make_nws_request` | `from http_layer import make_nws_request` |
| `from oauth_client import ServiceNowOAuthClient` | `from oauth import ServiceNowOAuthClient` |
| `from oauth_client import ServiceNowAuthenticationError` | `from oauth import ServiceNowAuthenticationError` |

### Module-level singleton stays in `oauth_client`

`get_oauth_client()`, `make_oauth_request()`, and the `_oauth_client` module attribute remain in `oauth_client.py` even after v4.1. The class moved to `oauth/client.py`; the singleton stays where existing test fixtures expect it.

## 3. Tests — patch targets

All v3 test-patch targets continue to resolve in v4.0. You do not need to rewrite test fixtures.

The following patch patterns are explicitly supported:

```python
@patch("oauth_client.httpx.AsyncClient")
@patch("oauth_client.ServiceNowOAuthClient")
oauth_client._oauth_client = None

@patch.object(client, "_request_access_token")
@patch.object(client, "_get_valid_token")
@patch.object(client, "get_auth_headers")

@patch("service_now_api_oauth.make_oauth_request")
@patch("service_now_api_oauth.get_oauth_client")

@patch("query_intelligence.extract_keywords")
@patch("query_validation.validate_query_filters")
```

If you are rewriting tests against the new packages, the equivalents are:

- `patch("oauth.client.httpx.AsyncClient")` — but `httpx` is a singleton, so either path works for module-attribute patches
- `patch("http_layer.request_dispatcher.make_oauth_request")` — note that the dispatcher does a runtime lookup via `sys.modules["service_now_api_oauth"]` first, then falls back to `oauth_client`, so patching the v3 shim still works

## 4. Tool count

The MCP tool count dropped from 37 to 32. If your client has a hardcoded expected count (e.g. for a health check), update it.

## 5. Dependency changes

Added dev dependencies:
- `pytest-asyncio>=0.23.0` — for v4 subsystem tests
- `tiktoken>=0.7.0` — for the token-footprint regression suite

No new production dependencies.

## 6. Token-budget invariants

v4.0 locks the token-optimization invariants in `tests/test_http_layer.py`:

- **GET path** applies `sysparm_exclude_reference_link=true`, `sysparm_no_count=true`, `sysparm_display_value=true`, and runs display-value flattening on the response.
- **POST/PATCH/DELETE** must NOT apply any of the above — applying read-only params to a write payload would mangle the request; running display flattening on a write response would corrupt its structure.

If you extend the HTTP layer, the negative-test suite will catch any leak between the two paths.

## Verifying your migration

```bash
# Tests should pass
pytest tests/ -v

# Live ServiceNow regression — capture baseline + diff
python scripts/capture_read_path_baseline.py
python scripts/capture_sla_token_baseline.py
python scripts/compare_sla_token_baseline.py

# Tool count check
python -c "import tools; assert len(tools.tools) == 32, len(tools.tools)"
```

## Questions?

- The full architectural rationale lives in `ARCHITECTURE_REFACTOR_PLAN.md`.
- Graphify analysis output (the source of these refactors) lives in `graphify-out/`.
