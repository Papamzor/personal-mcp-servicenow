"""Token-footprint regression tests for v4.0 SLA tools.

The Sprint 2 acceptance criterion is a per-tool token budget enforced
in CI without requiring access to a live ServiceNow instance. This
suite mocks the query layer with synthetic SLA payloads, invokes each
v4 tool, tokenizes the resulting JSON via tiktoken (cl100k_base — the
encoding Claude/GPT-4 family uses), and asserts the token count stays
within the budget recorded at v4.0/token_baseline.json.

Budgets are derived from the live baseline captured 2026-05-20 plus a
~5% / 50-token noise tolerance. They are intentionally loose — the
test catches structural regressions (added fields, lost flattening,
forgotten exclude_reference_link), not single-row data churn.
"""
from __future__ import annotations

import inspect
import json
from unittest.mock import patch

import pytest
import tiktoken

import tools
from Table_Tools.consolidated_tools import (
    _SLA_CRITICAL_FIELDS,
    _SLA_PERFORMANCE_FIELDS,
    get_sla_details,
    query_slas_by_status,
    query_slas_by_task,
    query_slas_custom,
)

ENCODER = tiktoken.get_encoding("cl100k_base")


def _count_tokens(payload) -> int:
    return len(ENCODER.encode(json.dumps(payload, default=str)))


# ---------------------------------------------------------------------------
# Tool-listing footprint (v4.5.0 Tier 1).
#
# The docstrings are sent to the model on every tool listing, once per
# conversation (and cached). Tier 1's docstring protocol lengthened all 39, so
# this measures the whole listing payload — name + signature + docstring per
# tool — the payload the earlier per-response budgets never covered.
#
# Recorded trade (cl100k_base tokens, measured at each release):
#   c951471 (v4.4.1, pre-Tier-1):   4693
#   v4.5.0 (Tier 1 docstrings):     8946   (+4253, +91%)
#   v5.0.0 (Tier 2, 39 -> 25 cull): 6716   (-2230, -25% from Tier 1)
# Tier 1's docstring protocol lengthened all tools; Tier 2's cull removed 15 of
# them, bringing the listing back down while keeping the protocol on every
# survivor. Static tool-selection held at preferred 28/30 (see
# tests/test_tool_selection.py for why 28, not 29).
# ---------------------------------------------------------------------------

# Ceiling with headroom for ordinary doc edits; a runaway (e.g. a re-introduced
# unconditional envelope, or protocol duplication) trips it. Ratcheted down from
# 9_500 (Tier 1) after the Tier 2 cull shrank the surface — floors ratchet down,
# never silently up.
BUDGET_TOOL_LISTING = 7_200


def _tool_listing_tokens() -> int:
    """Total tokens of the registered tool listing: name + signature + docstring."""
    total = 0
    for fn in tools.tools:
        doc = inspect.getdoc(fn) or ""
        text = f"{fn.__name__}{inspect.signature(fn)}\n{doc}"
        total += len(ENCODER.encode(text))
    return total


class TestToolListingFootprint:
    """The one-time tool-listing payload must not balloon past its budget."""

    def test_tool_listing_under_budget(self):
        total = _tool_listing_tokens()
        assert total <= BUDGET_TOOL_LISTING, (
            f"tool-listing footprint {total} tokens exceeds budget "
            f"{BUDGET_TOOL_LISTING}; a docstring grew unexpectedly or the "
            f"protocol was duplicated. Re-measure and justify before raising."
        )

    def test_every_tool_has_a_docstring(self):
        """The protocol is worthless if a tool ships with no docstring at all."""
        missing = [fn.__name__ for fn in tools.tools if not (inspect.getdoc(fn) or "").strip()]
        assert not missing, f"tools with no docstring: {missing}"


# ---------------------------------------------------------------------------
# Synthetic SLA row fixtures
# ---------------------------------------------------------------------------

# Mirrors ESSENTIAL_FIELDS["task_sla"] from constants.py.
_ESSENTIAL_ROW = {
    "task": "INC0010001",
    "sla": "Resolution P1",
    "stage": "In progress",
    "business_percentage": "45.2",
    "active": "true",
    "sys_created_on": "2026-04-15 10:30:00",
}

_CRITICAL_ROW = {field: f"sample_{field}" for field in _SLA_CRITICAL_FIELDS}
_PERFORMANCE_ROW = {field: f"sample_{field}" for field in _SLA_PERFORMANCE_FIELDS}


def _response(rows, count: int):
    return {"result": [rows] * count}


# ---------------------------------------------------------------------------
# Per-tool budgets (tokens). Baseline + noise tolerance.
# Values aligned with v4.0/token_baseline.json (see scripts/capture_*).
# ---------------------------------------------------------------------------

# Single-row sys_id lookup. v3 broken behaviour returned 10K rows / 1.2M tokens;
# v4 returns exactly one row. Budget kept tight to catch regressions.
BUDGET_GET_SLA_DETAILS = 200

# By-task lookups typically return 1-3 rows.
BUDGET_QUERY_SLAS_BY_TASK = 500

# Standard list views (active, breached, by_stage). 100 rows of ESSENTIAL_FIELDS.
BUDGET_QUERY_SLAS_STANDARD_LIST = 7_000

# Critical preset returns 7 curated fields × ~24 rows (P1/P2 active >80%).
# Even at 100 rows the curated view fits under 8K tokens.
BUDGET_QUERY_SLAS_CRITICAL = 8_000

# Performance preset returns 11 curated fields × 100 rows.
BUDGET_QUERY_SLAS_PERFORMANCE = 13_000

# Breaching preset typically returns 0-10 rows (rare condition).
BUDGET_QUERY_SLAS_BREACHING = 1_500


# ---------------------------------------------------------------------------
# Helper — patch the query layer to return a fixture and invoke the tool.
# ---------------------------------------------------------------------------

async def _run_with_mock_response(tool_coroutine_factory, response):
    """Patch query_table_with_filters to return `response`, then call the tool."""
    with patch(
        "Table_Tools.consolidated_tools.query_table_with_filters",
        return_value=response,
    ):
        return await tool_coroutine_factory()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSLATokenFootprint:
    """Per-tool token budgets — must not regress structurally."""

    @pytest.mark.asyncio
    async def test_get_sla_details_single_row(self):
        """v3 bug returned 10K rows; v4 must return 1."""
        response = _response(_ESSENTIAL_ROW, 1)
        result = await _run_with_mock_response(
            lambda: get_sla_details("abc123"), response
        )
        tokens = _count_tokens(result)
        assert tokens <= BUDGET_GET_SLA_DETAILS, (
            f"get_sla_details token count {tokens} exceeds budget {BUDGET_GET_SLA_DETAILS}"
        )

    @pytest.mark.asyncio
    async def test_query_slas_by_task(self):
        response = _response(_ESSENTIAL_ROW, 2)
        result = await _run_with_mock_response(
            lambda: query_slas_by_task("INC0010001"), response
        )
        tokens = _count_tokens(result)
        assert tokens <= BUDGET_QUERY_SLAS_BY_TASK

    @pytest.mark.asyncio
    @pytest.mark.parametrize("status", ["active", "breached", "by_stage"])
    async def test_standard_list_presets_under_budget(self, status):
        response = _response(_ESSENTIAL_ROW, 100)
        kwargs = {"stage": "in_progress"} if status == "by_stage" else {}
        result = await _run_with_mock_response(
            lambda: query_slas_by_status(status, **kwargs), response
        )
        tokens = _count_tokens(result)
        assert tokens <= BUDGET_QUERY_SLAS_STANDARD_LIST, (
            f"query_slas_by_status({status!r}) tokens {tokens} > budget {BUDGET_QUERY_SLAS_STANDARD_LIST}"
        )

    @pytest.mark.asyncio
    async def test_critical_preset_uses_curated_view(self):
        """Critical preset budget is tight because the field list is curated."""
        response = _response(_CRITICAL_ROW, 100)
        result = await _run_with_mock_response(
            lambda: query_slas_by_status("critical"), response
        )
        tokens = _count_tokens(result)
        assert tokens <= BUDGET_QUERY_SLAS_CRITICAL

    @pytest.mark.asyncio
    async def test_performance_preset_uses_11_field_view(self):
        response = _response(_PERFORMANCE_ROW, 100)
        result = await _run_with_mock_response(
            lambda: query_slas_by_status("performance"), response
        )
        tokens = _count_tokens(result)
        assert tokens <= BUDGET_QUERY_SLAS_PERFORMANCE

    @pytest.mark.asyncio
    async def test_breaching_preset_small_result_set(self):
        response = _response(_ESSENTIAL_ROW, 10)
        result = await _run_with_mock_response(
            lambda: query_slas_by_status("breaching"), response
        )
        tokens = _count_tokens(result)
        assert tokens <= BUDGET_QUERY_SLAS_BREACHING

    @pytest.mark.asyncio
    async def test_query_slas_custom_defaults_to_essential_fields(self):
        """Token budget invariant: custom with fields=None never returns all columns."""
        # The mock returns whatever we feed it — what we are asserting is that
        # the call surface defaults fields=None (verified by the dispatch test
        # elsewhere) so the query layer falls back to ESSENTIAL_FIELDS.
        response = _response(_ESSENTIAL_ROW, 100)
        result = await _run_with_mock_response(
            lambda: query_slas_custom({"active": "true"}), response
        )
        tokens = _count_tokens(result)
        assert tokens <= BUDGET_QUERY_SLAS_STANDARD_LIST


# ---------------------------------------------------------------------------
# Per-response envelope overhead (v5.0 "Boron" Tier 3.1).
#
# The §3.1 contract's headline risk is a re-introduced unconditional `meta`
# envelope (tool/table/query/fields/duration_ms) — the v2 plan's worst error,
# a 100-300% regression on a call like get_sla_details. These guards pin the
# ENVELOPE OVERHEAD: tokens(response) minus tokens({"result": rows}) — i.e.
# everything the tool adds around the data. list_response adds only
# returned_count + truncated (+ max_results); record_response adds only the
# `record` key. A meta envelope would blow straight past the ceiling.
#
# Measuring overhead, not an absolute count, keeps the guard immune to row-count
# and per-row data churn while still catching a structural regression — exactly
# the property the loose SLA budgets above were reaching for.
# ---------------------------------------------------------------------------

# list_response wraps rows in {result, returned_count, truncated, (max_results)}.
# Those keys + small int/bool values tokenize to ~12; 40 leaves headroom for a
# `suggestions` hint or a CMDB descriptor key, but not for a meta envelope.
BUDGET_LIST_ENVELOPE_OVERHEAD = 40
# record_response is just {"record": row} on a read — a handful of tokens.
BUDGET_RECORD_ENVELOPE_OVERHEAD = 15

_GENERIC_ROW = {
    "number": "INC0010001",
    "short_description": "Server crashed during nightly backup window",
    "priority": "1",
    "state": "2",
    "assignment_group": "SN Fleet",
    "sys_created_on": "2026-04-15 10:30:00",
}
_CI_ROW = {
    "number": "SRV0001234",
    "name": "host-app-01",
    "sys_class_name": "cmdb_ci_server",
    "operational_status": "1",
    "install_status": "1",
    "sys_created_on": "2026-04-15 10:30:00",
    "sys_updated_on": "2026-04-20 09:00:00",
}


def _list_envelope_overhead(resp) -> int:
    """tokens(resp) - tokens({"result": resp["result"]}) — the wrapper's cost."""
    return _count_tokens(resp) - _count_tokens({"result": resp["result"]})


class TestPerResponseEnvelopeFootprint:
    """No unconditional meta envelope on the default read path (plan §3.1)."""

    @pytest.mark.asyncio
    async def test_filter_records_envelope_is_thin(self):
        from Table_Tools.generic_tool_wrappers import filter_records
        rows = [dict(_GENERIC_ROW) for _ in range(100)]
        with patch("Table_Tools.generic_table_tools._make_paginated_request",
                   return_value=rows):
            resp = await filter_records("incident", {"priority": "1"})
        assert resp["result"]
        assert "message" not in resp
        assert _list_envelope_overhead(resp) <= BUDGET_LIST_ENVELOPE_OVERHEAD

    @pytest.mark.asyncio
    async def test_search_records_envelope_is_thin(self):
        from Table_Tools.generic_tool_wrappers import search_records
        rows = [dict(_GENERIC_ROW) for _ in range(50)]
        with patch("Table_Tools.generic_table_tools._make_paginated_request",
                   return_value=rows):
            resp = await search_records("incident", "server crash backup")
        assert resp["result"]
        assert "message" not in resp
        assert _list_envelope_overhead(resp) <= BUDGET_LIST_ENVELOPE_OVERHEAD

    @pytest.mark.asyncio
    async def test_get_record_envelope_is_thin(self):
        from Table_Tools.generic_tool_wrappers import get_record
        with patch("Table_Tools.generic_table_tools.make_nws_request",
                   return_value={"result": [dict(_GENERIC_ROW)]}):
            resp = await get_record("incident", "INC0010001")
        assert "record" in resp
        assert "result" not in resp
        overhead = _count_tokens(resp) - _count_tokens({"record": resp["record"]})
        assert overhead <= BUDGET_RECORD_ENVELOPE_OVERHEAD

    @pytest.mark.asyncio
    async def test_cmdb_list_envelope_is_thin(self):
        from Table_Tools.cmdb_tools import find_cis_by_type
        rows = [dict(_CI_ROW) for _ in range(100)]
        with patch("Table_Tools.cmdb_tools.make_nws_request",
                   return_value={"result": rows}):
            resp = await find_cis_by_type("cmdb_ci_server")
        assert resp["result"]
        assert "message" not in resp
        # CMDB list carries a `ci_type` descriptor key; still well under budget.
        assert _list_envelope_overhead(resp) <= BUDGET_LIST_ENVELOPE_OVERHEAD


class TestSLATokenBudgetConstants:
    """Lock budget constants — accidental relaxation should fail review."""

    def test_critical_budget_below_standard_list(self):
        """Curated 7-field view must be at most ~15% over standard ESSENTIAL list."""
        assert BUDGET_QUERY_SLAS_CRITICAL <= BUDGET_QUERY_SLAS_STANDARD_LIST * 1.2

    def test_performance_budget_proportional_to_field_count(self):
        """Performance preset has 11 fields vs essential's 6; budget reflects that."""
        # Performance has roughly 1.83x the fields, so budget can be up to 2x.
        assert BUDGET_QUERY_SLAS_PERFORMANCE <= BUDGET_QUERY_SLAS_STANDARD_LIST * 2

    def test_details_budget_is_single_row_scale(self):
        """A sys_id lookup must never need more than ~200 tokens (1 row)."""
        assert BUDGET_GET_SLA_DETAILS <= 250
