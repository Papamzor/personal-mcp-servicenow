"""Tool selection guidance — structured, injected into docstrings (v5.0 Tier 3.3).

The Tier 1 protocol put a WHEN TO USE / WHEN NOT TO USE / PREFER OVER block at the
top of every tool docstring, as prose. `TOOL_GUIDANCE` makes that block STRUCTURED
data — one `ToolGuidance` per tool — and `register_tools` injects it back as a
generated docstring footer at registration. Two payoffs:

  * It forces the protocol. Registration fails if a registered tool has no
    guidance entry, so a new tool cannot ship without its selection guidance —
    the thing the prose convention could only ask for politely.
  * The golden-set test can read the three fields directly (structured) instead
    of parsing them out of prose.

Injection is idempotent: `apply_guidance` first strips any existing WHEN TO USE …
PREFER OVER block from the docstring (including a footer it added on a previous
run), then appends the canonical one. So the served docstring is regenerated from
this registry — the registry is the single source of truth for tool guidance.

Only three fields, by design (plan §3.3: "only fields something reads"). `domain`,
`tables`, `public`, `mutates` stay out until a test or router consumes them; at 25
tools a hand list plus three fields is enough.
"""
from __future__ import annotations

import inspect
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ToolGuidance:
    """The selection guidance for one tool. All three fields are required."""
    when_to_use: str
    when_not: str
    prefer_over: str


# The guidance block, wherever it sits in a docstring: from `WHEN TO USE:` through
# the end of `PREFER OVER:` (and its wrapped continuation lines), stopping at the
# next uppercase section label (FOOTGUNS/TABLES/SIDE EFFECT/EXAMPLE/…), a blank
# line, or end of string. Used to strip the old prose block before re-injecting.
_GUIDANCE_BLOCK = re.compile(
    r'(?ms)^[ \t]*WHEN TO USE:.*?^[ \t]*PREFER OVER:.*?'
    r'(?=^[ \t]*[A-Z][A-Z ]+:|^[ \t]*$|\Z)'
)


def guidance_footer(name: str) -> str:
    """The canonical three-line footer generated from a tool's guidance."""
    g = TOOL_GUIDANCE[name]
    return (
        f"WHEN TO USE: {g.when_to_use}\n"
        f"WHEN NOT TO USE: {g.when_not}\n"
        f"PREFER OVER: {g.prefer_over}"
    )


def apply_guidance(fn):
    """Rewrite fn.__doc__ so its guidance comes from TOOL_GUIDANCE (idempotent)."""
    body = _GUIDANCE_BLOCK.sub("", inspect.getdoc(fn) or "").strip()
    footer = guidance_footer(fn.__name__)
    fn.__doc__ = f"{body}\n\n{footer}" if body else footer
    return fn


def register_tools(mcp, fns):
    """Inject guidance into each tool and register it with the FastMCP server.

    Fails loudly if a registered tool has no guidance entry — that is what makes
    the WHEN/WHEN-NOT/PREFER protocol mandatory rather than merely conventional.
    """
    missing = [fn.__name__ for fn in fns if fn.__name__ not in TOOL_GUIDANCE]
    if missing:
        raise ValueError(
            f"register_tools: no TOOL_GUIDANCE entry for {missing}. Every tool must "
            f"declare when_to_use / when_not / prefer_over (plan §3.3)."
        )
    for fn in fns:
        apply_guidance(fn)
        mcp.tool()(fn)
    return list(fns)


TOOL_GUIDANCE = {
    "health_check": ToolGuidance(
        when_to_use='confirm the server is up and ServiceNow is reachable — "is the ServiceNow connection up", "test ServiceNow authentication". Pass probe_table to also list one supported table\'s field names.',
        when_not="querying records (filter_records / search_records); building or explaining a filter (get_query_syntax_help).",
        prefer_over="nothing — this is the single diagnostic entry point. It replaces the former nowtest / now_test_oauth / now_auth_info / nowtestauth / nowtest_auth_input tools.",
    ),
    "search_records": ToolGuidance(
        when_to_use='the user describes a topic or symptom and wants matching records — "incidents about a server crashing during backup".',
        when_not="you already know the record number (get_record); you need field filters like state or priority (filter_records); a priority-plus-date list (get_priority_incidents).",
        prefer_over="filter_records when the ask is words, not field values.",
    ),
    "get_record": ToolGuidance(
        when_to_use='you know the record number and want its complete detail — "give me the full details of incident INC0012345".',
        when_not="a list view over many rows (filter_records); text search (search_records).",
        prefer_over="filter_records when you have the number and want every field of that one record; search_records when you have the number, not keywords.",
    ),
    "find_similar": ToolGuidance(
        when_to_use='you have one record\'s number and want others like it — "find other incidents similar to this one".',
        when_not="you have search words, not a seed record (search_records); you want that record's own fields (get_record).",
        prefer_over="search_records when the seed is an existing record, not text.",
    ),
    "filter_records": ToolGuidance(
        when_to_use='the user gives field conditions — state, priority, category, date ranges — "list change requests where state is 3 and category is network".',
        when_not="free-text topic search (search_records); a single record by number (get_record); a priority-plus-date incident list (get_priority_incidents); KB version rollups (get_kb_articles_by_state).",
        prefer_over="the table-specific tools when you need an arbitrary filter shape they do not expose.",
    ),
    "get_priority_incidents": ToolGuidance(
        when_to_use='the user names a priority (P1/P2/"priority 1") and wants the matching incidents, optionally within a date range.',
        when_not='free-text topic search ("incidents about X") — use search_records; arbitrary field filters — use filter_records.',
        prefer_over="filter_records only for the priority-plus-date shape, which this tool builds with reliable >= / <= operators.",
    ),
    "get_kb_articles_by_state": ToolGuidance(
        when_to_use='the user asks which articles are in a given publication state ("currently in published state", "drafts", "retired KB").',
        when_not="subject search (search_records on kb_knowledge); one category with no state question (filter_records with kb_category).",
        prefer_over="filter_records — this collapses ServiceNow's version rows that a raw filter would return duplicated.",
    ),
    "create_private_task": ToolGuidance(
        when_to_use="the user wants a brand-new private task opened.",
        when_not="to modify a task that already exists (its VTB number is known) — use update_private_task instead.",
        prefer_over="nothing; this is the only insert path for vtb_task.",
    ),
    "update_private_task": ToolGuidance(
        when_to_use="the task already exists and the user wants to set, close, reassign, or otherwise change it. A VTB number together with a change verb (set / close / update / reassign) is always this tool.",
        when_not="opening a brand-new task — use create_private_task.",
        prefer_over="create_private_task whenever the record already exists.",
    ),
    "update_knowledge_article": ToolGuidance(
        when_to_use='change an article\'s content or metadata — "update the body text of KB0001234".',
        when_not="changing publication state — publish (publish_knowledge_article) or retire (retire_knowledge_article).",
        prefer_over="nothing; this is the kb_knowledge field-write path.",
    ),
    "publish_knowledge_article": ToolGuidance(
        when_to_use='publish a single article — "publish knowledge article KB0001234".',
        when_not="several articles at once (use publish_knowledge_articles); only checking for duplicates without publishing (check_kb_duplicates).",
        prefer_over="publish_knowledge_articles when there is exactly one article.",
    ),
    "publish_knowledge_articles": ToolGuidance(
        when_to_use='two or more articles to publish together — "publish KB0001234, KB0001235 and KB0001236 in one go".',
        when_not="exactly one article (use publish_knowledge_article); checking duplicates without publishing (check_kb_duplicates).",
        prefer_over="calling publish_knowledge_article in a loop — this batches and never lets one failure abort the rest.",
    ),
    "retire_knowledge_article": ToolGuidance(
        when_to_use='take a published article out of service — "retire knowledge article KB0004321".',
        when_not="publishing (publish_knowledge_article); editing content (update_knowledge_article).",
        prefer_over="nothing; this is the kb_knowledge retire path.",
    ),
    "check_kb_duplicates": ToolGuidance(
        when_to_use='confirm an article has no duplicates before publishing — "check whether KB0001234 has duplicates before I publish it".',
        when_not="actually publishing (publish_knowledge_article / publish_knowledge_articles run this check themselves first).",
        prefer_over="nothing; this is the standalone duplicate probe.",
    ),
    "get_sla_details": ToolGuidance(
        when_to_use="you hold the SLA's 32-char sys_id and want that single row.",
        when_not="you have a task number rather than a sys_id — use query_slas_by_task; a status or stage query — use query_slas_by_status.",
        prefer_over="query_slas_custom for a known-sys_id point lookup.",
    ),
    "query_slas_by_task": ToolGuidance(
        when_to_use="you have a task number (INC/CHG/RITM/SCTASK/...) and want the SLAs attached to it.",
        when_not="matching SLAs by the task's wording — use filter_records('task_sla', {'task.short_description': 'LIKE...'}); filtering by status or stage — use query_slas_by_status.",
        prefer_over="query_slas_custom for this exact task-number lookup.",
    ),
    "query_slas_by_status": ToolGuidance(
        when_to_use='the intent maps to a preset — breached, breaching, active, critical, by_stage, performance ("which SLAs are breached").',
        when_not="SLAs for one task number (query_slas_by_task); a filter no preset covers (query_slas_custom).",
        prefer_over="query_slas_custom whenever a preset fits — presets carry curated field lists that protect the token budget.",
    ),
    "query_slas_custom": ToolGuidance(
        when_to_use="the SLA filter you need is not one of query_slas_by_status's presets, and it is not a plain task-number or task-text lookup.",
        when_not="a preset fits (query_slas_by_status); one task number (query_slas_by_task).",
        prefer_over="filter_records only when you want task_sla ESSENTIAL_FIELDS defaulting and the optional last-N-days convenience.",
    ),
    "find_cis_by_type": ToolGuidance(
        when_to_use='the user names a CI class — "list every Linux server configuration item".',
        when_not="searching by attributes like location/IP/status (search_cis_by_attributes); one CI by number (get_ci_details).",
        prefer_over="search_cis_by_attributes when the filter is purely the class.",
    ),
    "search_cis_by_attributes": ToolGuidance(
        when_to_use='the user filters CIs by attribute — location, IP, status, name — "configuration items at location Brussels with status installed".',
        when_not="a whole class with no attribute filter (find_cis_by_type); one CI by number (get_ci_details).",
        prefer_over="find_cis_by_type when the ask includes location/IP/status.",
    ),
    "get_ci_details": ToolGuidance(
        when_to_use='you know the CI number and want its complete record — "get all details for configuration item SRV0001234".',
        when_not="searching by class (find_cis_by_type) or attributes (search_cis_by_attributes); a loose name/IP lookup (quick_ci_search).",
        prefer_over="quick_ci_search when you have an exact CI number.",
    ),
    "similar_cis_for_ci": ToolGuidance(
        when_to_use="you have one CI and want others like it (same class, location, status).",
        when_not="attribute search from scratch (search_cis_by_attributes); one CI's own detail (get_ci_details).",
        prefer_over="search_cis_by_attributes when the seed is an existing CI.",
    ),
    "get_all_ci_types": ToolGuidance(
        when_to_use='the user wants the list of CI classes this instance defines — "which CI classes exist in this CMDB".',
        when_not="rows of one class (find_cis_by_type); a specific CI (get_ci_details).",
        prefer_over="nothing; this is the class-discovery path.",
    ),
    "quick_ci_search": ToolGuidance(
        when_to_use="you have one loose term and don't know which field it is.",
        when_not="an exact CI number (get_ci_details); structured attribute filters (search_cis_by_attributes); a whole class (find_cis_by_type).",
        prefer_over="get_ci_details only when the term may not be a CI number.",
    ),
    "get_query_syntax_help": ToolGuidance(
        when_to_use='you need the operator vocabulary in general — "which encoded query operators does ServiceNow support".',
        when_not="running a query (search_records / filter_records); inspecting the live connection (health_check).",
        prefer_over="guessing operator syntax when constructing a filter value.",
    ),
}
