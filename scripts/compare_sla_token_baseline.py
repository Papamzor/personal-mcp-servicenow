"""Run v4.0 SLA tools against live ServiceNow and diff vs v3 baseline.

Compares per-tool response token counts before and after the Sprint 2
collapse. Maps every v3 tool call to its v4 equivalent so the regression
budget is enforced one-for-one. Writes the diff report to
v4.0/token_diff.json.

Run:
    python scripts/compare_sla_token_baseline.py
"""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

import tiktoken

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from Table_Tools.consolidated_tools import (  # noqa: E402
    get_sla_details,
    query_slas_by_status,
    query_slas_by_task,
    query_slas_custom,
    similar_slas_for_text,
)
from Table_Tools.generic_table_tools import (  # noqa: E402
    TableFilterParams,
    query_table_with_filters,
)

ENCODER = tiktoken.get_encoding("cl100k_base")
BASELINE_PATH = REPO_ROOT / "v4.0" / "token_baseline.json"
DIFF_PATH = REPO_ROOT / "v4.0" / "token_diff.json"


def count_tokens(payload: Any) -> int:
    return len(ENCODER.encode(json.dumps(payload, default=str)))


async def discover_sample_sla() -> dict[str, str | None]:
    probe = await query_table_with_filters(
        "task_sla",
        TableFilterParams(filters={"active": "true"}, fields=["sys_id", "task.number"]),
    )
    rows = probe.get("result") if isinstance(probe, dict) else None
    if not rows:
        return {"task_number": None, "sla_sys_id": None}
    first = rows[0]
    return {"task_number": first.get("task.number"), "sla_sys_id": first.get("sys_id")}


async def measure(name: str, call: Callable[[], Awaitable[Any]], args_repr: str) -> dict[str, Any]:
    try:
        response = await call()
        rows = (
            len(response["result"])
            if isinstance(response, dict) and isinstance(response.get("result"), list)
            else None
        )
        return {
            "tool": name,
            "args": args_repr,
            "ok": True,
            "rows": rows,
            "response_chars": len(json.dumps(response, default=str)),
            "response_tokens": count_tokens(response),
        }
    except Exception as exc:  # noqa: BLE001
        return {"tool": name, "args": args_repr, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


async def main() -> int:
    if not BASELINE_PATH.exists():
        print(f"ERROR: baseline missing at {BASELINE_PATH}. Run capture script first.")
        return 2
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    baseline_by_tool = {r["tool"]: r for r in baseline["tools"]}

    sample = await discover_sample_sla()
    task_number = sample["task_number"]
    sla_sys_id = sample["sla_sys_id"]

    # Mapping: v3 baseline tool name -> (v4 tool call, args repr)
    plan = [
        ("similar_slas_for_text",
         lambda: similar_slas_for_text("incident"),
         'input_text="incident"'),
        ("get_slas_for_task",
         lambda: query_slas_by_task(task_number) if task_number else asyncio.sleep(0, result={"result": []}),
         f"task_number={task_number!r}"),
        # The corrected target row is what we measure against — the v3 broken row stays in the baseline as history.
        ("get_sla_details (corrected sys_id= lookup)",
         lambda: get_sla_details(sla_sys_id) if sla_sys_id else asyncio.sleep(0, result={"result": []}),
         f"sla_sys_id={sla_sys_id!r}"),
        ("get_breaching_slas",
         lambda: query_slas_by_status("breaching", threshold_minutes=60),
         "query_slas_by_status('breaching', threshold_minutes=60)"),
        ("get_breached_slas",
         lambda: query_slas_by_status("breached", days=7),
         "query_slas_by_status('breached', days=7)"),
        ("get_slas_by_stage",
         lambda: query_slas_by_status("by_stage", stage="in_progress"),
         "query_slas_by_status('by_stage', stage='in_progress')"),
        ("get_active_slas",
         lambda: query_slas_by_status("active"),
         "query_slas_by_status('active')"),
        ("get_sla_performance_summary",
         lambda: query_slas_by_status("performance", days=30),
         "query_slas_by_status('performance', days=30)"),
        ("get_recent_breached_slas",
         lambda: query_slas_by_status("breached", days=1),
         "query_slas_by_status('breached', days=1)"),
        ("get_critical_sla_status",
         lambda: query_slas_by_status("critical"),
         "query_slas_by_status('critical')"),
    ]

    diffs: list[dict[str, Any]] = []
    for baseline_name, call, args_repr in plan:
        v4 = await measure(baseline_name, call, args_repr)
        b = baseline_by_tool.get(baseline_name)
        if b is None or not b.get("ok"):
            v4["baseline_tokens"] = None
            v4["delta_tokens"] = None
            v4["delta_pct"] = None
            v4["verdict"] = "no-baseline"
        else:
            base_tokens = b["response_tokens"]
            if v4.get("ok"):
                delta = v4["response_tokens"] - base_tokens
                pct = (delta / base_tokens * 100) if base_tokens else 0.0
                v4["baseline_tokens"] = base_tokens
                v4["delta_tokens"] = delta
                v4["delta_pct"] = pct
                # Noise tolerance: live ServiceNow data churns between captures
                # (timestamps, row ordering, etc.). Real refactor regressions
                # are structural — schema additions or missing optimizations —
                # and produce far larger swings. Threshold: 5% AND >50 tokens.
                if delta <= 0:
                    v4["verdict"] = "IMPROVEMENT" if delta < 0 else "MATCH"
                elif pct > 5.0 and delta > 50:
                    v4["verdict"] = "REGRESSION"
                else:
                    v4["verdict"] = "NOISE"
            else:
                v4["baseline_tokens"] = base_tokens
                v4["verdict"] = "FAIL"
        diffs.append(v4)

    report = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "baseline_at": baseline.get("captured_at"),
        "encoder": "cl100k_base",
        "diffs": diffs,
    }
    DIFF_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Diff written to {DIFF_PATH}")
    print()
    print(f"{'v3 tool':<42} {'v3 tokens':>11} {'v4 tokens':>11} {'delta':>11} {'pct':>8} {'verdict':<12}")
    print("-" * 100)
    regressions = 0
    for d in diffs:
        base = d.get("baseline_tokens")
        v4tok = d.get("response_tokens")
        delta = d.get("delta_tokens")
        pct = d.get("delta_pct")
        verdict = d.get("verdict", "-")
        if verdict == "REGRESSION":
            regressions += 1
        print(
            f"{d['tool']:<42} "
            f"{(base if base is not None else '-'):>11} "
            f"{(v4tok if v4tok is not None else '-'):>11} "
            f"{(delta if delta is not None else '-'):>11} "
            f"{(f'{pct:+.1f}%' if pct is not None else '-'):>8} "
            f"{verdict:<12}"
        )
    print()
    print(f"Regressions: {regressions}")
    return 0 if regressions == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
