# MCP ServiceNow Server - Architecture Documentation

This folder contains Mermaid diagrams documenting the architecture of the Personal MCP ServiceNow server (v3.0).

## Diagram Index

| File | Description | Diagram Type | Status |
|------|-------------|--------------|--------|
| [01-architecture-overview.md](./01-architecture-overview.md) | v3.0 architecture with generic tool wrappers, performance params, URL encoding, deterministic sort | Component Diagram | **Updated for v3.0** |
| [02-oauth-authentication-flow.md](./02-oauth-authentication-flow.md) | OAuth 2.0 authentication sequence with ServiceNow | Sequence Diagram | Current |
| [03-tool-organization.md](./03-tool-organization.md) | v3.0 tool consolidation: 24 wrappers → 5 generic tools, 55 → 36 total tools | Graph Diagram | **Updated for v3.0** |
| [04-similarity-search-flow.md](./04-similarity-search-flow.md) | Search flow with `search_records` generic tool, API enhancements, AI search | Flowchart | **Updated for v3.0** |
| [05-ai-intelligence-flow.md](./05-ai-intelligence-flow.md) | AI intelligence workflow with natural language processing | Flowchart | Current |
| [06-sla-architecture-flow.md](./06-sla-architecture-flow.md) | SLA monitoring architecture with 10 specialised tools | Architecture Diagram | Current |

## How to View Diagrams

### VS Code
1. Install the **Mermaid Preview** extension
2. Open any `.md` file in this folder
3. Use `Ctrl+Shift+V` to preview with rendered diagrams

### GitHub / Bitbucket
- Diagrams render automatically when viewing files on GitHub
- Click on any `.md` file to see the rendered Mermaid charts

### Mermaid Live Editor
1. Copy the mermaid code block from any file
2. Paste into [Mermaid Live Editor](https://mermaid.live/)
3. View, edit, and export as needed

## System Overview (v3.0)

The MCP ServiceNow server provides:

- **36 Tools** across 8 ServiceNow table types (down from 55 in v2.x)
- **5 Generic Tools** replacing 24 per-table wrappers via `TABLE_CONFIGS` validation
- **OAuth 2.0 Authentication** with automatic token management
- **Performance Optimizations**: `sysparm_exclude_reference_link`, `sysparm_no_count`
- **Centralized URL Encoding**: All `sysparm_query` values encoded in `make_nws_request()`
- **Deterministic Pagination**: `^ORDERBYDESCsys_created_on` on all paginated queries
- **AI Intelligence**: Natural language query processing and smart filter generation
- **537 Tests**, 80% coverage, all functions under CC 15

## Architecture Summary

```
MCP Client (Claude)
  ↓ stdio
tools.py (FastMCP registration — 36 tools)
  ↓
generic_tool_wrappers.py (5 generic tools with table validation)
consolidated_tools.py   (priority incidents, knowledge, 10 SLA tools)
cmdb_tools.py           (6 CMDB tools)
intelligent_query_tools.py (5 NLP tools)
vtb_task_tools.py       (2 CRUD tools)
  ↓
generic_table_tools.py (core query engine + pagination + sort order)
  ↓
service_now_api_oauth.py (perf params + URL encoding + display values)
  ↓
oauth_client.py → httpx → ServiceNow REST API
```

---

*Last Updated: February 2026*
*Project: Personal MCP ServiceNow Server v3.0*
