# Migration Guide: v4.x → v5.0 "Boron"

v5.0 is a major release with breaking changes for **MCP clients**. Two things
change: the tool surface is culled 39 → 25 (15 tools removed, each with a
replacement), and **every** tool now returns one minimal response contract
instead of the v4 mix of bare strings, `{"message": ...}` dialects, and
one-row `result` lists.

If your client only ever passed tool output straight back to a model, the
response-shape change is low-risk (the model reads the new shapes fine). If your
client *parses* tool output, or calls any of the 15 removed tool names, read on.

---

## 1. Removed tools and their replacements

| Removed v4 tool | v5 replacement |
|---|---|
| `nowtest` | `health_check()` |
| `now_test_oauth` | `health_check()` |
| `nowtestauth` | `health_check()` |
| `now_auth_info` | `health_check()` |
| `nowtest_auth_input(table)` | `health_check(probe_table=table)` |
| `get_record_summary(table, number)` | `get_record(table, number)` |
| `intelligent_search(query, ...)` | `search_records(table, query)` / `filter_records(table, filters)` |
| `explain_servicenow_filters(...)` | (none — the host model explains its own filters) |
| `build_smart_servicenow_filter(...)` | `filter_records(table, filters)` |
| `get_servicenow_filter_templates()` | (none — see `get_query_syntax_help` for operators) |
| `get_query_examples()` | `get_query_syntax_help()` |
| `similar_knowledge_for_text(text, ...)` | `search_records("kb_knowledge", text)` |
| `get_knowledge_by_category(category)` | `filter_records("kb_knowledge", {"kb_category": category})` |
| `get_active_knowledge_articles()` | `get_kb_articles_by_state("published")` |
| `similar_slas_for_text(text)` | `filter_records("task_sla", {"task.short_description": "LIKE…"})` |

Notes:

- **The 5 diagnostics became one.** `health_check(probe_table=None)` returns a
  status bag: `server` liveness, `auth` config, `connection` (`ok`/`failed`), and
  — when `probe_table` is given — that table's `sample_fields`.
- **The NL / filter tools are gone on purpose.** The in-repo natural-language
  engine (~2000 lines) duplicated what the host model already does; there is no
  drop-in "smart" tool. Describe the query in `search_records` (free text) or name
  the fields in `filter_records`.
- **`similar_slas_for_text` never worked** — it filtered a `short_description`
  column `task_sla` does not have, so ServiceNow silently returned an arbitrary
  page. Filter the dot-walked field instead.
- **The "smart" KB reads silently dropped `input_text`** when a category/base was
  set. The replacements do exactly one thing each, visibly.

The 25 surviving tools keep their v4 names and signatures (except
`get_priority_incidents`, below).

---

## 2. Response contract — every tool

v4 tools answered in several shapes: a list under `result`, a one-row `result`
list for single records, a bare dict or a bare error **string** from writes, a
`{"result": [...], "message": "Found N records"}` success dialect, and 16 bare
not-found strings in the CMDB tools. v5 replaces all of it with four shapes.

| Case | v5 shape |
|---|---|
| List success (incl. empty) | `{"result": [...], "returned_count": <int>, "truncated": <bool>}` |
| Single record | `{"record": {...}}` — **never** a one-row `result` list |
| Single-record miss | `{"record": null}` |
| Write success | `{"record": {...}, "message": <str>}` |
| Failure | `{"error": {"code": <CODE>, "message": <str>}}` and nothing else |

`CODE` is one of `VALIDATION`, `NOT_FOUND`, `AUTH`, `FORBIDDEN`, `TIMEOUT`,
`HTTP`, `INTERNAL`.

**The discriminator is the presence of `error`.** There is no `ok`/`success`
boolean, and a successful-but-empty read is `{"result": [], "returned_count": 0}`
— an empty list is success, not an error.

### Client changes you will actually feel

- **`get_record`**: read `resp["record"]`, not `resp["result"][0]`. A missing
  record is `{"record": null}`.
- **Write tools** (`create_private_task`, `update_private_task`,
  `update_knowledge_article`, `publish_knowledge_article`,
  `retire_knowledge_article`): success is `{"record": {...}, "message": ...}`;
  failure is `{"error": {"code", "message"}}`. v4 code that did
  `isinstance(result, str)` to detect a write error must now check for an `error`
  key. A 2xx write that returns no record body is reported as
  `{"error": {"code": "INTERNAL", ...}}` (unconfirmed) — it is **not** silently
  treated as success.
- **CMDB tools**: an empty search is `{"result": []}` (not a "no CIs found"
  string); `get_ci_details` returns the CI under `record`.
- **Errors are `{code, message}` dicts, never strings.** Validation errors
  (unknown table, unsupported field, task_sla passed to an identity tool) are
  `{"error": {"code": "VALIDATION", "message": ...}}`.

### Two sanctioned exceptions

- **`health_check`** returns a diagnostic status bag, so `error` can sit beside
  `connection`/`server`/`auth`. It is not a data tool.
- **Partial page**: a read that fails *after* collecting some rows returns those
  rows plus `{"partial": true, "error": {...}}` — the one case where data and
  `error` coexist. Discarding good rows because a later page timed out was the bug
  this shape fixes.

---

## 3. `get_priority_incidents` — dropped `**kwargs`

v4 accepted arbitrary extra filters as keyword arguments (deprecated since v4.0).
v5 removes that path:

```python
# v4 (deprecated):  get_priority_incidents(["1"], state="2")
# v5:               get_priority_incidents(["1"], additional_filters={"state": "2"})
```

A stray keyword is now a `TypeError`, not a silently-merged filter.

---

## 4. Nothing else changed for callers

Auth, configuration, transport, the encoded-query value rules (v4.4.1), and the
read-failure contract (v4.4 Tier 0.3) are unchanged. The internal refactors
(`TableSpec` config consolidation, the tool-guidance registry, ~2000 lines of
dead NL-engine code removed) are not visible at the MCP boundary beyond the tool
list and the response shapes above.
