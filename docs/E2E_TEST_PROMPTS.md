# End-to-End MCP Test Prompts

Natural-language prompts to paste into a chatbot that has this MCP server connected.
They exercise the 25-tool v5.0 "Boron" surface end-to-end against a real ServiceNow
instance.

**Substitute placeholders** (`INC0012345`, sys_ids, `CI0001000`, `KB0001234`, `VTB0012345`)
with real values from your instance.

**Everything is read-only except the 🔴 WRITE section.** Run 🔴 prompts only against a
sandbox / non-production instance.

---

## A. Search + filters
*Validates keyword-combine, connection pooling, filter operators.*

```
Search incidents for database server timeout
Search change requests for firewall upgrade rollback
Find incidents matching "vpn authentication failure"
Show me P1 and P2 incidents created this month
Show incidents with priority 1 created in the last 7 days
Filter incidents where state is not resolved or closed, priority 1 or 2
Find incidents assigned to group Fleet
Get full details for incident INC0012345
Find incidents similar to INC0012345
Show me the ServiceNow query syntax help
```

**Watch for:** a multi-word search returns records matching *any* keyword (not just the
first) in one round-trip. A reference-field query (`group Fleet`) that returns zero rows
should include a hint about sys_id / dot-walk. `get_record` returns the full detail field
set; `filter_records` / search return the lean essential set. The syntax-help prompt
should flag that commas don't work in `IN` lists and that CONTAINS silently returns zero
rows where LIKE is required.

---

## B. Priority incidents + knowledge

```
Critical incidents from the last 7 days
P1 and P2 incidents this week, include metadata
Search knowledge articles for password reset
List published KB articles in category Network
Search knowledge articles for "remote access"
List KB articles by workflow state, deduplicated by number
Check KB0001234 and KB0005678 for duplicates
```

**Watch for:** knowledge search now goes through `search_records`/`filter_records`
(the smart-KB reads were culled in v5.0 — no `input_text` silently discarded when a
category filter is set). `get_kb_articles_by_state` returns one row per number with
`current_state` + `version_count` (KB versioning collapsed). `check_kb_duplicates` is
read-only and safe.

---

## C. SLA presets
*Validates the SLA preset dispatcher — all six presets.*

```
Show active SLAs
Show breached SLAs from the last 14 days
Show SLAs breaching within the next 30 minutes
Show critical SLAs (P1/P2 over 80% consumed)
Show SLA performance for the last 30 days
Show SLAs by stage in_progress
Get SLA details for sys_id <sla_sys_id>
Show SLAs for task INC0012345
```

**Watch for:** `critical` and `performance` return curated field sets (not every column).

---

## D. CMDB
*Validates the concurrent table probe + value-encoding fix.*

```
List all CI types
Find all CIs of type cmdb_ci_server
Get CI details for CI0001000
Search CIs by name web-server-01
Search CIs in location "Building 5"
Quick CI search for PROD-DB
Find CIs similar to CI0001000
```

**Watch for:** `Get CI details` with no type specified resolves via a concurrent probe of
the candidate tables. The location-with-space search returns rows (special characters in a
value previously corrupted the query → silent zero-rows). An unknown `ci_type` on
`find_cis_by_type` / `search_cis_by_attributes` should error, not silently downgrade to
base `cmdb_ci`.

---

## E. Health check
*Validates the single-tool diagnostic that replaced the 5 v4.x auth/connectivity tools.*

```
Is the ServiceNow connection up
Check the ServiceNow connection and probe the incident table
Show me the current auth config
```

**Watch for:** one `health_check` call returns `server` liveness, `auth` config, and
`connection` status. A failed probe reports a classified `error` ({"code", "message"}) —
it never blames auth for what was actually a timeout. With a table named, a successful
probe adds `sample_fields` + `has_records`.

---

## F. 🔴 WRITE / mutating — sandbox only
*These change data. Use a non-production instance.*

```
Create a private task: short description "MCP e2e test", priority 3, state 1
Update private task VTB0012345: set state to 2
Update knowledge article KB0001234: set short_description to "Updated via MCP test"
Publish knowledge article KB0001234
Publish knowledge articles KB0001234 and KB0005678
Retire knowledge article KB0001234
```

**Watch for:** clean localized error strings on 400/403/404 (not stack traces); publish
runs a duplicate check first and blocks if duplicates exist; batch publish returns one
status row per article.

---

## Pass/fail checklist

| Area | Pass criterion |
|------|----------------|
| Connection pooling | No auth errors across a long multi-tool conversation; warm-call latency drops after the first request |
| Keyword-combine | `Search incidents for database server timeout` returns any-keyword matches in a single request |
| CMDB probe / encoding | Untyped `Get CI details` resolves; spaced-value CI search returns rows |
| Response contract | List success → `result`/`returned_count`/`truncated`; single record → `record` (never a 1-row `result` list); failure → `error: {code, message}` only |
| Token shape | `filter_records` lean fields vs `get_record` full detail; SLA `critical`/`performance` curated |
| Stdio invariant | The chatbot never sees protocol corruption / malformed tool responses |
