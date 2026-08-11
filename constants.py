"""
Constants used throughout the ServiceNow MCP server.
"""

import os

# Per-table configuration is now defined once, in table_spec.TABLE_SPECS (v5.0
# "Boron" Tier 3.2). The collections below (TABLE_CONFIGS, ESSENTIAL_FIELDS,
# DETAIL_FIELDS, TABLE_ERROR_MESSAGES, TABLES_WITHOUT_RECORD_IDENTITY, the
# text-search map) are DERIVED from it so existing `from constants import ...`
# consumers are unaffected. Change a table there, not here.
from table_spec import TABLE_SPECS, TableSpec

# HTTP Content Types
APPLICATION_JSON = "application/json"

# Common HTTP Headers
JSON_HEADERS = {
    "Accept": APPLICATION_JSON,
    "Content-Type": APPLICATION_JSON
}

# API Response Messages
NO_DESCRIPTION_FOUND = "No description found."
CONNECTION_ERROR = "Connection error: Request failed"
RECORD_NOT_FOUND = "Record not found."
NO_RECORDS_FOUND = "No records found."

# MCP transport auth (SSE shared-secret bearer token — see auth_middleware.py).
# Deliberately generic: never reveal whether the token was missing, malformed,
# or wrong to the caller.
MCP_AUTH_REJECTED = "Unauthorized: invalid or missing MCP auth token."
UNABLE_TO_FETCH_RECORDS = "Unable to fetch alerts or no alerts found."
UNABLE_TO_FETCH_DETAILS = "Unable to fetch {record_type} details or no {record_type} found."
NO_SIMILAR_RECORDS_FOUND = "No similar records found (only exact match)"
REQUEST_FAILED_ERROR = "Request failed: {error}"
NO_FIELD_CONFIG_ERROR = "No field configuration found for table {table_name}"
NO_VALID_PRIORITIES_ERROR = "No valid priorities provided"
TABLE_NO_PRIORITY_SUPPORT_ERROR = "Table {table_name} does not support priority filtering"

# CMDB-specific error messages
# v5.0 "Boron" Tier 3.1 removed the CMDB bare not-found strings: empty is now a
# success shape (list_response([]) / record_response(None)), so
# NO_CIS_FOUND_FOR_TYPE, NO_CIS_FOUND_MATCHING_CRITERIA, CI_NOT_FOUND,
# NO_SIMILAR_CIS_FOUND, NO_CI_TYPES_FOUND and NO_CIS_FOUND_FOR_SEARCH are gone.
CI_TYPE_REQUIRED = "CI type is required"
CI_NUMBER_REQUIRED = "CI number is required"
# A rejected ci_type must never be silently downgraded to the base cmdb_ci
# table — that returns rows from the wrong table with no indication of it.
INVALID_CI_TYPE = (
    "Invalid CI type '{ci_type}'. Must be a cmdb_ci* table name containing only "
    "lowercase letters, digits and underscores (e.g. cmdb_ci_server). "
    "Call get_all_ci_types() to list the classes this instance actually has."
)

# ---------------------------------------------------------------------------
# Reference-field handling
# ---------------------------------------------------------------------------
# ServiceNow reference fields store a sys_id (32-char hex), not the display
# value. A bare equality filter against the display name (e.g.
# `assignment_group=SN_FLEET`) matches the sys_id column, never the name, and
# returns zero rows with no error. Detect this and tell the caller how to fix
# it: pass a sys_id, or dot-walk to a stored field (e.g. `assignment_group.name`).
REFERENCE_FIELDS = frozenset({
    "assignment_group",
    "assigned_to",
    "caller_id",
    "opened_by",
    "closed_by",
    "resolved_by",
    "company",
    "location",
    "cmdb_ci",
    "business_service",
    "parent",
    "u_requested_for",
    "requested_for",
})

REFERENCE_FIELD_HINT = (
    "Filter field '{field}' is a ServiceNow reference field — it stores a sys_id, "
    "not the display value '{value}'. A bare equality match returns zero rows. "
    "Pass the sys_id, or dot-walk to a stored attribute, e.g. "
    "{field}.nameLIKE{value} (substring) or {field}.name={value} (exact)."
)

# ---------------------------------------------------------------------------
# Encoded-query operator reference (anti-hallucination)
# ---------------------------------------------------------------------------
# Single source of truth for the operators that are VALID inside a
# sysparm_query encoded-query string. Exposed to the MCP client (see
# `servicenow://help/query-syntax` in tools.py) so the model uses real syntax
# instead of guessing. NOTE: `CONTAINS`/`NOTCONTAINS` are GlideRecord scripting
# operators and are NOT valid here — use `LIKE`/`NOT LIKE` for substring matches.
SERVICENOW_QUERY_OPERATORS = {
    "=": {"meaning": "equals", "example": "priority=1"},
    "!=": {"meaning": "not equal", "example": "state!=6"},
    "LIKE": {"meaning": "contains (substring); use this, NOT CONTAINS", "example": "short_descriptionLIKEserver"},
    "NOT LIKE": {"meaning": "does not contain", "example": "short_descriptionNOT LIKEtest"},
    "STARTSWITH": {"meaning": "begins with", "example": "numberSTARTSWITHINC"},
    "ENDSWITH": {"meaning": "ends with", "example": "short_descriptionENDSWITHdown"},
    "IN": {"meaning": "in a comma list", "example": "priorityIN1,2,3"},
    "NOT IN": {"meaning": "not in a comma list", "example": "stateNOT IN7,8"},
    "ISEMPTY": {"meaning": "field is empty", "example": "assigned_toISEMPTY"},
    "ISNOTEMPTY": {"meaning": "field is not empty", "example": "assigned_toISNOTEMPTY"},
    ">": {"meaning": "greater than", "example": "priority>2"},
    ">=": {"meaning": "greater than or equal", "example": "sys_created_on>=2026-01-01"},
    "<": {"meaning": "less than", "example": "priority<3"},
    "<=": {"meaning": "less than or equal", "example": "sys_created_on<=2026-06-30"},
    "BETWEEN": {"meaning": "inclusive range (a@b)", "example": "sys_created_onBETWEEN2026-01-01@2026-03-31"},
    "INSTANCEOF": {"meaning": "table inheritance", "example": "sys_class_nameINSTANCEOFcmdb_ci_server"},
    "^": {"meaning": "AND", "example": "priority=1^state=2"},
    "^OR": {"meaning": "OR", "example": "priority=1^ORpriority=2"},
    "^NQ": {"meaning": "new query (UNION)", "example": "active=true^NQactive=false"},
    "ORDERBY": {"meaning": "sort ascending", "example": "^ORDERBYsys_created_on"},
    "ORDERBYDESC": {"meaning": "sort descending", "example": "^ORDERBYDESCsys_created_on"},
}

QUERY_SYNTAX_NOTES = (
    "ServiceNow encoded-query syntax: write conditions as fieldOPERATORvalue, "
    "joined by ^ (AND) / ^OR (OR). For substring 'contains', use LIKE "
    "(fieldLIKEvalue) — CONTAINS is GlideRecord-script-only and is silently "
    "ignored in encoded queries. Reference fields (assignment_group, "
    "assigned_to, caller_id, cmdb_ci, ...) store sys_ids; filter by sys_id or "
    "dot-walk (assignment_group.nameLIKEFleet)."
)
ERROR_SEARCHING_CIS = "Error searching CIs: Request failed"
ERROR_SEARCHING_CIS_BY_TYPE = "Error searching CIS by type: Request failed"
ERROR_FINDING_SIMILAR_CIS = "Error finding similar CIs: Request failed"
ERROR_GETTING_CI_TYPES = "Error getting CI types: Request failed"
ERROR_QUICK_CI_SEARCH = "Error in quick CI search: Request failed"

# VTB Task-specific error messages
ERROR_SHORT_DESC_REQUIRED = "Error: short_description is required to create a private task."
ERROR_NO_UPDATE_DATA = "Error: No update data provided."
PRIVATE_TASK_NOT_FOUND_UPDATE = "Private Task not found for update."
UNABLE_TO_FETCH_PRIVATE_TASK_DETAILS = "Unable to fetch private task details or no private task found."
ERROR_PRIVATE_TASK_OPERATION = "Error during private task {operation}: {message}"
ERROR_PRIVATE_TASK_REQUEST_FAILED = "Error during private task {operation}: Request failed"
ERROR_PRIVATE_TASK_AUTH_FAILED = "Error during private task {operation}: Authentication failed"
ERROR_PRIVATE_TASK_ACCESS_DENIED = "Error during private task {operation}: Access denied"
ERROR_PRIVATE_TASK_INVALID_REQUEST = "Error during private task {operation}: Invalid request data"
ERROR_PRIVATE_TASK_NOT_FOUND = "Error during private task {operation}: Task not found"
ERROR_PRIVATE_TASK_SERVER_ERROR = "Error during private task {operation}: Server error"
# A write that came back with no record is unconfirmed, not successful. See
# ERROR_KB_WRITE_UNCONFIRMED for why this stopped being phrased as a success.
ERROR_PRIVATE_TASK_WRITE_UNCONFIRMED = (
    "Private task {operation} could not be confirmed: ServiceNow accepted the request "
    "but returned no record. Check the task before retrying."
)

# Write allowlist for update_private_task — blocks writes to sys_* metadata,
# number, or other fields that should never be caller-settable.
VTB_UPDATABLE_FIELDS = [
    "short_description", "description", "state", "priority", "assigned_to",
    "assignment_group", "due_date", "parent", "comments", "work_notes"
]

# KB Article-specific error messages
ERROR_KB_NO_UPDATE_DATA = "Error: No update data provided."
ERROR_KB_ARTICLE_NOT_FOUND_OP = "Knowledge article {number} not found."
ERROR_KB_ARTICLE_REQUEST_FAILED = "Error during knowledge article {operation}: Request failed"
ERROR_KB_ARTICLE_AUTH_FAILED = "Error during knowledge article {operation}: Authentication failed"
ERROR_KB_ARTICLE_ACCESS_DENIED = "Error during knowledge article {operation}: Access denied"
ERROR_KB_ARTICLE_INVALID_REQUEST = "Error during knowledge article {operation}: Invalid request data"
ERROR_KB_ARTICLE_NOT_FOUND = "Error during knowledge article {operation}: Article not found"
ERROR_KB_ARTICLE_SERVER_ERROR = "Error during knowledge article {operation}: Server error"
# A write that came back with no record is unconfirmed, not successful. The old
# wording ("... successful but no data returned") asserted the write had landed
# on the strength of the response being empty, which is the one thing an empty
# response cannot establish.
ERROR_KB_WRITE_UNCONFIRMED = (
    "Knowledge article {operation} could not be confirmed: ServiceNow accepted the "
    "request but returned no record. Check the article before retrying."
)
ERROR_KB_PUBLISH_NOT_CONFIRMED = (
    "Publish for {number} could not be confirmed (workflow endpoint may have "
    "failed, or ServiceNow has not yet committed the state change). Re-check "
    "with check_kb_duplicates or get_kb_articles_by_state before retrying."
)

# Write allowlist for update_knowledge_article — editable content fields only.
# workflow_state is deliberately excluded: it is a ServiceNow-managed field
# that publish/retire transition via the qonv workflow endpoint, never a
# direct Table API write (see kb_article_tools._call_kb_workflow). sys_* and
# number are likewise never caller-settable. meta / meta_description are the
# kb_knowledge SEO keyword and description fields (ServiceNow Table API names).
KB_UPDATABLE_FIELDS = [
    "short_description", "text", "kb_category", "meta", "meta_description",
]

# Table-specific error messages (derived from TABLE_SPECS — Tier 3.2).
TABLE_ERROR_MESSAGES = {name: spec.error_message for name, spec in TABLE_SPECS.items()}

# ---------------------------------------------------------------------------
# Text search and record identity
# ---------------------------------------------------------------------------
# Default field the free-text search path matches against.
TEXT_SEARCH_FIELD = "short_description"

# task_sla carries no short_description of its own — the description lives on
# the referenced task. A filter against a field a table does not have is
# SILENTLY DROPPED by ServiceNow, so searching short_description on task_sla
# produced an unfiltered page of arbitrary SLAs labelled as matches (the same
# failure mode as the 1.2M-token get_sla_details bug). Dot-walk instead.
TASK_SLA_TEXT_SEARCH_FIELD = "task.short_description"

# Per-table free-text search field, derived from TABLE_SPECS (Tier 3.2). Getting
# it wrong is silent — a condition on a missing field is dropped, not rejected —
# which is why the field lives on the spec rather than being chosen per call site.
TEXT_SEARCH_FIELD_BY_TABLE = {
    name: spec.text_search_field
    for name, spec in TABLE_SPECS.items()
    if spec.text_search_field != TEXT_SEARCH_FIELD
}


def text_search_field_for(table_name: str) -> str:
    """The field a free-text search must target for *table_name*."""
    spec = TABLE_SPECS.get(table_name)
    return spec.text_search_field if spec else TEXT_SEARCH_FIELD

# Tables the number- and text-addressed generic tools cannot query at all.
# DERIVED from TABLE_SPECS (Tier 3.2): a spec with number_field=None has no
# record identity, so it lands here structurally — a table can no longer be
# addressable-by-number in one place and forgotten in this guard. task_sla has
# neither `number` nor its own `short_description`, so get_record /
# find_similar / search_records could only build queries against fields that do
# not exist.
TABLES_WITHOUT_RECORD_IDENTITY = frozenset(
    name for name, spec in TABLE_SPECS.items() if not spec.has_record_identity
)

TABLE_LACKS_RECORD_IDENTITY = (
    "Table '{table}' has no 'number' or 'short_description' field, so this tool "
    "cannot address its records — ServiceNow silently drops a filter on a "
    "missing field and would return unrelated rows. Use query_slas_by_task("
    "task_number), query_slas_by_status(status), get_sla_details(sla_sys_id), "
    "or filter_records('{table}', filters)."
)

# Table field definitions, derived from TABLE_SPECS (Tier 3.2). Lists (not the
# specs' tuples) to preserve the historical public type of these dicts.
ESSENTIAL_FIELDS = {name: list(spec.essential_fields) for name, spec in TABLE_SPECS.items()}

DETAIL_FIELDS = {name: list(spec.detail_fields) for name, spec in TABLE_SPECS.items()}

# VTB Task specific field definitions
COMMON_VTB_TASK_FIELDS = [
    "number",
    "short_description", 
    "priority",
    "sys_created_on",
    "state",
    "assigned_to",
    "assignment_group"
]

DETAILED_VTB_TASK_FIELDS = COMMON_VTB_TASK_FIELDS + [
    "description",
    "comments",
    "work_notes",
    "close_code",
    "close_notes",
    "sys_updated_on",
    "due_date",
    "parent"
]

KB_WRITE_RESPONSE_FIELDS = {
    "number", "sys_id", "short_description", "workflow_state",
    "meta", "meta_description",
}

# Field lists for KB read queries (ordered tuples — sysparm_fields order is stable).
KB_META_FIELDS = ("sys_id", "short_description")
KB_DEDUP_FIELDS = ("number", "short_description", "workflow_state", "sys_created_on", "kb_category")
KB_VERIFY_FIELDS = ("sys_id", "number", "workflow_state", "short_description")

# Workflow states that should NOT block a publish on duplicate check.
# Retired = explicitly killed; outdated = prior version after a newer publish (ServiceNow versioning artefact).
# Draft / review / published remain blockers because they represent live or pending content.
KB_DUPLICATE_IGNORED_STATES = {"retired", "outdated"}

# Row cap on the duplicate-check query. The check LIKE-matches in ServiceNow and
# then exact-matches in Python, so a page that hits this cap may have left the
# real duplicate behind — a capped page is inconclusive, not clean. Without an
# explicit limit the instance default applies silently and truncation is
# indistinguishable from a complete answer.
KB_DEDUP_QUERY_LIMIT = 200

# Characters that break the STRUCTURE of an encoded query when they appear
# inside a value, and so make a duplicate check untrustworthy for that title.
#
# v4.4.1 narrowed this from ("^", "&") to ("^",). "&" was only ever broken in
# transport: the encoder unquoted before re-quoting, so a call site's "%26" was
# undone and the raw "&" escaped sysparm_query= into a sibling URL parameter.
# The encoder preserves existing escapes now and `encode_query_value` escapes the
# title, so "Sales & Marketing" is carried faithfully and no longer blocks a
# publish. The same change retired the percent-escape round-trip check.
#
# "^" stays refused because it is unrepresentable, not merely mis-transported:
# even correct end-to-end encoding hands ServiceNow a decoded value containing
# "^", and its condition parser splits there —
#   "Cost^Center"  ->  short_descriptionLIKECost ^ Center   (two conditions)
# The query that runs is broader than the one asked for, so a "no duplicates"
# answer from it would be meaningless. Inconclusive, not clean.
#
# Measured against the whole encoder safe-set (2026-08-05): a value containing
# = < > ( ) : @ ! survives the round trip intact.
KB_QUERY_UNSAFE_CHARS = ("^",)

# The duplicate check could not produce a trustworthy answer, so the publish did
# not happen. Fail-closed: "could not check" is not "nothing found".
ERROR_KB_DUPLICATE_CHECK_INCONCLUSIVE = (
    "Duplicate check for {number} could not be completed ({reason}), so it was not "
    "published. Nothing was written. Re-run once the cause is resolved."
)
KB_DEDUP_REASON_UNSAFE_CHARS = (
    "the title contains a character ({chars}) that ServiceNow's encoded-query syntax "
    "cannot carry inside a value, which would silently widen the search"
)
KB_DEDUP_REASON_TRUNCATED = (
    "the search hit its {limit}-row cap, so a duplicate may have been left off the page"
)

# ---------------------------------------------------------------------------
# Encoded-query value boundary (v4.4.1)
# ---------------------------------------------------------------------------
# Refusal message for the one character a value cannot carry. Not a warning and
# not a dropped condition: a silently dropped or widened condition is how a
# scoped query became a table read (see the silently_dropped_filters memory), so
# the caller is told instead of being handed rows from a different query.
QUERY_VALUE_CARET_ERROR = (
    "Cannot search for a value containing '{char}': ServiceNow's encoded-query "
    "syntax uses '{char}' to separate conditions and has no way to escape it "
    "inside a value, so the search would silently match more records than "
    "requested. Refused rather than answered. Value: '{value}'. Remove the "
    "'{char}', or express the intent as separate filters."
)

# `^NQ` starts a brand-new query, discarding every condition built before it, so
# one poisoned filter value turns a scoped query into an unbounded table read.
# v4.4.1 turned the existing defense from a silent drop into this refusal: the
# drop removed the poisoned condition but ran the remaining ones, answering a
# question nobody asked with rows that look legitimate.
QUERY_VALUE_NEW_QUERY_ERROR = (
    "Refusing a filter value containing '{char}NQ': it restarts the query and "
    "discards every condition before it, which would return records from an "
    "unscoped table read. Nothing was queried. Value: '{value}'."
)

# Three filter keys accept a PRE-BUILT fragment rather than a value: `_date_range`,
# `_complete_caller_exclusion`, and `_complete_query`. They carry their own
# operators — `build_date_filter` legitimately emits
# "sys_created_on>=A^sys_created_on<=B" — so they cannot be escaped, and `^` has to
# be allowed. `&` never is: it is not an encoded-query operator, so it can only
# escape `sysparm_query=` into a sibling URL parameter and truncate the fragment.
# Refused because there is nowhere else to catch it.
QUERY_FRAGMENT_AMPERSAND_ERROR = (
    "Refusing a pre-built filter fragment containing '&': the fragment carries its "
    "own operators so it cannot be escaped, and a raw '&' ends the query string and "
    "silently drops everything after it. Nothing was queried. Fragment: '{value}'."
)

# Field NAMES are caller-supplied too — they are the keys of the filters dict, and
# no tool validates them. An unchecked key put the operators straight into the
# query: {"x^NQstate=99": "1"} built "x^NQstate=99=1", the same unscoped-table-read
# injection the value guard refuses. Shape check rather than a character blacklist,
# because a legitimate field name is narrow: identifier characters plus '.' for
# dot-walking (task.priority) and a leading '_' for the internal fragment keys.
QUERY_FIELD_NAME_ERROR = (
    "Refusing the filter field name '{value}': a field name may contain only "
    "letters, digits, '_' and '.' (for dot-walked references such as "
    "task.priority). Anything else would be read as query syntax rather than as a "
    "field. Nothing was queried."
)

# The publish workflow fired but the confirming read failed. Distinct from a
# publish that is known not to have happened: this one may well have committed.
ERROR_KB_PUBLISH_VERIFY_UNREADABLE = (
    "Publish for {number} was submitted but could not be confirmed: the verification "
    "read failed ({message}). The article may or may not be published; check its state "
    "before retrying, as retrying may publish a second version."
)

# KB publish workflow tuning — the SN /qonv/.../publish endpoint runs duplicate
# check + state transition + reindex synchronously and routinely takes 60-90s.
# Fire-and-verify pattern: POST with extended timeout, then poll for the
# Published row to confirm. Treat verify as source of truth.
KB_PUBLISH_TIMEOUT_SECONDS = 180.0
# Total deadline for a single KB table write (PATCH/POST via _write_kb_article).
# The v4.2 anyio refactor set the pooled client to timeout=None and only wrapped
# the GET and publish-workflow paths in anyio.fail_after, leaving ordinary writes
# (update/retire) unbounded — a slow or half-open ServiceNow connection could hang
# update_knowledge_article for minutes. This restores the pre-refactor 30s bound.
KB_WRITE_TIMEOUT_SECONDS = 30.0
# Total deadline for a single vtb_task write (POST/PATCH via _write_private_task).
# Parity with KB_WRITE_TIMEOUT_SECONDS above.
VTB_WRITE_TIMEOUT_SECONDS = 30.0
KB_VERIFY_DELAY_SECONDS = 12
KB_PUBLISH_MAX_RETRIES = 1
KB_PUBLISH_BATCH_CONCURRENCY = 2
KB_PUBLISHED_STATE = "published"
# Hard cap on caller-supplied concurrency for KB batch tools (check_kb_duplicates,
# publish_knowledge_articles) to prevent excessive concurrent ServiceNow requests.
KB_MAX_BATCH_CONCURRENCY = 5

# ServiceNow Query Patterns and Validation
SERVICENOW_OR_SYNTAX_EXAMPLE = "1^ORpriority=2"
SERVICENOW_DATE_RANGE_EXAMPLE = ">=2024-01-01 00:00:00^<=2024-01-31 23:59:59"

# Common ServiceNow priority values
PRIORITY_VALUES = {
    "critical": "1",
    "high": "2",
    "moderate": "3",
    "low": "4",
    "planning": "5"
}

# Month name to number mapping for date parsing
MONTH_NAME_TO_NUMBER = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12
}

# Query validation messages
QUERY_WARNINGS = {
    "multiple_priorities_no_or": "Multiple priorities detected but no OR syntax used",
    "incomplete_date_range": "Date range appears incomplete - missing start or end date",
    "low_critical_incident_count": "Unusually low count for critical incidents - verify completeness",
    "zero_results_high_priority": "No results for high priority query - check filter syntax"
}

# Query-injection hardening
# `_complete_query` lets a caller hand a raw, pre-built ServiceNow encoded
# query straight through the filter pipeline, bypassing every per-field
# handler and the `^NQ` new-query-reset defense. Off by default; an operator
# can opt back in.
ENABLE_COMPLETE_QUERY = os.getenv("ENABLE_COMPLETE_QUERY", "false").strip().lower() in ("1", "true", "yes", "on")

# LogicMonitor integration caller sys_id, used for exclusion filters.
LOGICMONITOR_CALLER_SYS_ID = os.getenv("LOGICMONITOR_CALLER_SYS_ID", "1727339e47d99190c43d3171e36d43ad")

# ServiceNow table configurations, derived from TABLE_SPECS (Tier 3.2). Same
# dict-of-dicts shape and keys as before; api_name has always equalled the table
# key. Consumers reading TABLE_CONFIGS[t]["number_prefix"] etc. are unchanged.
TABLE_CONFIGS = {
    name: {
        "display_name": spec.display_name,
        "api_name": name,
        "supports_work_notes": spec.supports_work_notes,
        "supports_comments": spec.supports_comments,
        "number_prefix": spec.number_prefix,
        "priority_field": spec.priority_field,
        "state_field": spec.state_field,
    }
    for name, spec in TABLE_SPECS.items()
}

# API endpoint patterns
API_ENDPOINTS = {
    "table_query": "/api/now/table/{table_name}",
    "table_record": "/api/now/table/{table_name}/{sys_id}",
    "test_endpoint": "/api/x_146833_awesomevi/test",
    "test_table_endpoint": "/api/x_146833_awesomevi/test/{table_name}"
}

# Common query parameters  
QUERY_PARAMS = {
    "display_value": "sysparm_display_value=true",
    "fields": "sysparm_fields={fields}",
    "query": "sysparm_query={query}",
    "limit": "sysparm_limit={limit}",
    "offset": "sysparm_offset={offset}"
}
# Field reference constants
TASK_NUMBER_FIELD = "task.number"
