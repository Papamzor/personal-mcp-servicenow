# v3.0 Release — Implementation Plan

## Overview

5 improvements: fix URL encoding bug, correct HTTP semantics, add performance parameters, ensure deterministic pagination, and consolidate near-duplicate tools. All functions kept under CC 15.

---

## Step 0: Create CLAUDE.md

Create `CLAUDE.md` at project root with codebase architecture knowledge for future sessions.

**Status**: Done

---

## Step 1: PUT to PATCH (Improvement 2)

**Smallest change, zero risk.**

### Problem
`vtb_task_tools.py:185` uses `"PUT"` for partial updates. REST semantics require `PATCH` for partial updates — PUT implies full resource replacement.

### Changes
| File | Change |
|------|--------|
| `Table_Tools/vtb_task_tools.py:185` | `"PUT"` → `"PATCH"` |
| `tests/test_vtb_task_tools.py` | Update assertion from `"PUT"` to `"PATCH"` |

### Verify
```bash
pytest tests/test_vtb_task_tools.py -v --tb=short
```
**Status**: Done

---

## Step 2: Performance Parameters (Improvement 3)

**Add `sysparm_exclude_reference_link=true` and `sysparm_no_count=true` to all API calls.**

### Problem
Every response includes unused reference link URLs (bloating token usage) and ServiceNow runs a `SELECT COUNT(*)` on every paginated request (adding latency). The pagination code never reads `X-Total-Count`.

### Approach
Add a `_add_default_params(url, display_value)` helper in `service_now_api_oauth.py` that injects all three params using the existing pattern. Replace the inline `sysparm_display_value` injection.

```python
def _add_default_params(url: str, display_value: bool = True) -> str:
    params = []
    if display_value and "sysparm_display_value" not in url:
        params.append("sysparm_display_value=true")
    if "sysparm_exclude_reference_link" not in url:
        params.append("sysparm_exclude_reference_link=true")
    if "sysparm_no_count" not in url:
        params.append("sysparm_no_count=true")
    if not params:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}{'&'.join(params)}"
```

CC: ~5.

### Changes
| File | Change |
|------|--------|
| `service_now_api_oauth.py` | Add `_add_default_params()`, refactor `make_nws_request()` to use it |
| `tests/test_service_now_api.py` | Add tests for new params, update URL assertions |

### Verify
```bash
pytest tests/test_service_now_api.py -v --tb=short
```

### Summary
All API read calls now include `sysparm_exclude_reference_link=true` (removes unused reference link URLs from responses, reducing token usage) and `sysparm_no_count=true` (skips `SELECT COUNT(*)` on paginated requests, reducing latency). A new `_add_default_params()` helper centralizes injection of these parameters alongside the existing `sysparm_display_value=true`. Tests were migrated from the legacy `service_now_api` module to `service_now_api_oauth`.

**Status**: Done

---

## Step 3: URL Encoding (Improvement 1)

**Centralize query encoding in `make_nws_request()` so all call sites are covered.**

### Problem
`_encode_query_string()` exists at `generic_table_tools.py:652` but is only used in `query_table_with_filters()` and `query_table_intelligently()`. Missing from:
- `query_table_by_text()` (line 154)
- `get_record_description()` (line 174)
- `get_record_details()` (line 186)
- `vtb_task_tools.py` read functions (lines 104, 112, 138, 215)

If a query contains `&`, `=`, `^`, `#`, or spaces, ServiceNow silently returns all records instead of filtered results.

### Approach
Add `_ensure_query_encoded(url)` helper in `service_now_api_oauth.py` that extracts the `sysparm_query` value from the URL and applies `quote(value, safe='=<>&^():@!')`. Call it inside `make_nws_request()`.

All read-path queries flow through `make_nws_request()`, so this fixes everything centrally. The CRUD paths in vtb_task_tools.py use `_make_authenticated_request()` directly but those use sys_id-based URLs with no user query input.

CC: ~4.

### Changes
| File | Change |
|------|--------|
| `service_now_api_oauth.py` | Add `_ensure_query_encoded()`, call in `make_nws_request()` |
| `Table_Tools/cmdb_tools.py` | Remove ad-hoc `quote(query_string, safe='=^')` calls (~lines 220, 409) since centralized now |
| `tests/test_service_now_api.py` | Add tests for encoding with special chars, already-encoded URLs, URLs without sysparm_query |

### Verify
```bash
pytest tests/test_service_now_api.py tests/test_generic_table_tools.py -v --tb=short
```

---

## Step 4: Sort Order for Pagination (Improvement 4)

**Append `^ORDERBYDESCsys_created_on` to all paginated queries.**

### Problem
`_make_paginated_request()` at `generic_table_tools.py:659` uses `sysparm_offset` pagination without a sort order. ServiceNow can return records in arbitrary order across pages — records can be skipped or duplicated.

### Approach
Add `_inject_sort_order(url, sort_directive)` helper and a `default_sort` parameter to `_make_paginated_request()`.

```python
def _inject_sort_order(url: str, sort_directive: str) -> str:
    if "ORDERBY" in url:
        return url  # Already has explicit sort
    if "sysparm_query=" in url:
        import re
        return re.sub(r'(sysparm_query=[^&]*)', rf'\1^{sort_directive}', url)
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}sysparm_query={sort_directive}"
```

CC: ~4. `_make_paginated_request()` stays at ~7.

### Changes
| File | Change |
|------|--------|
| `Table_Tools/generic_table_tools.py` | Add `_inject_sort_order()`, add `default_sort` param to `_make_paginated_request()` |
| `tests/test_generic_table_tools.py` | Add sort injection tests, update pagination tests |

### Verify
```bash
pytest tests/test_generic_table_tools.py -v --tb=short
```

---

## Step 5: Tool Consolidation (Improvement 5)

**Replace 24 near-duplicate 1-line wrappers with 5 generic tools that take a `table` parameter. Remove dead code from vtb_task_tools.py.**

### What gets removed (24 wrappers in `consolidated_tools.py`)
All are 1-line functions that call a generic function with a hardcoded table name:
- 7x `similar_X_for_text()` → `search_records(table, query)`
- 5x `get_short_desc_for_X()` → `get_record_summary(table, number)`
- 5x `similar_X_for_X()` → `find_similar(table, number)`
- 5x `get_X_details()` → `get_record(table, number)`
- 2x `get_X_by_filter()` → `filter_records(table, filters, fields)`

### What stays (unique logic)
- 10 SLA tools (each has specialized query patterns)
- 6 CMDB tools (separate architecture)
- 5 intelligent query tools
- 5 auth/utility tools
- `get_priority_incidents()` (complex date logic)
- `get_knowledge_by_category()`, `get_active_knowledge_articles()` (unique params)
- `create_private_task()`, `update_private_task()` (CRUD)

### New file: `Table_Tools/generic_tool_wrappers.py`
5 new MCP-facing functions with rich docstrings listing supported tables, fields, return format, and usage examples. Each validates table name against `TABLE_CONFIGS` and delegates to the existing generic function. CC: 3 per function.

### Dead code removal: `Table_Tools/vtb_task_tools.py`
Remove lines 100-218 (5 duplicate query functions never registered in tools.py — the consolidated versions are used instead). Keep only:
- CRUD helpers: `_get_authenticated_headers()`, `_make_authenticated_request()`, `_handle_http_error()`, `_prepare_task_create_data()`, `_get_task_sys_id()`
- `create_private_task()`
- `update_private_task()`

### Changes
| File | Change |
|------|--------|
| **Create** `Table_Tools/generic_tool_wrappers.py` | 5 generic tool functions with rich docstrings |
| `Table_Tools/consolidated_tools.py` | Remove 24 wrapper functions. Keep priority incidents, knowledge-specific, SLA tools, helper functions. |
| `Table_Tools/vtb_task_tools.py` | Remove dead duplicate functions (lines 100-218) |
| `tools.py` | Rewrite imports and tool list for new generic tools |
| `personal_mcp_servicenow_main.py` | Update `__version__` to `"3.0.0"` |
| **Create** `tests/test_generic_tool_wrappers.py` | Test table validation, each generic tool, error cases |
| `tests/test_consolidated_tools.py` | Remove tests for removed wrappers. Keep priority/SLA/helper tests. |
| `tests/test_vtb_task_tools.py` | Remove tests for dead functions. Keep CRUD tests. |
| `tests/test_mcp_tools.py` | Update expected tool count |

### Final Tool Inventory (~31 tools)

| # | Tool | Category |
|---|------|----------|
| 1 | `search_records(table, query)` | Generic |
| 2 | `get_record(table, number)` | Generic |
| 3 | `get_record_summary(table, number)` | Generic |
| 4 | `find_similar(table, number)` | Generic |
| 5 | `filter_records(table, filters, fields)` | Generic |
| 6 | `get_priority_incidents(...)` | Incident |
| 7 | `get_knowledge_by_category(...)` | Knowledge |
| 8 | `get_active_knowledge_articles(...)` | Knowledge |
| 9 | `create_private_task(...)` | CRUD |
| 10 | `update_private_task(...)` | CRUD |
| 11-20 | 10 SLA tools | SLA |
| 21-26 | 6 CMDB tools | CMDB |
| 27-31 | 5 intelligent query tools | Intelligence |
| +5 | auth/utility tools | Auth |

### Verify
```bash
pytest tests/ -v --tb=short
pytest tests/ --cov=. --cov-report=term-missing
```

---

## Final Verification

After all steps:
1. `pytest tests/ -v --tb=short` — all tests pass
2. `pytest tests/ --cov=. --cov-report=term-missing` — coverage >= 80%
3. `python personal_mcp_servicenow_main.py --version` — shows 3.0.0
4. Start MCP server and verify tool count matches ~31 (+ 5 auth)
5. Smoke test: call `search_records("incident", "test")` and verify response has encoded query, performance params, and sorted results
