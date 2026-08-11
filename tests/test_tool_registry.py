"""Tool-guidance registry + docstring-footer injection (v5.0 "Boron" Tier 3.3).

Pins the structured selection-guidance mechanism: every registered tool has a
TOOL_GUIDANCE entry, the entry is injected as a single canonical docstring footer,
injection is idempotent, and registration refuses a tool with no guidance (which
is what makes the WHEN/WHEN-NOT/PREFER protocol mandatory rather than merely a
docstring convention). The golden-set test can now read these three fields as
structured data instead of parsing them back out of prose.
"""
from __future__ import annotations

import inspect

import pytest

import tools
from tool_registry import (
    TOOL_GUIDANCE,
    ToolGuidance,
    apply_guidance,
    guidance_footer,
    register_tools,
)

_REGISTERED = {fn.__name__ for fn in tools.tools}


class TestGuidanceCoverage:
    """The registry and the registered surface must match exactly."""

    def test_every_registered_tool_has_guidance(self):
        missing = _REGISTERED - set(TOOL_GUIDANCE)
        assert not missing, f"registered tools with no TOOL_GUIDANCE entry: {sorted(missing)}"

    def test_no_stale_guidance_entries(self):
        stale = set(TOOL_GUIDANCE) - _REGISTERED
        assert not stale, f"TOOL_GUIDANCE entries for unregistered tools: {sorted(stale)}"

    def test_all_three_fields_non_empty(self):
        for name, g in TOOL_GUIDANCE.items():
            assert isinstance(g, ToolGuidance), name
            assert g.when_to_use.strip(), name
            assert g.when_not.strip(), name
            assert g.prefer_over.strip(), name


class TestFooterInjection:
    """The registered docstring carries exactly one generated guidance footer."""

    def test_footer_present_once_in_every_registered_doc(self):
        for fn in tools.tools:
            doc = inspect.getdoc(fn) or ""
            assert doc.count("WHEN TO USE:") == 1, f"{fn.__name__}: guidance block not unique"
            assert doc.count("PREFER OVER:") == 1, fn.__name__
            assert guidance_footer(fn.__name__) in doc, f"{fn.__name__}: footer text missing"

    def test_footer_is_the_tail_of_the_doc(self):
        for fn in tools.tools:
            doc = inspect.getdoc(fn) or ""
            assert doc.rstrip().endswith(guidance_footer(fn.__name__)), fn.__name__

    def test_injection_is_idempotent(self):
        async def sample():
            """A summary line.

            WHEN TO USE: original prose here.
            WHEN NOT TO USE: not this.
            PREFER OVER: nothing.

            Args:
                x: whatever
            """

        # Borrow a real tool's guidance so guidance_footer has an entry.
        sample.__name__ = "get_record"
        once = apply_guidance(sample).__doc__
        twice = apply_guidance(sample).__doc__
        assert once == twice
        assert once.count("WHEN TO USE:") == 1
        # The original prose guidance was replaced by the canonical footer.
        assert "original prose here" not in once
        assert "A summary line." in once and "Args:" in once


class TestProtocolIsMandatory:
    """register_tools fails loudly on a tool with no guidance."""

    def test_register_tools_rejects_ungoverned_tool(self):
        class _FakeMcp:
            def tool(self):
                return lambda fn: fn

        async def brand_new_tool():
            """No guidance entry exists for this one."""

        with pytest.raises(ValueError, match="no TOOL_GUIDANCE entry"):
            register_tools(_FakeMcp(), [brand_new_tool])
