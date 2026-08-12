# Changelog

All notable changes to the Personal MCP ServiceNow project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [5.0.1] — 2026-08-12

Two silent-data-loss defects in `get_kb_articles_by_state`, both found by live
testing against a real KB (363 raw rows) rather than by the test suite. Neither
raised an error — the tool returned confidently wrong data.

### Fixed

- **Drafts on already-published articles were invisible to a `draft` filter.**
  The `workflow_state` filter tested equality against `current_state`, the
  priority winner of `published > draft > review > outdated > retired`. Because
  re-drafting an update leaves a `published` row beside the new `draft` one,
  `published` won and the article dropped out of the filtered result. Measured
  live: the tool reported **1** pending draft where a raw `filter_records` saw
  **48** — 47 of 48 real work items silently missing, in the *common* KB-churn
  case (edits to existing articles, not new ones).

  Each entry now carries **`states_present`** — every distinct `workflow_state`
  across that number's versions — and `workflow_state` filters on membership in
  it. `current_state` keeps its meaning (the canonical/live state) for
  post-publish verification. Because `published` is the top-priority state,
  `current_state == "published"` already implies membership, so the published
  view is unchanged; only the lower-priority states widen, which is the fix.

- **A capped raw scan reported the wrong `current_state`, not merely fewer rows.**
  `max_results` capped the *raw row fetch*, and de-duplication then ran on
  whatever arrived. The scan sorts `sys_created_on` DESC, so a recent `draft`
  row could land inside a 100-row cap while its older `published` sibling fell
  off the end — and the article came back as `current_state: draft`. Rows for one
  number are scattered across the sort, so truncation poisons *every* entry's
  state, not just the omitted ones.

  The raw scan is now decoupled from the output cap: it always runs to
  `KB_STATE_SCAN_LIMIT` (1000 rows), while `max_results` caps the deduped
  entries returned. If the scan itself hits its ceiling the response carries
  `scan_incomplete: true` and a `warning` naming the risk, instead of serving a
  guessed state as authoritative.

- `max_results` outside 1..1000 now returns a `VALIDATION` error instead of
  raising an unhandled pydantic `ValidationError`.

### Behavior changes

- `truncated` on this tool now means **the deduped output was capped at
  `max_results`**. It previously reflected the raw fetch. A capped raw scan is
  reported separately as `scan_incomplete` — the two were one flag, which
  conflated "there are more articles than I returned" with "the states I
  reported may be wrong". Only the second makes the returned rows untrustworthy.
- `workflow_state="draft"` (and `review`, `outdated`, `retired`) now return
  strictly more articles. `workflow_state="published"` is unchanged.

### Added

- `tests/test_kb_state_rollup.py` — 17 regression tests covering both defects.
- Regression tests pinning that retired/outdated duplicates do **not** block a
  publish while a live duplicate beside them still does. This behavior was
  already correct but untested, and was flagged as unverified in the live-test
  handoff.

## [5.0.0] — Boron — 2026-08-11

The MCP-surface redesign. **Breaking**: the tool surface is culled 39 → 25, and
every tool now returns one minimal response contract instead of the previous mix
of bare strings, `{"message": ...}` dialects, and `result`-is-sometimes-a-dict
shapes. If you upgrade, read [MIGRATION_v4_to_v5.md](MIGRATION_v4_to_v5.md) — it
lists every removed tool with its replacement and every response-shape change.

**Why.** The v4 surface had grown 39 tools with overlapping intents and five
different auth/health diagnostics; a host model wasted selection budget choosing
between near-duplicates, and each tool answered in its own ad-hoc shape. v5 keeps
only tools whose absence would lose capability, and gives the survivors one
predictable envelope.

### Removed (15 tools)

- **5 diagnostics → 1.** `nowtest`, `now_test_oauth`, `now_auth_info`,
  `nowtestauth`, `nowtest_auth_input` are replaced by a single
  `health_check(probe_table=None)`.
- **5 NL / filter tools.** `intelligent_search`, `explain_servicenow_filters`,
  `build_smart_servicenow_filter`, `get_servicenow_filter_templates`,
  `get_query_examples` — the host model does natural-language → filter natively,
  so the in-repo NL engine (~2000 lines) was dead weight. Use `search_records` /
  `filter_records`.
- **3 smart-KB reads.** `similar_knowledge_for_text`, `get_knowledge_by_category`,
  `get_active_knowledge_articles` (the old "smart" search silently discarded the
  text when a category was set). Use `search_records("kb_knowledge", …)`,
  `filter_records("kb_knowledge", {"kb_category": …})`, or
  `get_kb_articles_by_state("published")`.
- **`similar_slas_for_text`** — queried a `short_description` that `task_sla`
  lacks, so ServiceNow silently returned an arbitrary page; it never worked. Use
  `filter_records("task_sla", {"task.short_description": "LIKE…"})`.
- **`get_record_summary`** — folded into `get_record`.

### Changed (breaking)

- **Response contract (§3.1) across every tool.** List success is
  `{"result": [...], "returned_count": int, "truncated": bool}`; a single record
  is `{"record": {...}}` (or `{"record": null}` for a miss) — never a one-row
  `result` list; a write success is `{"record": {...}, "message": str}`; a failure
  is `{"error": {"code": <VALIDATION|NOT_FOUND|AUTH|FORBIDDEN|TIMEOUT|HTTP|INTERNAL>,
  "message": str}}` and nothing else. Bare-string returns and the
  `{"result": [...], "message": "Found N records"}` dialect are gone.
- **`get_record`** now returns `{"record": {...}}`, not `{"result": [{...}]}`.
- **Write tools** (`create_private_task`, `update_private_task`,
  `update_knowledge_article`, `publish_knowledge_article`,
  `retire_knowledge_article`) return `{"record": {...}, "message": ...}` on success
  and `{"error": {"code", "message"}}` on failure — no more `dict | str` unions. A
  2xx write with no record body is reported as `error` (`INTERNAL`, unconfirmed),
  not as success.
- **CMDB tools** lost their 16 bare not-found strings: an empty result is a
  success shape (`{"result": []}` / `{"record": null}`), and `get_ci_details`
  returns the CI under `record`.
- **`get_priority_incidents`** dropped its deprecated `**kwargs` filter path; pass
  extra field filters via `additional_filters`.

### Added

- **`health_check(probe_table=None)`** — the single diagnostic entry point
  (server liveness, auth config, live connection; optional table field peek).
- **`Table_Tools/response.py`** — `error_response` / `list_response` /
  `record_response`, the contract's constructors, plus a surface-wide
  `tests/test_tool_response_contract.py` that drives every registered tool through
  the real dispatcher.
- **`table_spec.py`** — one `TableSpec` per table as the single source of truth;
  `TABLE_CONFIGS` / `ESSENTIAL_FIELDS` / `DETAIL_FIELDS` / `TABLE_ERROR_MESSAGES` /
  the identity and text-search maps are derived from it. `number_field` makes the
  `task_sla` "no record identity" foot-gun structural.
- **`tool_registry.py`** — the WHEN TO USE / WHEN NOT TO USE / PREFER OVER
  selection guidance is now structured data, injected into each tool's docstring
  (above the Args section, so it reaches the served MCP description) and mandatory
  at registration.

### Behavior changes to check before upgrading

- Any client parsing tool output must handle the new shapes — most notably
  `get_record` (`record`, not `result[0]`) and the write tools (`record` +
  `message`, not a bare dict or string).
- 15 tool names no longer exist; see the Removed list and MIGRATION_v4_to_v5.md
  for the one-to-one replacements.

### Internal

- ~2000 lines of dead NL-engine code removed (`filter/intelligence.py`,
  `filter/explainer.py`, `query_table_intelligently` + helpers).
- Per-response token-footprint guards extended beyond SLA to
  `filter_records` / `search_records` / `get_record` / a CMDB list, pinning the
  envelope overhead so an unconditional `meta` block cannot creep back.
- Suite: 1136 passing, 0 skipped. Tool-listing footprint 6743 tokens (ceiling
  7200). Static tool-selection preferred-hit floor 28/30.

## [4.5.0] - 2026-08-10

Tier 1 of the MCP-surface redesign: a **docstring protocol** on all 39 tools so a
client can tell them apart from the intent alone. Non-breaking — no tool is added, removed, or
re-signatured (`tests/test_integration.py` still asserts 39). Only docstrings, two inline
footguns, and test floors change.

**Why docstrings, and why measured.** The tool docstrings are what an MCP client sends the model
to choose between tools; they are also the cheapest lever, sent once per conversation and cached.
The point of the tier is not prose but a **measurement** — whether the surface is discriminating
enough — so the change is gated on tool-selection numbers, not on the docstrings reading nicely.

### Added

- **A six-field protocol on every tool**: `WHEN TO USE` / `WHEN NOT TO USE` / `PREFER OVER` /
  `TABLES` / `SIDE EFFECT` / `EXAMPLE`. The register matches the existing `filter_records`
  reference. `SIDE EFFECT: WRITE` is stated on every write tool (the four KB writes and the two
  private-task tools); everything else is marked read-only.
- **The fatal footguns moved inline** onto the two entry points, not left only in
  `get_query_syntax_help` (plan §3.3): use `LIKE`, never `CONTAINS` (a GlideRecord scripting
  operator, silently ignored in an encoded query, returns zero rows); reference fields
  (`assignment_group`, `assigned_to`, `caller_id`, `cmdb_ci`) hold sys_ids, so filter by sys_id or
  dot-walk. `search_records` gained them; `filter_records` already carried them.
- **A tool-listing token-footprint budget** (`tests/test_token_footprint.py`). The per-response
  budgets never covered the listing payload; this one does, and records the trade below.

### Changed

- **Static tool-selection preferred-hit rose 21/30 → 29/30, acceptable 22/30 → 29/30, and total
  ambiguity fell 66 → 50 plausible paths** (`tests/test_tool_selection.py`). The floors are raised
  to lock the gain in. Fixes include the costliest class — a *write* mis-selection where
  "set my private task VTB0001234 to closed complete" chose `create_private_task` over
  `update_private_task` — plus the full-details, change-request-filter, SLA-by-task, SLA-by-text,
  server-crash-search, password-reset and batch-publish intents.
- **The one intent the static router cannot fix is `is the ServiceNow connection up`**, which still
  scores to `build_smart_servicenow_filter`: `servicenow` sits in that tool's *name* and wins the
  bag-of-words tie no docstring can break. It is a name-bound collision, deferred to Tier 2's
  diagnostic/filter cull. An **LLM-reasoned pass** over the same 30 intents resolves it correctly
  (reading `now_test_oauth`'s "verify ServiceNow is reachable — connectivity/health probe" against
  `build_smart_servicenow_filter`'s "never contacts ServiceNow"), reaching 30/30 preferred — which
  is exactly why the plan gates the tier on an LLM read and not the static router (§3.2).
  *Caveat:* that 30/30 is a reasoned judgement, not an independent adversarial harness; the
  CI-enforced, reproducible number is the static 29/30.
- **Tier 2 scope signal.** Docstrings alone carry *selection* nearly all the way, so Tier 2's
  39→25 cull is justified by residual name-collisions (connection-up; the KB write-tool band that
  scores 6 on "knowledge articles about password reset" from `knowledge`+`article` in their names)
  and surface simplicity — not by a selection deficit. "Count is not the metric; overlap is."
- **Tool-listing token footprint grew 4693 → 8946 cl100k_base tokens (+91%)**, measured in a
  worktree at each commit. This is the price of the protocol: a one-time, cached, per-conversation
  cost that buys the selection gain and averts far more expensive wrong-tool calls. The
  per-response token budgets (the token-optimization invariant) are untouched. Tier 2's cull is the
  lever that brings the listing size back down.
- **One seeded-collision ratchet re-derived** (password-reset, 5 → 6 plausible paths). Lifting
  `similar_knowledge_for_text` to the top of that intent raised the 80% band threshold, admitting
  the name-bound KB cluster; the top pick is now correct and total ambiguity still fell.

## [4.4.1] - 2026-08-10

Closes the one correctness defect 4.4.0 shipped with a "Known limitation" heading: a `^`, `&` or
literal `%XY` inside an encoded-query **value** produced a query that differed from the one
requested — and always a broader one. Same family as the silently-dropped-filter class 4.4.0
was about: the server answered a question nobody asked and presented the rows as matches.

**Why it needed its own release.** The fix is a coordinated flip. The transport was silently
normalising every producer's query, so it could not stop doing that until every producer escaped
its own values, and no producer could usefully escape while the transport undid it. Half a flip
gives either double-encoded values or raw structural characters, so it lands in one commit with
a test matrix rather than incrementally.

### Fixed

- **`&` in a query value no longer truncates the condition.** It was never mis-parsed *within*
  the query — it escaped `sysparm_query=` and became a sibling URL parameter, so
  `nameLIKESales & Marketing` searched for "Sales " and sent a stray `Marketing` parameter.
  `&` is not an encoded-query operator (conditions separate on `^`), so it left the transport's
  safe-set; values are now escaped at the producer and that escaping survives.
- **A literal `%XY` in a value is no longer decoded on its way out.** The transport unquoted
  before re-quoting, so a search for `Deal 20%2C off` ran against `Deal 20, off` and `%41dmin`
  against `Admin`. `unquote` never raises, so nothing announced it. Values escape their own `%`
  to `%25` now.
- **Sixteen escaping seams, not the four the plan listed.** Derived from the code: the exact-match
  default, the operator-prefix handler, the suffix-operator handler, the date-range `>=`/`<=`
  branch, all three priority builders, the caller-exclusion list, `_build_additional_filters`, and
  the CMDB/KB/VTB call sites. The three the plan missed included the *default* handler — the one
  most callers reach; review then found four more that were escaped correctly but **unasserted**
  (`_build_priority_filter`'s single-priority branch and the CMDB `ip_address`/`location`/`status`
  attributes), so reverting any of them left the suite green. A taint-propagating AST scan over the
  condition-building closure now fails by name if a new terminal handler forgets. Its first version
  was a regex with a hardcoded name whitelist, which `priorities[0]` walked straight past — a
  subscript is not a bare name.
- **A `sys_id`/`number` lookup that selects a write target is escaped.** `kb_article_tools`,
  `cmdb_tools` and `vtb_task_tools` resolve a record by `number=` and then PATCH or attribute the
  result; a `^` there could have OR'd in a second condition and resolved to a *different* record.
  Five such lookups, and review caught that only one of them was pinned — reverting the escaping
  on the other four left the suite green. An AST scan across `Table_Tools/` now names any
  `number=` interpolation that is not escaped, following a one-hop local assignment so an
  already-escaped variable is not a false positive.

### Changed

- **A `^` in a query value is refused instead of answered.** It is unrepresentable, not merely
  mis-transported: ServiceNow's parser splits on the *decoded* value, so no encoding can carry
  it. Affected tools return `{"error": {"code": "VALIDATION", ...}}` and send no request.
  `^OR` inside a filter value is unchanged — it is still read as caller-supplied query structure,
  which is what an LLM writing `{"priority": "1^ORpriority=2"}` means.
- **A `^NQ` new-query-reset in a filter value is refused instead of silently dropped.** The drop
  removed the poisoned condition but still ran the rest, handing back real-looking rows from a
  query the caller did not ask for. The check now runs at the *top* of
  `_build_query_condition`: review found it sat below the pre-built-fragment early returns, so
  `filter_records({"_complete_caller_exclusion": "caller_id!=x^NQstate=99"})` walked straight past
  it, and `_build_additional_filters` — a second, parallel assembly path — never reached it at
  all, so `get_priority_incidents(additional_filters={"_date_range": "1^NQstate=99"})` sent the
  reset to ServiceNow verbatim and returned rows. Both verified live before and after the fix.
- **Every structural paste of a caller-built fragment refuses `&`.** Four handlers return a
  caller value verbatim because the value *is* the fragment — the bare-OR repair, a complete
  `^OR` filter, the `BETWEEN` early return, and the already-`caller_id!=` passthrough. They
  cannot escape it, so `&` is refused there as it is for the underscore fragment keys. Found in
  the second review, and invisible from `filter_records`: that route runs
  `_encode_query_string` and escaped the `&` before the URL was built, while
  `query_table_with_generic_filters` did not, so `{"priority": "1^ORpriority=2&x"}` reached
  ServiceNow as `priority=1^ORpriority=2` plus a stray `x` parameter. Reachable from
  `similar_knowledge_for_text` and `get_knowledge_by_category`, whose `category`/`kb_base` land
  in exactly that path. A `&` in an *ordinary* value ("Payroll & Benefits") is still escaped and
  carried, not refused.
- **The three pre-built-fragment filter keys are guarded.** `_date_range`,
  `_complete_caller_exclusion` and `_complete_query` carry their own operators, so they cannot be
  escaped and `^` has to be allowed — `build_date_filter` emits
  `sys_created_on>=A^sys_created_on<=B`. `&` is refused there instead, because it is not an
  operator and can only truncate the fragment. Previously a `&` in `_date_range` silently cut the
  query short at it.
- **Filter field *names* are validated.** The keys of a `filters` dict are caller-supplied and
  nothing checked them, so `{"x^NQstate=99": "1"}` built `x^NQstate=99=1` — the same unscoped
  table read the value guard refuses, arriving through the key. A field name must now be
  identifier characters plus `.` for dot-walking (`task.priority`).
- **A KB title containing `&` or `%` no longer blocks a publish.** The duplicate check refused
  those as inconclusive because it could not trust the query; it can now. `^` still blocks —
  fail-closed, since a check that ran broader than asked cannot clear a publish. `KB_QUERY_UNSAFE_CHARS`
  went from `("^", "&")` to `("^",)` and the percent round-trip check is gone.
- **`Table_Tools.generic_table_tools._encode_query_string` is an alias for the transport's
  encoder.** It was a second, independent `quote(safe=...)` with a different safe-set and no
  idempotency, so a value could pass through two encoders that disagreed and be round-trip-stable
  by luck. One implementation now.

### Added

- **`filter/value_encoding.py`** — `encode_query_value`, `QueryValueError`, `QUERY_VALUE_SAFE`.
  The producer half of the contract. Its safe-set is deliberately the transport's minus `^`, and
  a test pins that relationship: the transport's idempotency-by-decoding is only sound while
  decoding cannot resurrect a structural character.
- **`tests/test_query_value_encoding.py`** and **`tests/sn_query_probe.py`** — the matrix asserts
  the value ServiceNow's parser *decodes*, plus the condition count and the URL parameter count,
  across 24 characters and 12 producer seams. Asserting on the encoded URL string is how you
  write a test that passes while the query is still wrong. 15 mutations were run against the
  fix; each is caught by a named behavioural test.
- A regression test pinning the text-search tokenizer's `\b[a-zA-Z]{4,}\b` character class. The
  text-search tools were never affected by any of this, but only because a keyword cannot contain
  `^`, `&` or `%` — protection nobody designed, which a widened tokenizer would have removed
  silently.

### Known limitation

`_has_operator_in_value` still treats any `=` in a filter value as caller-supplied operator
syntax, so `{"short_description": "Cost=Center"}` builds a condition on a field that does not
exist, which ServiceNow drops silently. Not an encoding defect — escaping cannot decide whether
the caller meant an operator — and pinned by a test rather than left unrecorded. The value
round-trips correctly once the operator is explicit (`LIKECost=Center`).

## [4.4.0] - 2026-08-06

Tier 0 of the v5 "Boron" redesign: correctness only, no tool-count changes. Still 39 tools.

**The theme is that the server stops answering questions it does not know the answer to.**
Before this release a failed read returned `None`, which every consumer turned into "no
matching records" — so a 30-second timeout, an expired credential and an empty table all
produced the same reply. Six months of "it says there are no results" could mean any of them.

That one conflation is the root of most entries below, and it appeared in more places than
expected once the reads were typed: a CMDB timeout attributed a server to the wrong table, a
failed duplicate check let a KB article publish unchecked, a failed lookup told users their
task did not exist and then declined to update it.

**Upgrade note.** Read the "Behavior changes" section before upgrading. Result sets get larger
(#58), some inputs that used to return rows now return errors (#60, #61), and a KB publish can
now be refused where it previously went ahead (#66). All of those are deliberate.

### Added

- **Knowledge article SEO fields** — `meta` and `meta_description` are updatable via
  `update_knowledge_article` and appear in detail reads. They were blocked by the write
  allowlist. (#54)
- **`Table_Tools/read_helpers.py`** — `is_read_failure`, `carry_partial`,
  `carry_partial_after_filter`. The failure and partial-read shapes travel up through several
  modules that re-wrap each other's responses; these keep both intact, because re-wrapping a
  failure as an empty result is easy to reintroduce and reads as ordinary code.
- **A test that derives its own subject matter.** `test_every_read_path_consumer_handles_the_raise`
  walks the AST for every module importing `make_nws_request` and asserts each has an
  `except ServiceNowRequestError` arm. Detection is by *import*, not by a text match on
  `make_nws_request(` — an aliased import binds the name and never spells it at the call site,
  so a text match would skip the module silently. A new consumer without a handler fails the
  suite, named. (#67, #68)
- Golden intent set for tool-selection baselining. (#57)

### Behavior changes

Each of these changes an answer a caller previously received.

- **A failed read is never reported as a missing record.** A failed GET now raises
  `ServiceNowRequestError`, and consumers return `{"error": {"code", "message"}}` with a code
  from a fixed seven-value vocabulary (`VALIDATION`, `NOT_FOUND`, `AUTH`, `FORBIDDEN`,
  `TIMEOUT`, `HTTP`, `INTERNAL`). `NOT_FOUND` is used only when ServiceNow actually returned
  404. An empty result set keeps its existing not-found message — empty is still success, and
  deciding what it means stays the consumer's job. (#59, #64-#68)
- **A partial read keeps its rows.** A page failing mid-pagination returns the rows already
  collected plus `partial: true` and the error, instead of discarding them; a first-page failure
  is a plain error. If a filter empties a partial result, the response is the failure, not "no
  matches" — a confident "nothing found" next to an error saying the read never finished is
  self-contradicting, and the rows that would have matched may be in the pages that failed. (#64)
- **KB publish is fail-closed.** The duplicate check now has three outcomes — clear,
  duplicates-found, inconclusive — and only *clear* permits a publish. Previously a failed
  check returned `[]`, the one value `publish_knowledge_article` reads as "clear to publish", so
  a timeout published the article with the guard skipped and reported success. Inconclusive
  covers: the read failed; the title contains `^` or `&`, which an encoded query cannot carry
  inside a value; the title contains a `%XY` sequence, which the read path decodes so
  ServiceNow would be searched for a different string; or the result page hit its new
  `sysparm_limit=200` and a duplicate may be off the end of it. (#66)
- **An unreadable publish verification no longer re-fires the workflow.** A failed verify read
  was indistinguishable from "not published yet", so the publish was submitted a second time —
  a write retried because a *read* failed. Now one submission, reported as `unconfirmed` with
  the article's state unknown, because the write did go out and may have committed.
  `publish_knowledge_articles` gains that status alongside `published`, `blocked` and `error`.
  (#66)
- **`check_kb_duplicates` no longer answers "no duplicates" from a check that did not run.**
  Rows for an indeterminate check omit `has_duplicate` entirely and carry
  `duplicate_check: "inconclusive"` plus `error`. Previously such a row read
  `has_duplicate: False` with no error field — and this is the tool the publish-unconfirmed
  message tells users to re-check with. (#66)
- **KB and private-task writes that return no record report "could not be confirmed"** instead
  of "<operation> successful but no data returned". The old wording asserted the write had
  landed on the strength of an empty response, which is the one thing an empty response cannot
  establish. (#66)
- **Domain filtering deleted.** Incident queries no longer silently append
  `category != Payroll / People Support / Workplace`, and `sc_*` queries no longer append a
  `People_Pay` catalog exclusion plus 11 assignment-group exclusions. **Result sets get larger
  and noisier** — this is the change most likely to be noticed. The exclusions were a legacy
  policy from an earlier deployment; the server is authorized-personnel-only, so they bought
  nothing while making every query wider, slower and harder to reason about. (#58)
- **A CMDB probe failure fails the whole lookup** instead of counting as "the CI is not in this
  table". Every CI also lives in the base `cmdb_ci` table, so a timeout on `cmdb_ci_server`
  used to make a server CI appear to live in `cmdb_ci` — the wrong table, reported
  confidently. An incomplete probe set supports neither "not found anywhere" nor attribution to
  a less specific table. A failure *after* a hit is ignored: the higher-priority table already
  decided. (#65)
- **CMDB tools return an error object rather than a not-found string on failure.** Five guards
  of the form `if data and data.get('result')` were collapsing a failed read into
  `NO_CIS_FOUND_FOR_TYPE`, `CI_NOT_FOUND`, `NO_CI_TYPES_FOUND` and friends. The module's return
  type is `dict | str` for now; the strings go in a later tier. (#65)
- **`ci_type` is validated by shape.** A value that is not a `cmdb_ci*` table name returns an
  error instead of rows from a different table, and cannot smuggle query parameters into the
  URL path. `get_all_ci_types` renames `record_count` → `number_prefix_ref`: the underlying
  `sys_db_object.number_ref` is a reference to the table's numbering configuration, never a row
  count, and the old name invited callers to read it as a population figure. Use
  `find_cis_by_type(ci_type)` and read `count` if you need one. (#60)
- **`task_sla` is guarded on the identity tools.** `search_records`, `get_record_summary`,
  `get_record` and `find_similar` return an error for `task_sla` instead of unrelated rows —
  the table has no `number` prefix and uses `stage` rather than `state`, so those tools were
  answering with whatever came back. `similar_slas_for_text` and natural-language search on
  `task_sla` return actual matches instead of an arbitrary page, by resolving the text-search
  field from the table rather than asking callers to pass it. (#61)
- **An explicit `auth_type` other than `oauth` raises `ConfigError`** at validation instead of
  being accepted and then failing at request time. (#56)
- **A pre-write lookup failure is no longer reported as a missing record.**
  `update_knowledge_article`, `publish_knowledge_article`, `retire_knowledge_article` and
  `update_private_task` return the classified failure; a genuinely absent record keeps its
  existing "not found" message. Previously a timeout during the `sys_id` lookup told the user
  their article or task did not exist, and silently declined to write it. (#66, #67)
- **The auth-test tools name the actual failure.** `nowtestauth` answered "Authentication test
  failed" for any failure including a timeout, and `nowtest_auth_input` guessed "table may not
  exist or no permissions" for a read that never completed. Both are what someone reaches for
  while trying to find out what is broken, and both were prepared to blame the wrong thing.
  (#67)

### Fixed

- **Read-failure classification.** `ValueError` was reported as "response is not valid JSON",
  because `json.JSONDecodeError` subclasses it and the handler paired them — so a missing
  `.env`, which raises `ValueError("Missing OAuth configuration")` *before any request*, was
  reported as a JSON parse failure. Separately the OAuth exception hierarchy fell through to
  `INTERNAL`, so a wrong client secret read as "unexpected internal error" while the identical
  failure arriving as an httpx 401 mapped to `AUTH`. (#59)
- **Response flattening is inside the error-handling boundary.** It had drifted outside, which
  would have propagated a parser failure uncaught to MCP clients for every read caller. (#59)
- **`ci_type` matched with `fullmatch`, not `match`.** Python's `$` also matches immediately
  before a single trailing newline, so `"cmdb_ci_server\n"` passed the validation that was
  meant to close a path-injection hole. (#60)
- **`search_field` plumbing restored.** Merging #61 after #58 kept #61's docstrings and call
  sites while taking the pre-#61 code, so the signature, an import and a format placeholder all
  vanished while everything referencing them stayed. Docstrings surviving a conflict resolution
  is not evidence the code did. (#63)
- **Test coverage on the two least-tested modules.** `Table_Tools/cmdb_tools.py` went from
  62.63% to 88.64% line coverage — its existing test file patched the module's own bound
  attributes and so asserted nothing about the real functions. `table_tools.py` went from 13.79%
  to 100%; it had no tests of its own at all, which is why it went unnoticed as an unmigrated
  read-path consumer until the migration was nearly finished. (#65, #67)

### Removed

- The `_legacy_none_shim` / `_TYPED_CALLERS` / `_calling_module` migration scaffold. It let the
  five consumer modules be migrated one PR at a time without exposing a half-migrated module,
  and its deletion is what makes the read contract unconditional. (#68)
- Domain category and catalog exclusion filtering. (#58)
- The unusable basic-auth credential path. (#56)

### Internal

Listed so a merge log diffed against this file shows no silent gaps.
`.gitignore` and stale-artifact cleanup (#53), SonarQube test-smell fixes (#55), doc rot plus
the backfilled 4.3.0 changelog (#62). The `v4.3.0..HEAD` merge range also contains Bitbucket-
numbered duplicates (#49-#52) of work already released in 4.3.0 — an artefact of the dual-remote
history, not additional changes.

One of these is visible at runtime, narrowly: #62 corrected the `how_to_use` hint returned by
`get_servicenow_filter_templates`, which pointed at `getIncidentsByFilter`, a function that no
longer exists. Copy in a tool's output, not behaviour.

### Known limitation

**`^` and `&` inside an encoded-query *value* produce a query that differs from the one
requested — and it runs broader.** `ensure_query_encoded` unquotes before re-quoting and keeps
the ServiceNow operator characters in its safe set, so percent-encoding a value at the call site
does not survive.

> **Fixed in [4.4.1].** `&` and a literal `%XY` are carried faithfully; `^` is refused rather
> than answered. Kept here as the record of what 4.4.0 shipped with.

The two fail by different mechanisms, and `&` is the more severe:

- `^` splits the value into two **conditions** inside ServiceNow's own encoded-query parser. It
  is worse than a leak — it is genuinely *unrepresentable* inside a value, because the parser
  splits on it after URL-decoding and the syntax has no escape mechanism. No encoder change can
  carry it; the only options are refusing the value or restructuring the query.
- `&` escapes `sysparm_query=` and becomes a **sibling URL parameter**, truncating the condition
  at the `&` and appending a stray parameter — it breaks out of the query string itself rather
  than being mis-parsed within it. Unlike `^` this one is representable, and survives correctly
  if the encoding is preserved, so it is fixable.

Affected: `search_cis_by_attributes` / `quick_ci_search` (a `^` or `&` in a name or location),
and caller-supplied filter values via `filter_records` / `query_table_with_filters`. Not
affected: the text search tools, whose keyword tokenizer drops those characters before they
reach a query, and the KB duplicate check, which refuses to answer rather than trust it (#66).

The fix is a per-value encoding boundary plus refusing `^`, which touches every table and the
token-optimization invariant — deliberately not bundled into a correctness release.

## [4.3.0] - 2026-07-14

Backfilled 2026-08-03 from the 33 non-merge commits between the 4.1.0 work and the `v4.3.0` tag.

**On the missing 4.2.0 — and on 4.1.0.** The shipped version string went straight from `4.0.0`
to `4.3.0`, in one bump in the packaging commit (`c9276cc`). There was never a `4.2.0`, and
`4.1.0` was never a shipped version either: it is a CHANGELOG heading only. The commit that
carries the 4.1.0 work (`baa7d46`, the shim deletion) does not touch
`personal_mcp_servicenow_main.py` at all. Tags agree — only `v4.0.0` and `v4.3.0` exist between
v3 and here.

So the performance and token work planned as "4.2" is recorded below under its own heading
rather than as a fabricated 4.2.0 release, and the `[4.1.0]` heading above should be read as
"the 4.1.0 work", not as a release you could have installed. Retroactive tags were deliberately
not created.

### Added

- **Claude Desktop Extension packaging** — the server builds as a `.mcpb` bundle. Version is
  3-way synced across `pyproject.toml`, `manifest.json` and `personal_mcp_servicenow_main.py`.
- **SSE transport authentication** — `MCP_SSE_AUTH_TOKEN` shared-secret bearer check in
  `auth_middleware.py`. SSE startup refuses to run without it unless `MCP_ALLOW_INSECURE_SSE`
  is set explicitly. Rejection messages never reveal whether a token was missing, malformed or
  wrong.
- **Log hardening** — URLs in stderr diagnostics are reduced to path plus a stable query hash,
  so a `sysparm_query` never reaches the logs.
- E2E MCP test prompts (`docs/E2E_TEST_PROMPTS.md`).

### Performance and token work (planned as 4.2, shipped in 4.3.0)

- **Pooled HTTP client** — one process-wide keep-alive `httpx.AsyncClient` (`oauth/http_pool.py`)
  shared by the request executor, the 401-retry and the token fetch. Previously every request
  paid a fresh TLS handshake.
- **One query instead of N** — `query_table_by_text` builds a single OR-combined LIKE query
  across all keywords (`short_descriptionLIKEa^ORshort_descriptionLIKEb`) instead of one serial
  request per keyword. Fewer round-trips *and* better recall: the old loop only ever matched a
  single keyword.
- **Concurrent CMDB probes** — `get_ci_details` probes candidate CI tables concurrently (bounded)
  instead of one at a time, preserving most-specific-first priority.
- **Debug payload opt-in** — `query_table_intelligently(debug=False)` no longer recomputes the
  debug extras on the default path.
- **Trimmed tool docstrings** — roughly 2k characters per session removed from the registered
  tool descriptions.
- Pre-compiled hot-path regexes; shared write-response helpers (`write_helpers.py`) for the KB
  and VTB paths; module-level condition-handler registry; dead helpers and a redundant
  `load_dotenv()` removed.

### Fixed

- **`LIKE`, not `CONTAINS`, in encoded queries.** `CONTAINS` is a GlideRecord scripting operator
  and is silently ignored inside a `sysparm_query` — it returned zero rows with no error. Also
  surfaces reference-field hints: `assignment_group`, `assigned_to`, `caller_id`, `cmdb_ci` and
  friends store sys_ids, so a bare display-value match silently matched nothing.
- **CMDB: valid CI types no longer rejected.** `find_cis_by_type` validated against a static
  table list that drifted from real instances and refused common classes such as
  `cmdb_ci_server`.
- **CMDB: user values percent-encoded** in CI search queries, so `#`, `+`, `%` or `?` in a name
  or location can no longer corrupt the query.
- **MCP parameter coercion** — some clients stringify and double-encode flat `List`/`Dict`
  parameters; `param_coercion.py` peels the layers at the tool boundary.
- **KB publish timeouts** — `anyio` `TimeoutError` is caught on the publish fire-timeout instead
  of escaping as an unhandled error; KB writes are now bounded, and stale pooled connections
  expire.
- Ticket detail field sets gain `sys_updated_on` and `opened_at`.
- Security sanitization sweep, P0 through P3, plus a linter-driven fix pass.
- Stale docstrings and a wrong date-explanation branch in the NL query path.

### Removed

- Nuitka binary builds dropped from the release workflow — `.mcpb` is the distribution path.
- graphify cache artifacts are no longer tracked.

## [4.1.0] - 2026-06-11

### BREAKING CHANGES

#### v4.0 backwards-compat shims deleted

The four re-export shim modules left in place for one release cycle are now removed:
`service_now_api_oauth.py`, `oauth_client.py`, `query_validation.py`, `query_intelligence.py`.

**Migration — import from the canonical packages directly:**
- `from service_now_api_oauth import make_nws_request, NWS_API_BASE, test_oauth_connection, get_auth_info` → `from http_layer import ...`
- `from oauth_client import ServiceNowOAuthClient, get_oauth_client, make_oauth_request` → `from oauth import ...`
- `from query_validation import ServiceNowQueryBuilder, validate_query_filters, ...` → `from filter import ...`
- `from query_intelligence import QueryIntelligence, get_filter_templates, ...` → `from filter import ...`

The process-wide OAuth singleton (`_oauth_client`, `get_oauth_client`, `make_oauth_request`) moved
from the deleted `oauth_client.py` to `oauth/singleton.py` (re-exported via `oauth/__init__.py`).
`http_layer/request_dispatcher.py` now imports the singleton at module level; the `sys.modules`-based
`_resolve_oauth_binding` indirection was removed.

**Test patch-target migration:**
- `patch("service_now_api_oauth.make_oauth_request")` → `patch("http_layer.request_dispatcher.make_oauth_request")`
- `patch("service_now_api_oauth.get_oauth_client")` → `patch("http_layer.request_dispatcher.get_oauth_client")`
- `patch("oauth_client.httpx.AsyncClient")` → `patch("oauth.singleton.httpx.AsyncClient")`
- `oauth_client._oauth_client = None` → `oauth.singleton._oauth_client = None`
- `patch("query_intelligence.*")` / `patch("query_validation.*")` → `patch("filter.intelligence.*")` / `patch("filter.validator.*")`

No production behaviour change: the GET read path (encoding + perf params + display flattening) and the
write path (bypass + `raise_for_status`) are unchanged. Full suite: 662 passed, 5 skipped (pre-existing).

#### SmartQueryParams removed (Sprint 1b)

`filter.SmartQueryParams` deleted — dead code. Defined and exported since v4.0 Sprint 1 but never
instantiated anywhere (zero call sites, zero tests). The NL query boundary is served by
`IntelligentQueryParams` in `Table_Tools/intelligent_query_tools.py`; the field-value boundary by
`filter.TableFilterParams`. The Sprint 1b "merge vs keep" question resolved to neither — the two
models address different concerns, and the NL one was simply unused.

## [4.0.0] - 2026-05-20

### BREAKING CHANGES

Architectural refactor surfaced by a graphify analysis of god-node clusters in the v3 codebase. Three sprints, each independently mergeable. Full migration guide in `MIGRATION_v3_to_v4.md`.

#### SLA tool consolidation (Sprint 2)

8 SLA tools collapsed into 3 new tools. Total tool count: **37 -> 32**.

**Removed (8 tools):**
- `get_slas_for_task`
- `get_breaching_slas`
- `get_breached_slas`
- `get_slas_by_stage`
- `get_active_slas`
- `get_sla_performance_summary`
- `get_recent_breached_slas`
- `get_critical_sla_status`

**Added (3 tools):**
- `query_slas_by_task(task_number)` — replaces `get_slas_for_task`
- `query_slas_by_status(status, days?, threshold_minutes?, stage?, extra_filters?)` — preset dispatcher for the 6 status-based tools. Status enum: `"active"`, `"breached"`, `"breaching"`, `"critical"`, `"by_stage"`, `"performance"`.
- `query_slas_custom(filters, fields?, days?)` — escape hatch. Defaults to `ESSENTIAL_FIELDS["task_sla"]` so it never returns all columns by default.

**Unchanged:**
- `similar_slas_for_text(text)`
- `get_sla_details(sys_id)` — **bug fix** included (see below)

#### get_sla_details v3 bug fix (Sprint 2)

v3 `get_sla_details(sys_id)` delegated to `get_record_details("task_sla", sys_id)` which built a `number={sys_id}` filter. The `task_sla` table has no `number` field, so the filter was silently ignored and the call returned the full default page — **10,000 rows / ~1.2 million tokens** — instead of the single record. v4 routes via `sys_id={sys_id}` directly, returning the single record (~69 tokens). **99.99% token reduction** for that tool.

### Added

#### Filter pipeline package (Sprint 1)

New `filter/` package consolidates filter construction, validation, NL parsing, and explanation:
- `filter/builder.py` — `ServiceNowQueryBuilder`
- `filter/validator.py` — `validate_query_filters`, `validate_and_correct_filters` (new), helpers
- `filter/intelligence.py` — `QueryIntelligence` (NL → filter, no backref to builder)
- `filter/explainer.py` — `QueryExplainer`, `explain_existing_filter`
- `filter/models.py` — `TableFilterParams`, `SmartQueryParams`, `QueryValidationResult`

#### HTTP layer package (Sprint 3)

New `http_layer/` package splits the v3 monolithic `make_nws_request`:
- `http_layer/url_builder.py` — `ensure_query_encoded`, `add_default_params` (GET-only)
- `http_layer/response_parser.py` — display-value flattening (GET-only)
- `http_layer/request_dispatcher.py` — `make_nws_request` orchestrator (~30 lines)

#### OAuth package (Sprint 3)

New `oauth/` package splits the v3 `ServiceNowOAuthClient`:
- `oauth/token_store.py` — token cache + refresh + injectable fetcher
- `oauth/request_executor.py` — authenticated HTTP + 401 retry
- `oauth/client.py` — `ServiceNowOAuthClient` façade
- `oauth/exceptions.py` — `ServiceNowOAuthError` + 3 subclasses

#### Token-optimization infrastructure

- `scripts/capture_sla_token_baseline.py` + `scripts/compare_sla_token_baseline.py` — live ServiceNow baseline and diff runners for SLA tools.
- `scripts/capture_read_path_baseline.py` — read-path baseline across all 7 tables. Validates four token-optimization URL invariants (`sysparm_exclude_reference_link`, `sysparm_no_count`, `sysparm_display_value`, sort order).
- `tests/test_token_footprint.py` — offline budget regression suite (`tiktoken` cl100k_base) for SLA tools.
- `tests/test_http_layer.py` — 13 tests locking the GET vs write divergence. **Three critical negative tests** prove POST/PATCH bypass the read-path mutations.

### Deprecated (deleted in v4.1)

Backwards-compat shims retain the v3 import paths and test-patch targets:
- `query_validation.py` — re-exports from `filter/`
- `query_intelligence.py` — re-exports from `filter/`
- `service_now_api_oauth.py` — re-exports from `http_layer/` + keeps `make_oauth_request` / `get_oauth_client` patch targets
- `oauth_client.py` — canonical home of the module-level singleton (`_oauth_client`, `get_oauth_client`, `make_oauth_request`) + `httpx` re-export

### Architecture

`filter/intelligence.py` no longer imports from `filter/builder.py`. Auto-correction logic that needs `ServiceNowQueryBuilder` lives in `filter/validator.validate_and_correct_filters` — the only module allowed to bridge NL parsing → query construction.

### Metrics

- Tool count: 32 (down from 37)
- Tests: 575 passing (up from 537)
- Overall coverage: ~83%
- `filter/` coverage: 98.16%
- `oauth/` + `http_layer/` coverage: 92.98%

---

## [2.0.0] - 2025-01-14

### 🚨 BREAKING CHANGES

This is a major architectural overhaul with significant breaking changes. See CHANGELOG entries below for v1.x → v2.0 migration notes.

#### **Deleted Files (Breaking Changes)**

- **REMOVED**: `Table_Tools/incident_tools.py` - Use `consolidated_tools.py` functions instead
- **REMOVED**: `Table_Tools/change_tools.py` - Use `consolidated_tools.py` functions instead
- **REMOVED**: `Table_Tools/kb_tools.py` - Use `consolidated_tools.py` functions instead
- **REMOVED**: `Table_Tools/ur_tools.py` - Use `consolidated_tools.py` functions instead

#### **Authentication Changes**

- **OAuth 2.0 Only**: Removed basic authentication fallback for enhanced security
- **Required Environment Variables**: `SERVICENOW_CLIENT_ID` and `SERVICENOW_CLIENT_SECRET` now mandatory

#### **API Changes**

- **Tool Registration**: Consolidated from 25+ individual tools to unified approach
- **Function Names**: All MCP tools now use snake_case naming convention
- **Return Types**: Standardized return formats across all functions

### 🚀 NEW FEATURES

#### **AI-Powered Natural Language Queries**

- **Intelligent Search**: `intelligent_search()` - Natural language to ServiceNow queries
- **Query Explanation**: `explain_servicenow_filters()` - AI explanations of what filters will do
- **Smart Filter Building**: `build_smart_servicenow_filter()` - Convert natural language to ServiceNow syntax
- **Predefined Templates**: `get_servicenow_filter_templates()` - Ready-to-use filter patterns
- **Query Examples**: `get_query_examples()` - Natural language query examples

#### **Enhanced Generic Table Operations**

- **Universal Functions**: `query_table_intelligently()` - AI-powered queries for any table
- **Advanced Filtering**: `query_table_with_filters()` with intelligent natural language parsing
- **Priority Queries**: `get_records_by_priority()` - Generic priority filtering for any table
- **Generic CRUD**: Complete Create, Read, Update operations for supported tables

#### **Natural Language Intelligence**

- **Date Range Parsing**:
  - "Week 35 2025" → Proper BETWEEN syntax with calculated dates
  - "August 25-31, 2025" → Month range parsing
  - "2025-08-25 to 2025-08-31" → ISO date range
- **Priority Parsing**:
  - "1,2" → "priority=1^ORpriority=2" (proper OR syntax)
  - "P1,P2" → "priority=1^ORpriority=2" (P-notation conversion)
- **Caller Exclusion Parsing**:
  - "logicmonitor" → Automatic sys_id lookup and exclusion

### 🛡️ SECURITY ENHANCEMENTS

#### **ReDoS Protection**

- **Input Validation**: Pre-validation of all text inputs to prevent malicious patterns
- **Timeout Protection**: `timeout_protection()` context manager for regex operations
- **Length Limits**: Automatic rejection of overly long input strings

#### **Enhanced Authentication**

- **OAuth 2.0 Exclusive**: Improved security through OAuth-only approach
- **Automatic Token Refresh**: Intelligent token management and expiration handling

### ⚡ PERFORMANCE IMPROVEMENTS

#### **Optimized Architecture**

- **Code Reduction**: Net reduction of 142 lines while adding significant functionality
- **Pagination**: `_make_paginated_request()` with configurable limits and complete result retrieval
- **Smart Caching**: Automatic token caching and reuse
- **Query Optimization**: Intelligent query building with handler registry pattern

#### **Enhanced API Integration**

- **URL Encoding Preservation**: Maintains ServiceNow JavaScript functions during encoding
- **Proper OR Syntax**: Correct ServiceNow query syntax for multiple priorities
- **JavaScript Date Functions**: Perfect BETWEEN syntax with ServiceNow date functions

### 📚 DOCUMENTATION & TESTING

#### **Comprehensive Documentation**

- **Architecture Diagrams**: Complete system architecture documentation
- **AI Intelligence Flow**: Detailed documentation of natural language processing
- **Tool Organization**: Clear mapping of all available tools and capabilities
- **API Examples**: Extensive examples of natural language queries

#### **Enhanced Testing**

- **Consolidated Tool Tests**: `Testing/test_consolidated_tools.py` with 417 new lines
- **Query Intelligence Tests**: Enhanced `Testing/test_query_intelligence.py`
- **Comprehensive Validation**: `Testing/test_filtering_fixes.py` with 100% success rate
- **CMDB Testing**: Updated `Testing/test_cmdb_tools.py`

### 🏗️ ARCHITECTURAL IMPROVEMENTS

#### **Code Quality Enhancements**

- **Cognitive Complexity Reduction**: All functions now under complexity limit ≤15
- **Helper Function Extraction**: Modular design with single-responsibility functions
- **Constants Consolidation**: Enhanced `constants.py` with centralized configuration
- **Error Message Standardization**: All duplicated literals moved to constants

#### **Maintainability**

- **Single Responsibility**: Clear separation of concerns across modules
- **Enhanced Testability**: Individual components can be tested independently
- **Modular Design**: Reusable functions with consistent interfaces

### 🔧 INFRASTRUCTURE

#### **New Dependencies**

- Enhanced `requirements.txt` with AI/ML processing capabilities
- Natural language processing support
- Advanced regex processing with safety features

#### **Tool Registration Optimization**

- **Streamlined Registration**: Unified tool registration in `tools.py`
- **Intelligent Query Tools**: 5 new AI-powered MCP tools
- **Zero Functional Regression**: All existing functionality maintained

### 📈 METRICS

- **Lines Added**: 2,781
- **Lines Removed**: 1,146
- **Net Change**: +1,635 lines of enhanced functionality
- **Files Modified**: 29
- **Files Deleted**: 4 (consolidated into generic functions)
- **Files Created**: 7 (documentation, tests, new features)

### 🔄 MIGRATION GUIDE

See the v2.0 section above for migration notes from v1.x to v2.0.

### 🙏 ACKNOWLEDGMENTS

This release represents one of the largest architectural changes in the project's history, implementing cutting-edge AI integration while maintaining zero functional regression.

---

## [1.0.0] - Previous Release

Previous release information maintained for historical reference.
