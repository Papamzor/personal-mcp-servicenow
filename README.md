# Personal MCP ServiceNow Integration

MCP server for ServiceNow integration. Uses FastMCP over stdio transport, OAuth 2.0 client credentials.

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![ServiceNow](https://img.shields.io/badge/ServiceNow-REST%20API-green.svg)](https://servicenow.com)
[![OAuth 2.0](https://img.shields.io/badge/Auth-OAuth%202.0%20Only-orange.svg)](https://oauth.net/2/)

---

## Support This Project

[![PayPal](https://img.shields.io/badge/PayPal-Support%20Development-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://www.paypal.me/papamzor)

---

## Release highlights

Current release: **5.0.1** (25 tools). The 5.0.0 "Boron" surface was breaking — culled 39 → 25 with one minimal response contract. If upgrading from v4, read [MIGRATION_v4_to_v5.md](MIGRATION_v4_to_v5.md). Full history in [CHANGELOG.md](CHANGELOG.md).

| Release | What changed |
|---|---|
| **5.0.1** | Two silent-data-loss fixes in `get_kb_articles_by_state`, both found live. A `draft` filter now finds drafts on **already-published** articles (the priority collapse hid them — live, 1 reported against 48 real); entries carry `states_present` and the state filter tests membership. The raw scan no longer inherits `max_results`, which had made a truncated fetch report the *wrong* `current_state`; a capped scan now says `scan_incomplete` instead of guessing. |
| **5.0.0 "Boron"** | Breaking. Tool surface culled **39 → 25** (5 diagnostics folded into one `health_check`; the NL/filter and smart-KB/SLA read tools removed — the host model does NL→filter natively). One **minimal response contract** across every tool: list `{result, returned_count, truncated}`, single-record `{record}`, write `{record, message}`, failure `{error:{code, message}}` — no more bare-string returns or `result`-is-sometimes-a-dict. `TableSpec` makes per-table config one source of truth; tool selection guidance is a structured registry injected into each docstring. ~2000 lines of dead NL-engine code removed. See MIGRATION_v4_to_v5.md. |
| **4.5.0** | Tool-selection docstring protocol on all 39 tools (WHEN TO USE / WHEN NOT TO USE / PREFER OVER / TABLES / SIDE EFFECT / EXAMPLE). Non-breaking — no tool added, removed, or re-signatured. The fatal footguns (LIKE-not-CONTAINS, reference fields hold sys_ids) now sit inline on `search_records` and `filter_records`. Static tool-selection preferred-hit rose 21/30 → 29/30, ambiguity 66 → 50 plausible paths. |
| **4.4.1** | Encoded-query values are carried faithfully. A `&` or a literal `%XY` in a search value no longer silently changes the query into a broader one; a `^` is refused rather than answered, because ServiceNow's syntax cannot carry it inside a value. A KB title containing `&` or `%` no longer blocks a publish. |
| **4.4.0** | Correctness release. A failed read is no longer reported as a missing record — reads raise a classified error instead of returning `None`, so a timeout, an expired credential and an empty table stop producing the same answer. KB publishing is fail-closed on an unusable duplicate check. Legacy domain filtering deleted, so result sets get larger. See the CHANGELOG's "Behavior changes" before upgrading. |
| **4.3.0** | Claude Desktop `.mcpb` packaging; Nuitka binary builds dropped from the release workflow. Absorbed the performance and token work planned as 4.2 (pooled httpx client, one OR-combined keyword query, concurrent CMDB probes). |
| 4.1.0 † | v4.0 shims deleted; KB write tools; `get_kb_articles_by_state`; `get_query_syntax_help`; `filter_records` truncation metadata. |
| **4.0.0** | SLA collapse, `filter/` + `http_layer/` + `oauth/` packages. Breaking — see below. |

† The shipped version string went `4.0.0` → `4.3.0` directly. Neither 4.1.0 nor 4.2.0 was ever released or tagged — "4.1.0" labels a body of work in the CHANGELOG, not an installable version.

### v4.0, in detail

v4.0 was a breaking release. See [MIGRATION_v3_to_v4.md](MIGRATION_v3_to_v4.md) if upgrading from v3.

| Change | Detail |
|---|---|
| SLA tool consolidation | 8 tools collapsed into 3 (`query_slas_by_task`, `query_slas_by_status`, `query_slas_custom`). Tool count: **37 → 32**. |
| `get_sla_details` bug fix | v3 built a `number={sys_id}` filter on `task_sla` (no `number` field). ServiceNow ignored it, returning 10,000 rows (~1.2M tokens). v4 routes via `sys_id=` — single record (~69 tokens). |
| `filter/` package | Filter construction, validation, NL parsing, and explanation consolidated into a single package. `query_validation.py` and `query_intelligence.py` became shims, deleted in 4.1.0. |
| `http_layer/` + `oauth/` packages | `make_nws_request` and `ServiceNowOAuthClient` split into focused packages. GET-path token-optimization invariants locked by 3 negative write-path tests. |

Backwards-compat shims kept all v3 import paths and test-patch targets working for one release cycle; they were deleted in 4.1.0. Import from `http_layer`, `oauth`, and `filter` directly.

---

## Easy install — Claude Desktop (no technical knowledge needed)

This works on Windows 11 and macOS and takes about 2 minutes.

**Before you start:** ask your IT department for 3 things:
- Your company's ServiceNow address (looks like `https://company.service-now.com`)
- A Client ID
- A Client Secret

**Steps:**

1. Open the [Releases page](https://github.com/Papamzor/personal-mcp-servicenow/releases/latest) and download the file ending in `.mcpb`.
2. Double-click the downloaded file. Claude Desktop will open an install prompt — click **Install**. (If double-clicking doesn't open Claude Desktop, go to Claude Desktop → **Settings** → **Extensions** → **Advanced settings** → **Install Extension…** and pick the file instead.)
3. Fill in the three boxes with the values your IT department gave you, then save.
4. Start a new chat and try asking: "Show me my open ServiceNow incidents".

**First use note:** the first chat after installing can take a minute while the extension sets itself up. This only happens once.

**Something not working?**
- "Server disconnected" — double-check the three values you entered (Claude Desktop → Settings → Extensions → ServiceNow for Claude → Configure).
- Ask Claude to "test the ServiceNow connection" — it will tell you what's wrong.
- On a company network, the one-time setup needs access to `pypi.org`, `files.pythonhosted.org` and `astral.sh`. Ask IT to allow these if setup doesn't finish.

IT readers: see [docs/MCPB_BUILD.md](docs/MCPB_BUILD.md) for build, release and proxy details.

---

## Installation (developers)

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

## Available tools (25)

> **v5.0 "Boron" (Tier 2 cull, 39 → 25), deletes-only.** Removed the redundant
> `get_record_summary`; the three smart-KB read tools; `similar_slas_for_text`;
> the five NL/filter tools (the host model builds and explains filters
> natively); and folded the five diagnostics into one `health_check`.

### Generic table tools (4)

Work across all supported tables: `incident`, `change_request`, `sc_req_item`, `sc_task`, `universal_request`, `kb_knowledge`, `vtb_task`, `task_sla`.

- `search_records(table, query)` — text similarity search
- `get_record(table, number)` — full detail fields for a single record
- `find_similar(table, number)` — records similar to an existing record
- `filter_records(table, filters, fields=None, max_results=100)` — field-value filters with operators and date ranges; response carries `returned_count` / `truncated`

### Query-syntax help (1)

- `get_query_syntax_help()` — encoded-query operator reference (LIKE vs CONTAINS, reference-field dot-walking)

### Priority incidents (1)

- `get_priority_incidents(priorities, start_date, end_date, additional_filters, include_metadata)`

### Knowledge base — read (1)

- `get_kb_articles_by_state(workflow_state, category, kb_base, max_results)` — collapses ServiceNow KB versioning to one row per `number`, with `current_state` (the canonical/live state), `states_present` (every state that number has a version in) and `version_count`. `workflow_state` matches on `states_present` membership, so a draft on an already-published article is found. `max_results` caps the returned entries; the raw scan runs to its own 1000-row ceiling and sets `scan_incomplete` + `warning` if it hits it. For topic search use `search_records("kb_knowledge", ...)`; for a category use `filter_records("kb_knowledge", {"kb_category": ...})`.

### Knowledge base — write (5)

- `update_knowledge_article(article_number, update_data)`
- `publish_knowledge_article(article_number)` — fire-and-verify; a POST is not trusted as truth
- `publish_knowledge_articles(article_numbers, concurrency)` — batch, capped at 20 numbers, flat per-article status rows
- `retire_knowledge_article(article_number)`
- `check_kb_duplicates(article_numbers, concurrency)` — the publish-time duplicate check, standalone

### Private task CRUD (2)

- `create_private_task(task_data)` — creates vtb_task record
- `update_private_task(task_number, update_data)` — PATCH update

### SLA management (4)

- `get_sla_details(sla_sys_id)`
- `query_slas_by_task(task_number)`
- `query_slas_by_status(status, days?, threshold_minutes?, stage?, extra_filters?)` — status enum: `"active"`, `"breached"`, `"breaching"`, `"critical"`, `"by_stage"`, `"performance"`
- `query_slas_custom(filters, fields?, days?)` — escape hatch; `fields=None` defaults to `ESSENTIAL_FIELDS["task_sla"]`

### CMDB (6)

- `find_cis_by_type(ci_type, detailed=False)` — any `cmdb_ci*` table
- `search_cis_by_attributes(name=None, ip_address=None, location=None, status=None, ci_type=None, detailed=False)` — at least one attribute required
- `get_ci_details(ci_number, ci_type=None)` — probes the common CI tables when `ci_type` is omitted
- `similar_cis_for_ci(ci_number)`
- `get_all_ci_types()` — live `sys_db_object` query, not a static list
- `quick_ci_search(search_term)`

### Diagnostic (1)

- `health_check(probe_table=None)` — server liveness + auth config + live ServiceNow probe; `probe_table` also returns that table's sample field names. Replaces the former `nowtest` / `now_test_oauth` / `now_auth_info` / `nowtestauth` / `nowtest_auth_input`.

---

## Architecture

```
MCP Client (Claude)
  ↓ stdio / sse
tools.py (FastMCP — 25 tools)
  ↓
generic_tool_wrappers.py   consolidated_tools.py   vtb_task_tools.py
cmdb_tools.py   utility_tools.py   intelligent_query_tools.py
  ↓
generic_table_tools.py (core query engine, pagination, deterministic sort)
  ↓
filter/                     (v4.0 Sprint 1)
  builder.py                — ServiceNowQueryBuilder
  validator.py              — validate_query_filters, validate_and_correct_filters
  intelligence.py           — QueryIntelligence (NL → filter; no backref to builder)
  explainer.py              — QueryExplainer
  models.py                 — TableFilterParams, QueryValidationResult
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
- [docs/MCPB_BUILD.md](docs/MCPB_BUILD.md) — Claude Desktop Extension (`.mcpb`) build & release

---

## License

MIT — see [LICENSE](LICENSE).

---

Found a bug? [Open an issue](https://github.com/Papamzor/personal-mcp-servicenow/issues).
