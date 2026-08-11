# MCP ServiceNow Server — Architecture Documentation

Mermaid diagrams for the Personal MCP ServiceNow server. Packaging is Claude Desktop Extension (`.mcpb`); distribution is no longer Nuitka binaries.

## Diagram Index

| File | Description | Diagram Type | Status |
|------|-------------|--------------|--------|
| [01-architecture-overview.md](./01-architecture-overview.md) | Layered architecture: tools → filter → http_layer → oauth → ServiceNow | Component | v5.0 |
| [02-oauth-authentication-flow.md](./02-oauth-authentication-flow.md) | Client-credentials flow, token cache, 401 retry, pooled httpx | Sequence | v4.3 (oauth layer unchanged in v5.0) |
| [03-tool-organization.md](./03-tool-organization.md) | 25 tools by source module; generic wrappers + domain tools | Graph | v5.0 |
| [04-similarity-search-flow.md](./04-similarity-search-flow.md) | `search_records` / `filter_records` read path (OR-LIKE, pagination, GET params, §3.1) | Flowchart | v5.0 |
| [06-sla-architecture-flow.md](./06-sla-architecture-flow.md) | 4 SLA tools, status presets, token-safe defaults | Architecture | v5.0 |

> `05-ai-intelligence-flow.md` was deleted in v5.0 — the NL engine it documented is gone; natural language → filter is the host model's job.

## How to View Diagrams

### VS Code
1. Install the **Mermaid Preview** extension (or use built-in Markdown preview with Mermaid support)
2. Open any `.md` file in this folder
3. Preview with `Ctrl+Shift+V` (Windows) / `Cmd+Shift+V` (macOS)

### GitHub / Bitbucket
- Mermaid in fenced ` ```mermaid ` blocks renders in the file viewer

### Mermaid Live Editor
1. Copy a mermaid code block
2. Paste into [Mermaid Live Editor](https://mermaid.live/)

## System Overview (v5.0)

- **25 MCP tools** over stdio (Claude Desktop) or SSE (Docker / network agents)
- **8 tables** via `table_spec.TABLE_SPECS` → derived `TABLE_CONFIGS`: `incident`, `change_request`, `sc_req_item`, `sc_task`, `universal_request`, `kb_knowledge`, `vtb_task`, `task_sla`
- **4 generic tools** for any configured table (`search_records`, `get_record`, `find_similar`, `filter_records`)
- **§3.1 response contract** — list / record / write / error envelopes from `Table_Tools/response.py`
- **Filter pipeline** in `filter/` (builder, validator, value_encoding, models — no NL intelligence)
- **HTTP layer** in `http_layer/` — GET token-optimization invariants; writes bypass them
- **OAuth** in `oauth/` — façade + TokenStore + RequestExecutor + process-wide httpx pool (v4.2)
- **Writes**: `vtb_task` CRUD + KB article lifecycle tools
- **Registration**: `tool_registry.register_tools` injects WHEN / WHEN-NOT / PREFER guidance
- **Distribution**: `.mcpb` bundle (`scripts/build_mcpb.py`) or Docker SSE

## Architecture Summary

```
MCP Client (Claude / agent)
  ↓ stdio | SSE
tools.py (FastMCP + AuthMiddleware + AuditMiddleware)
  ↓ tool_registry.register_tools — 25 tools + guidance injection
utility_tools.py           (health_check — 1)
generic_tool_wrappers.py   (4 generic tools — TABLE_CONFIGS validate)
consolidated_tools.py      (priority, KB state rollup, 4 SLA tools)
vtb_task_tools.py          (private task create/update)
kb_article_tools.py        (KB update / publish / batch / retire / dup-check)
cmdb_tools.py              (6 CMDB tools)
intelligent_query_tools.py (get_query_syntax_help only)
  ↓ Table_Tools/response.py  (§3.1 contract constructors)
generic_table_tools.py     (query engine, pagination)
  ↓
table_spec.py → constants.py   (SSOT → derived field/config maps)
filter/                    (builder, validator, value_encoding, models)
  ↓
http_layer/                (make_nws_request: GET url_builder + response_parser)
  ↓
oauth/                     (singleton → client → token_store + request_executor + http_pool)
  ↓
httpx → ServiceNow Table API
```

## Related docs (repo root)

| Doc | Purpose |
|-----|---------|
| [README.md](../README.md) | Install, config, Claude Desktop / Docker |
| [docs/MCPB_BUILD.md](../docs/MCPB_BUILD.md) | `.mcpb` build and release |
| [MIGRATION_v4_to_v5.md](../MIGRATION_v4_to_v5.md) | v4 → v5 tool cull + response contract (breaking) |
| [MIGRATION_v3_to_v4.md](../MIGRATION_v3_to_v4.md) | v3 → v4 SLA + import path changes |
| [OAUTH_SETUP_GUIDE.md](../OAUTH_SETUP_GUIDE.md) | ServiceNow OAuth client setup |
| [CHANGELOG.md](../CHANGELOG.md) | Version history |

---

*Last updated: 2026-08-11 · Project version: 5.0.0*
