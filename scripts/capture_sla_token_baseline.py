"""Capture SLA tool token baseline for v4.0 Sprint 2.

Runs each of the 10 SLA-related MCP tools against the live ServiceNow
instance configured via .env, measures the JSON response token count
using tiktoken (cl100k_base, the encoding Claude/GPT-4 family uses),
and writes results to v4.0/token_baseline.json.

The Sprint 2 collapse (10 -> 5 tools) must not exceed any per-tool
token count recorded here. The baseline becomes the regression budget.

Run:
    python scripts/capture_sla_token_baseline.py

Output:
    v4.0/token_baseline.json
"""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

import tiktoken

# Make repo root importable when run as script
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from Table_Tools.consolidated_tools import (  # noqa: E402
    get_active_slas,
    get_breached_slas,
    get_breaching_slas,
    get_critical_sla_status,
    get_recent_breached_slas,
    get_sla_details,
    get_sla_performance_summary,
    get_slas_by_stage,
    get_slas_for_task,
    similar_slas_for_text,
)
from Table_Tools.generic_table_tools import (  # noqa: E402
    TableFilterParams,
    query_table_with_filters,
)

ENCODER = tiktoken.get_encoding("cl100k_base")
OUTPUT_PATH = REPO_ROOT / "v4.0" / "token_baseline.json"


def count_tokens(payload: Any) -> int:
    """Count tokens of the JSON-serialised response."""
    return len(ENCODER.encode(json.dumps(payload, default=str)))


async def discover_sample_sla() -> dict[str, str | None]:
    """Probe for a real task number and SLA sys_id to use in by-id calls.

    ESSENTIAL_FIELDS for task_sla omits sys_id, so do a small custom-field
    query just for discovery — does not affect the per-tool baseline.
    """
    probe = await query_table_with_filters(
        "task_sla",
        TableFilterParams(
            filters={"active": "true"},
            fields=["sys_id", "task.number"],
        ),
    )
    rows = probe.get("result") if isinstance(probe, dict) else None
    if not rows:
        return {"task_number": None, "sla_sys_id": None}
    first = rows[0]
    return {
        "task_number": first.get("task.number"),
        "sla_sys_id": first.get("sys_id"),
    }


async def measure(
    name: str,
    call: Callable[[], Awaitable[Any]],
    args_repr: str,
) -> dict[str, Any]:
    """Invoke a tool, measure its response, and return a record."""
    try:
        response = await call()
        rows = (
            len(response["result"])
            if isinstance(response, dict) and isinstance(response.get("result"), list)
            else None
        )
        char_count = len(json.dumps(response, default=str))
        token_count = count_tokens(response)
        return {
            "tool": name,
            "args": args_repr,
            "ok": True,
            "rows": rows,
            "response_chars": char_count,
            "response_tokens": token_count,
        }
    except Exception as exc:  # noqa: BLE001 - baseline must not abort on one failure
        return {
            "tool": name,
            "args": args_repr,
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "response_chars": None,
            "response_tokens": None,
        }


async def main() -> int:
    sample = await discover_sample_sla()
    task_number = sample["task_number"]
    sla_sys_id = sample["sla_sys_id"]

    records: list[dict[str, Any]] = []

    records.append(
        await measure(
            "similar_slas_for_text",
            lambda: similar_slas_for_text("incident"),
            'input_text="incident"',
        )
    )

    if task_number:
        records.append(
            await measure(
                "get_slas_for_task",
                lambda: get_slas_for_task(task_number),
                f"task_number={task_number!r}",
            )
        )
    else:
        records.append({"tool": "get_slas_for_task", "args": "skipped", "ok": False, "error": "no sample task discovered"})

    if sla_sys_id:
        # NOTE: v3.0 bug — get_sla_details calls get_record_details which builds
        # `number={sys_id}` filter, but task_sla has no `number` field. Query is
        # silently ignored, returning the full default page (10,000 rows). The
        # broken behavior is what production sees today; v4 Sprint 2 will fix it.
        broken = await measure(
            "get_sla_details",
            lambda: get_sla_details(sla_sys_id),
            f"sla_sys_id={sla_sys_id!r}",
        )
        broken["known_bug"] = "task_sla has no 'number' field; get_record_details returns full table dump"
        records.append(broken)

        # Capture the corrected lookup token cost so Sprint 2 has a real target.
        corrected = await measure(
            "get_sla_details (corrected sys_id= lookup)",
            lambda: query_table_with_filters(
                "task_sla",
                TableFilterParams(filters={"sys_id": sla_sys_id}),
            ),
            f"filters={{'sys_id': {sla_sys_id!r}}}",
        )
        corrected["note"] = "post-fix target — Sprint 2 must land near this number, not the broken one"
        records.append(corrected)
    else:
        records.append({"tool": "get_sla_details", "args": "skipped", "ok": False, "error": "no sample sys_id discovered"})

    records.append(
        await measure(
            "get_breaching_slas",
            lambda: get_breaching_slas(60),
            "time_threshold_minutes=60",
        )
    )
    records.append(
        await measure(
            "get_breached_slas",
            lambda: get_breached_slas(days=7),
            "days=7",
        )
    )
    records.append(
        await measure(
            "get_slas_by_stage",
            lambda: get_slas_by_stage("in_progress"),
            'stage="in_progress"',
        )
    )
    records.append(
        await measure(
            "get_active_slas",
            lambda: get_active_slas(),
            "(no args)",
        )
    )
    records.append(
        await measure(
            "get_sla_performance_summary",
            lambda: get_sla_performance_summary(days=30),
            "days=30",
        )
    )
    records.append(
        await measure(
            "get_recent_breached_slas",
            lambda: get_recent_breached_slas(days=1),
            "days=1",
        )
    )
    records.append(
        await measure(
            "get_critical_sla_status",
            lambda: get_critical_sla_status(),
            "(no args)",
        )
    )

    baseline = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "encoder": "cl100k_base",
        "sample_task_number": task_number,
        "sample_sla_sys_id": sla_sys_id,
        "tools": records,
        "totals": {
            "tools_measured": sum(1 for r in records if r.get("ok")),
            "tools_failed": sum(1 for r in records if not r.get("ok")),
            "total_response_tokens": sum(r.get("response_tokens") or 0 for r in records),
            "total_response_chars": sum(r.get("response_chars") or 0 for r in records),
        },
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(baseline, indent=2), encoding="utf-8")

    print(f"Baseline written to {OUTPUT_PATH}")
    print(f"  Tools measured: {baseline['totals']['tools_measured']}/10")
    print(f"  Total response tokens: {baseline['totals']['total_response_tokens']:,}")
    print(f"  Total response chars:  {baseline['totals']['total_response_chars']:,}")
    print()
    print(f"{'Tool':<35} {'Rows':>6} {'Chars':>10} {'Tokens':>10}")
    print("-" * 65)
    for r in records:
        if r.get("ok"):
            print(
                f"{r['tool']:<35} {r.get('rows') or '-':>6} "
                f"{r['response_chars']:>10,} {r['response_tokens']:>10,}"
            )
        else:
            print(f"{r['tool']:<35} FAILED: {r.get('error','?')[:50]}")
    return 0 if baseline["totals"]["tools_failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
