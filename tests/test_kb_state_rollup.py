"""Regression tests for the `get_kb_articles_by_state` dedup/truncation defects.

Found by live testing against KB `a9703827c38a2e1026bb03d9d0013148` (2026-08-12),
where the tool reported **1** draft against `filter_records`' **48**.

Two distinct defects, both silent — no error, no exception, just wrong data:

1. **Priority collapse hid drafts.** The `workflow_state` filter tested equality
   against `current_state` (the priority WINNER). An article re-drafted for an
   update has both a `published` and a `draft` row, so `published` won and the
   article vanished from a `draft` filter. 47 of that KB's 48 pending drafts
   followed this pattern — the common case, not an edge case.

2. **Raw-scan truncation poisoned `current_state`.** `max_results` capped the RAW
   row fetch, and dedup then ran on whatever arrived. Because the scan sorts
   `sys_created_on` DESC, a recent `draft` row could land inside the cap while
   its older `published` sibling fell off the end — so `current_state` came back
   *wrong*, not merely missing. Worse than an incomplete list: a confidently
   incorrect answer for rows that DID make it into the output.
"""
import pytest
from unittest.mock import patch

from Table_Tools.consolidated_tools import (
    get_kb_articles_by_state,
    _pick_canonical_kb_row,
)
from constants import KB_STATE_SCAN_LIMIT


def _rows(*specs):
    """Build raw kb_knowledge rows from (number, state, sys_id) triples."""
    return [
        {
            "number": num,
            "sys_id": sys_id,
            "short_description": f"desc {num}",
            "workflow_state": state,
            "kb_category": "Docs",
            "sys_updated_on": "2026-08-12 07:30:03",
        }
        for num, state, sys_id in specs
    ]


class TestDraftMaskedByPublished:
    """Defect 1: a draft on an already-published article must stay discoverable."""

    @pytest.mark.asyncio
    async def test_draft_filter_finds_redrafted_published_article(self):
        """The live KB0011378 case: Draft + Published rows, filtered on draft."""
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {
                "result": _rows(
                    ("KB0011378", "draft", "s_draft"),
                    ("KB0011378", "published", "s_pub"),
                ),
                "truncated": False,
            }
            result = await get_kb_articles_by_state(workflow_state="draft")

        numbers = [r["number"] for r in result["result"]]
        assert numbers == ["KB0011378"], (
            "a draft on an already-published article was dropped by the "
            "priority collapse — the defect that hid 47 of 48 live drafts"
        )

    @pytest.mark.asyncio
    async def test_canonical_state_still_reports_the_priority_winner(self):
        """`current_state` keeps its verification meaning: published wins."""
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {
                "result": _rows(
                    ("KB0011378", "draft", "s_draft"),
                    ("KB0011378", "published", "s_pub"),
                ),
                "truncated": False,
            }
            result = await get_kb_articles_by_state(workflow_state="draft")

        row = result["result"][0]
        assert row["current_state"] == "published"
        assert row["states_present"] == ["published", "draft"]
        assert row["version_count"] == 2

    @pytest.mark.asyncio
    async def test_states_present_ordered_by_priority(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {
                "result": _rows(
                    ("KB001", "retired", "s1"),
                    ("KB001", "draft", "s2"),
                    ("KB001", "published", "s3"),
                    ("KB001", "outdated", "s4"),
                ),
                "truncated": False,
            }
            result = await get_kb_articles_by_state()

        assert result["result"][0]["states_present"] == [
            "published", "draft", "outdated", "retired",
        ]

    @pytest.mark.asyncio
    async def test_published_filter_is_unchanged_by_membership(self):
        """`published` is rank 0, so membership and equality coincide there.

        This is why the fix widens draft/review discovery without loosening the
        published view: `current_state == "published"` already implies
        `"published" in states_present`.
        """
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {
                "result": _rows(
                    ("KB001", "published", "s1"),
                    ("KB002", "draft", "s2"),
                    ("KB003", "retired", "s3"),
                ),
                "truncated": False,
            }
            result = await get_kb_articles_by_state(workflow_state="published")

        assert [r["number"] for r in result["result"]] == ["KB001"]

    @pytest.mark.asyncio
    async def test_state_absent_everywhere_returns_empty(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {
                "result": _rows(("KB001", "published", "s1")),
                "truncated": False,
            }
            result = await get_kb_articles_by_state(workflow_state="review")

        assert result["result"] == []
        assert result["returned_count"] == 0
        assert "error" not in result

    def test_pick_canonical_tracks_every_state_seen(self):
        info = _pick_canonical_kb_row(
            _rows(("KB001", "draft", "s1"), ("KB001", "published", "s2"))
        )["KB001"]
        assert info["states"] == {"draft", "published"}
        assert info["row"]["sys_id"] == "s2"


class TestRawScanDecoupledFromOutputCap:
    """Defect 2: truncating the raw scan must never produce a wrong state."""

    @pytest.mark.asyncio
    async def test_scan_uses_its_own_ceiling_not_max_results(self):
        """`max_results` shapes OUTPUT; the raw scan runs to its own ceiling.

        The live failure: max_results=100 fetched 100 of 363 raw rows, so
        KB0011378's published row fell off the end and it reported
        `current_state: draft`.
        """
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": [], "truncated": False}
            await get_kb_articles_by_state(max_results=10)

        params = mock_query.call_args[0][1]
        assert params.max_results == KB_STATE_SCAN_LIMIT, (
            "the raw scan must not inherit the caller's output cap"
        )

    @pytest.mark.asyncio
    async def test_max_results_caps_deduped_output(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {
                "result": _rows(*[(f"KB{i:04d}", "published", f"s{i}") for i in range(10)]),
                "truncated": False,
            }
            result = await get_kb_articles_by_state(max_results=4)

        assert result["returned_count"] == 4
        assert result["truncated"] is True

    @pytest.mark.asyncio
    async def test_complete_output_is_not_truncated(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {
                "result": _rows(*[(f"KB{i:04d}", "published", f"s{i}") for i in range(3)]),
                "truncated": False,
            }
            result = await get_kb_articles_by_state(max_results=100)

        assert result["truncated"] is False
        assert "scan_incomplete" not in result

    @pytest.mark.asyncio
    async def test_capped_scan_flags_states_as_untrustworthy(self):
        """A capped raw scan poisons EVERY number's state, so say so loudly."""
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {
                "result": _rows(("KB0011378", "draft", "s_draft")),
                "truncated": True,
            }
            result = await get_kb_articles_by_state()

        assert result["scan_incomplete"] is True
        assert str(KB_STATE_SCAN_LIMIT) in result["warning"]
        assert "current_state" in result["warning"]
        # Rows are still served — discarding them would be the bug class this
        # repo already fixed for partial pages.
        assert result["result"][0]["number"] == "KB0011378"

    @pytest.mark.asyncio
    async def test_capped_scan_warns_even_when_filter_empties_the_set(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {
                "result": _rows(("KB001", "published", "s1")),
                "truncated": True,
            }
            result = await get_kb_articles_by_state(workflow_state="review")

        assert result["result"] == []
        assert result["scan_incomplete"] is True, (
            "an empty answer off a capped scan must not read as a clean 'none found'"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("bad", [0, -1, KB_STATE_SCAN_LIMIT + 1])
    async def test_out_of_range_max_results_is_a_validation_error(self, bad):
        """Previously raised an unhandled pydantic ValidationError."""
        result = await get_kb_articles_by_state(max_results=bad)
        assert result["error"]["code"] == "VALIDATION"


class TestReadFailuresStillPropagate:
    """The v4.4 Tier 0.3 contract must survive the rewrite."""

    @pytest.mark.asyncio
    async def test_failure_passes_through_untouched(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {
                "error": {"code": "TIMEOUT", "message": "timed out"}
            }
            result = await get_kb_articles_by_state()

        assert result["error"]["code"] == "TIMEOUT"
        assert "result" not in result

    @pytest.mark.asyncio
    async def test_partial_read_keeps_its_rows_and_error(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {
                "result": _rows(("KB001", "published", "s1")),
                "truncated": False,
                "partial": True,
                "error": {"code": "TIMEOUT", "message": "page 2 died"},
            }
            result = await get_kb_articles_by_state()

        assert result["partial"] is True
        assert result["error"]["code"] == "TIMEOUT"
        assert result["result"][0]["number"] == "KB001"

    @pytest.mark.asyncio
    async def test_partial_emptied_by_filter_reports_the_failure(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {
                "result": _rows(("KB001", "published", "s1")),
                "truncated": False,
                "partial": True,
                "error": {"code": "TIMEOUT", "message": "page 2 died"},
            }
            result = await get_kb_articles_by_state(workflow_state="review")

        assert result["error"]["code"] == "TIMEOUT"
        assert not result.get("result")
