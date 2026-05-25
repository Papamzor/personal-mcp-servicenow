# Personal MCP ServiceNow Integration

MCP server for ServiceNow integration. Uses FastMCP over stdio transport, OAuth 2.0 client credentials.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![ServiceNow](https://img.shields.io/badge/ServiceNow-REST%20API-green.svg)](https://servicenow.com)
[![OAuth 2.0](https://img.shields.io/badge/Auth-OAuth%202.0%20Only-orange.svg)](https://oauth.net/2/)

---

## Support This Project

[![PayPal](https://img.shields.io/badge/PayPal-Support%20Development-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://www.paypal.me/papamzor)

---

## What's new in v4.0

v4.0 is a breaking release. See [MIGRATION_v3_to_v4.md](MIGRATION_v3_to_v4.md) if upgrading.

| Change | Detail |
|---|---|
| SLA tool consolidation | 8 tools collapsed into 3 (`query_slas_by_task`, `query_slas_by_status`, `query_slas_custom`). Tool count: **37 → 32**. |
| `get_sla_details` bug fix | v3 built a `number={sys_id}` filter on `task_sla` (no `number` field). ServiceNow ignored it, returning 10,000 rows (~1.2M tokens). v4 routes via `sys_id=` — single record (~69 tokens). |
| `filter/` package | Filter construction, validation, NL parsing, and explanation consolidated into a single package. `query_validation.py` and `query_intelligence.py` are now shims. |
| `http_layer/` + `oauth/` packages | `make_nws_request` and `ServiceNowOAuthClient` split into focused packages. GET-path token-optimization invariants locked by 3 negative write-path tests. |

Backwards-compat shims keep all v3 import paths and test-patch targets working. Shims deleted in v4.1.

---

## Installation

### From source

```bash
git clone https://github.com/Papamzor/personal-mcp-servicenow.git
cd personal-mcp-servicenow
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Docker (cloud / network agents)

For hosting over the network (N8N, LangChain, any MCP-compatible agent):

```bash
docker build -t mcp-servicenow .

docker run -d \
  -p 8000:8000 \
  --env-file .env.local \
  --name mcp-servicenow \
  mcp-servicenow
```

> **Do not pass secrets with `-e KEY=value`.** They land in shell history and are visible via `ps` / `docker inspect`. Use `--env-file` for local testing; see [Production: Azure Container Apps + Key Vault](#production-azure-container-apps--key-vault) for production.

The image sets `MCP_TRANSPORT=sse` by default. Agents connect at `http://<your-host>:8000/sse`.

---

## Configuration

Create `.env` in project root:

```env
SERVICENOW_INSTANCE=https://your-instance.service-now.com
SERVICENOW_CLIENT_ID=your_oauth_client_id
SERVICENOW_CLIENT_SECRET=your_oauth_client_secret
```

OAuth 2.0 client credentials are required. Basic auth is not supported. See [OAUTH_SETUP_GUIDE.md](OAUTH_SETUP_GUIDE.md) for ServiceNow-side setup.

---

## Claude Desktop / Claude Code integration

**Claude Desktop** — config file location:

- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "servicenow": {
      "command": "python",
      "args": ["/full/path/to/personal-mcp-servicenow/personal_mcp_servicenow_main.py"]
    }
  }
}
```

Credentials are read from the `.env` file. If you prefer to inject them via the config:

```json
{
  "mcpServers": {
    "servicenow": {
      "command": "python",
      "args": ["/full/path/to/personal-mcp-servicenow/personal_mcp_servicenow_main.py"],
      "env": {
        "SERVICENOW_INSTANCE": "https://your-instance.service-now.com",
        "SERVICENOW_CLIENT_ID": "your_oauth_client_id",
        "SERVICENOW_CLIENT_SECRET": "your_oauth_client_secret"
      }
    }
  }
}
```

**Claude Code (remote SSE)**:

```json
{
  "mcpServers": {
    "servicenow": {
      "type": "sse",
      "url": "http://<your-host>:8000/sse"
    }
  }
}
```

---

## Available tools (32)

### Generic table tools (5)

Work across all supported tables: `incident`, `change_request`, `sc_req_item`, `sc_task`, `universal_request`, `kb_knowledge`, `vtb_task`, `task_sla`.

- `search_records(table, query)` — text similarity search
- `get_record_summary(table, number)` — short description for a single record
- `get_record(table, number)` — full detail fields for a single record
- `find_similar(table, number)` — records similar to an existing record
- `filter_records(table, filters, fields)` — field-value filters with operators and date ranges

### Intelligent query tools (5)

- `intelligent_search(query, table, context)` — natural language: "high priority incidents from last week"
- `build_smart_servicenow_filter(query, table, context)` — NL → ServiceNow query syntax
- `explain_servicenow_filters(filters, table)` — human-readable filter explanation
- `get_servicenow_filter_templates()` — pre-built filters for common scenarios
- `get_query_examples()` — natural language examples

### Priority incidents (1)

- `get_priority_incidents(priorities, start_date, end_date, additional_filters, include_metadata)`

### Knowledge base (3)

- `similar_knowledge_for_text(input_text, kb_base, category)`
- `get_knowledge_by_category(category, kb_base)`
- `get_active_knowledge_articles(input_text)`

### Private task CRUD (2)

- `create_private_task(task_data)` — creates vtb_task record
- `update_private_task(task_number, update_data)` — PATCH update

### SLA management (5)

- `similar_slas_for_text(input_text)`
- `get_sla_details(sla_sys_id)`
- `query_slas_by_task(task_number)`
- `query_slas_by_status(status, days?, threshold_minutes?, stage?, extra_filters?)` — status enum: `"active"`, `"breached"`, `"breaching"`, `"critical"`, `"by_stage"`, `"performance"`
- `query_slas_custom(filters, fields?, days?)` — escape hatch; `fields=None` defaults to `ESSENTIAL_FIELDS["task_sla"]`

### CMDB (6)

- `find_cis_by_type(ci_type)` — 100+ CI types supported
- `search_cis_by_attributes(name, ip_address, location, status)`
- `get_ci_details(ci_number)`
- `similar_cis_for_ci(ci_number)`
- `get_all_ci_types()`
- `quick_ci_search(search_term)`

### Server & auth (5)

- `nowtest()`, `now_test_oauth()`, `now_auth_info()`, `nowtestauth()`, `nowtest_auth_input(table)`

---

## Architecture

```
MCP Client (Claude)
  ↓ stdio / sse
tools.py (FastMCP — 32 tools)
  ↓
generic_tool_wrappers.py   consolidated_tools.py   vtb_task_tools.py
cmdb_tools.py              intelligent_query_tools.py
  ↓
generic_table_tools.py (core query engine, pagination, deterministic sort)
  ↓
filter/                     (v4.0 Sprint 1)
  builder.py                — ServiceNowQueryBuilder
  validator.py              — validate_query_filters, validate_and_correct_filters
  intelligence.py           — QueryIntelligence (NL → filter; no backref to builder)
  explainer.py              — QueryExplainer
  models.py                 — TableFilterParams, SmartQueryParams
  ↓
http_layer/                 (v4.0 Sprint 3)
  url_builder.py            — ensure_query_encoded, add_default_params (GET-only)
  response_parser.py        — extract_display_values (GET-only)
  request_dispatcher.py     — make_nws_request (~30 lines, dispatches GET vs write)
  ↓
oauth/                      (v4.0 Sprint 3)
  token_store.py            — token cache + refresh (injectable fetcher)
  request_executor.py       — authenticated HTTP + 401 retry
  client.py                 — ServiceNowOAuthClient façade
  exceptions.py             — 4 exception classes
  ↓
httpx → ServiceNow REST API
```

**GET path** applies `sysparm_exclude_reference_link=true`, `sysparm_no_count=true`, `sysparm_display_value=true`, and display-value flattening.  
**POST/PATCH/DELETE** bypass all of the above — enforced by 3 negative tests in `tests/test_http_layer.py`.

**v4.0 shims** (deleted in v4.1): `query_validation.py`, `query_intelligence.py`, `oauth_client.py`, `service_now_api_oauth.py`

---

## Testing

```bash
# Full suite
pytest tests/ -v --tb=short

# With coverage
pytest tests/ --cov=. --cov-report=term-missing

# Live ServiceNow regression
python scripts/capture_sla_token_baseline.py
python scripts/compare_sla_token_baseline.py
python scripts/capture_read_path_baseline.py
```

575 tests passing, ~83% overall coverage. `filter/` 98.16%, `oauth/` + `http_layer/` 92.98%.

---

## Cloud hosting: Azure Container Apps + Key Vault

For production, store credentials in Azure Key Vault and inject via managed identity. No secrets in env vars, shell history, or `docker inspect`.

```
Key Vault (secrets)
   ↑ reads via RBAC
Container App (managed identity)
   ↓ injects as env vars via secretRef
mcp-servicenow container
```

**1. Push to Azure Container Registry**

```bash
az acr create -g <rg> -n <acrName> --sku Basic
az acr login -n <acrName>
docker tag mcp-servicenow <acrName>.azurecr.io/mcp-servicenow:latest
docker push <acrName>.azurecr.io/mcp-servicenow:latest
```

**2. Create Key Vault and store secrets**

```bash
az keyvault create -g <rg> -n <kvName> --enable-rbac-authorization true
az keyvault secret set --vault-name <kvName> --name servicenow-instance      --value "https://your-instance.service-now.com"
az keyvault secret set --vault-name <kvName> --name servicenow-client-id     --value "your_oauth_client_id"
az keyvault secret set --vault-name <kvName> --name servicenow-client-secret --value "your_oauth_client_secret"
```

**3. Create Container App with system-assigned managed identity**

```bash
az containerapp env create -g <rg> -n <envName> --location westeurope

az containerapp create \
  -g <rg> -n mcp-servicenow \
  --environment <envName> \
  --image <acrName>.azurecr.io/mcp-servicenow:latest \
  --target-port 8000 --ingress external \
  --system-assigned \
  --registry-server <acrName>.azurecr.io
```

**4. Grant Key Vault access to the identity**

```bash
PRINCIPAL_ID=$(az containerapp show -g <rg> -n mcp-servicenow --query identity.principalId -o tsv)
KV_ID=$(az keyvault show -g <rg> -n <kvName> --query id -o tsv)

az role assignment create \
  --assignee "$PRINCIPAL_ID" \
  --role "Key Vault Secrets User" \
  --scope "$KV_ID"
```

**5. Wire Key Vault references into the Container App**

```bash
az containerapp secret set \
  -g <rg> -n mcp-servicenow \
  --secrets \
    "servicenow-instance=keyvaultref:https://<kvName>.vault.azure.net/secrets/servicenow-instance,identityref:system" \
    "servicenow-client-id=keyvaultref:https://<kvName>.vault.azure.net/secrets/servicenow-client-id,identityref:system" \
    "servicenow-client-secret=keyvaultref:https://<kvName>.vault.azure.net/secrets/servicenow-client-secret,identityref:system"

az containerapp update \
  -g <rg> -n mcp-servicenow \
  --set-env-vars \
    "SERVICENOW_INSTANCE=secretref:servicenow-instance" \
    "SERVICENOW_CLIENT_ID=secretref:servicenow-client-id" \
    "SERVICENOW_CLIENT_SECRET=secretref:servicenow-client-secret"
```

To rotate a credential: update the Key Vault secret and create a new Container App revision (`az containerapp update --revision-suffix vN`).

---

## Audit logging

Every tool call emits one structured JSON line to stderr via the `AuditMiddleware` registered in [tools.py](tools.py). Azure Container Apps automatically ships container stderr to Log Analytics — no extra SDK, no log shipper, no file rotation.

**Log line shape** (one JSON object per `tools/call`):

```json
{
  "timestamp": "2026-05-25T10:30:00.123Z",
  "level": "info",
  "event": "tool_call",
  "tool": "search_records",
  "user": "jonathan.demeulemeester@company.com",
  "request_id": "req-abc-123",
  "args": {"table_name": "incident", "limit": 10},
  "duration_ms": 147.32,
  "status": "success"
}
```

Errors add `"status": "error"`, `"error": "<message>"`, and `"level": "error"`.

**User identity** is parsed from the `Authorization: Bearer <jwt>` header (claim priority: `preferred_username` → `upn` → `email` → `sub`). The JWT signature is NOT verified inside the container — Azure APIM / Front Door / Container Apps ingress must validate the token at the edge before the request reaches the MCP server. Without an Authorization header, `user` is `"unauthenticated"`. Under `stdio` transport (local dev), there is no HTTP context and identity tracking is unavailable.

**Sensitive arguments** matching `password`, `secret`, `token`, `key`, `auth`, or `credential` (case-insensitive substring in the parameter name) are written as `"[REDACTED]"`. Adjust the set in [audit_middleware.py](audit_middleware.py).

**Query audit logs in Azure**

In the Log Analytics workspace attached to the Container Apps environment:

```kql
ContainerAppConsoleLogs_CL
| where ContainerAppName_s == "mcp-servicenow"
| where Log_s contains '"event":"tool_call"'
| extend payload = parse_json(Log_s)
| project TimeGenerated, user=payload.user, tool=payload.tool,
          status=payload.status, duration_ms=payload.duration_ms,
          request_id=payload.request_id, args=payload.args, error=payload.error
| order by TimeGenerated desc
```

For long-term retention or compliance reporting, route the table to a dedicated Log Analytics workspace with a multi-year retention policy, or export to an immutable Storage account via a Diagnostic Setting.

**Dockerfile note**: ensure `PYTHONUNBUFFERED=1` so log lines flush to stderr immediately and are not buffered across container restarts.

---

## Transport modes

| `MCP_TRANSPORT` | How it runs | Use case |
|---|---|---|
| `stdio` (default) | subprocess via stdin/stdout | local Claude Code |
| `sse` | HTTP server | Docker, cloud, N8N, any network agent |

Override host/port:

```bash
docker run -d \
  -p 9000:9000 \
  -e MCP_TRANSPORT=sse \
  -e MCP_HOST=0.0.0.0 \
  -e MCP_PORT=9000 \
  --env-file .env.local \
  mcp-servicenow
```

**N8N**: MCP Client node → SSE URL.  
**LangChain / custom agents**: any MCP-compatible SSE client library.

---

## Dependencies

Production: `requirements.txt`  
Dev (pytest, coverage, tiktoken, pytest-asyncio): `requirements-dev.txt`  
Dev dependencies are never installed in the Docker image.

---

## Documentation

- [OAUTH_SETUP_GUIDE.md](OAUTH_SETUP_GUIDE.md) — ServiceNow OAuth 2.0 setup
- [MIGRATION_v3_to_v4.md](MIGRATION_v3_to_v4.md) — v3 → v4 migration guide
- [CHANGELOG.md](CHANGELOG.md) — full change history
- [ARCHITECTURE_REFACTOR_PLAN.md](ARCHITECTURE_REFACTOR_PLAN.md) — rationale behind v4.0 refactor sprints

---

## License

MIT — see [LICENSE](LICENSE).

---

Found a bug? [Open an issue](https://github.com/Papamzor/personal-mcp-servicenow/issues).
