# MCP ServiceNow Server — Architecture Documentation

Mermaid diagrams for the Personal MCP ServiceNow server (**v4.3**). Packaging is Claude Desktop Extension (`.mcpb`); distribution is no longer Nuitka binaries.

## Diagram Index

| File | Description | Diagram Type | Status |
|------|-------------|--------------|--------|
| [01-architecture-overview.md](./01-architecture-overview.md) | Layered architecture: tools → filter → http_layer → oauth → ServiceNow | Component | **v4.3** |
| [02-oauth-authentication-flow.md](./02-oauth-authentication-flow.md) | Client-credentials flow, token cache, 401 retry, pooled httpx | Sequence | **v4.3** |
| [03-tool-organization.md](./03-tool-organization.md) | 39 tools by source module; generic wrappers + domain tools | Graph | **v4.3** |
| [04-similarity-search-flow.md](./04-similarity-search-flow.md) | `search_records` / `intelligent_search` read path (OR-LIKE, pagination, GET params) | Flowchart | **v4.3** |
| [05-ai-intelligence-flow.md](./05-ai-intelligence-flow.md) | NL → `filter/` pipeline (intelligence → validator → builder → explainer) | Flowchart | **v4.3** |
| [06-sla-architecture-flow.md](./06-sla-architecture-flow.md) | 5 SLA tools, status presets, token-safe defaults | Architecture | **v4.3** |

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

## System Overview (v4.3)

- **39 MCP tools** over stdio (Claude Desktop) or SSE (Docker / network agents)
- **8 tables** in `TABLE_CONFIGS`: `incident`, `change_request`, `sc_req_item`, `sc_task`, `universal_request`, `kb_knowledge`, `vtb_task`, `task_sla`
- **5 generic tools** for any configured table (`search_records`, `get_record`, …)
- **Filter pipeline** in `filter/` (no v3 shims — deleted in v4.1)
- **HTTP layer** in `http_layer/` — GET token-optimization invariants; writes bypass them
- **OAuth** in `oauth/` — façade + TokenStore + RequestExecutor + process-wide httpx pool (v4.2)
- **Writes**: `vtb_task` CRUD + KB article lifecycle tools
- **Distribution**: `.mcpb` bundle (`scripts/build_mcpb.py`) or Docker SSE

## Architecture Summary

```
MCP Client (Claude / agent)
  ↓ stdio | SSE
tools.py (FastMCP + AuthMiddleware + AuditMiddleware — 39 tools)
  ↓
generic_tool_wrappers.py   (5 generic tools — TABLE_CONFIGS validate)
consolidated_tools.py      (priority incidents, knowledge read, 5 SLA tools)
vtb_task_tools.py          (private task create/update)
kb_article_tools.py        (KB update / publish / batch / retire / dup-check)
cmdb_tools.py              (6 CMDB tools)
intelligent_query_tools.py (6 NLP / filter-help tools)
  ↓
generic_table_tools.py     (query engine, pagination)
  ↓
filter/                    (builder, validator, intelligence, explainer, models)
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
| [MIGRATION_v3_to_v4.md](../MIGRATION_v3_to_v4.md) | v3 → v4 SLA + import path changes |
| [OAUTH_SETUP_GUIDE.md](../OAUTH_SETUP_GUIDE.md) | ServiceNow OAuth client setup |
| [CHANGELOG.md](../CHANGELOG.md) | Version history |

---

*Last updated: 2026-08-10 · Project version: 4.4.1*
