"""Capture read-path token baseline across all supported tables.

Sprint 3 relocates `_add_default_params`, `_ensure_query_encoded`, and
`_extract_display_values` into the new `http_layer/` package. A subtle
mistake there — dropping a perf param on a specific table, or breaking
the display-value flattening — would inflate every LLM-visible response.
The Sprint 2 baseline only covered `task_sla`. This script extends the
coverage to the seven other tables via `search_records` and
`filter_records`, plus the three remaining consolidated read tools.

Records both the outgoing URL (so URL-shape regressions are catchable)
and the response token count (so payload-shape regressions are catchable).

Run:
    python scripts/capture_read_path_baseline.py

Output:
    v4.0/read_path_baseline.json
"""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable
from unittest.mock import patch

import tiktoken

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from Table_Tools.consolidated_tools import (  # noqa: E402
    get_active_knowledge_articles,
    get_priority_incidents,
    similar_knowledge_for_text,
)
from Table_Tools.generic_tool_wrappers import (  # noqa: E402
    filter_records,
    search_records,
)

ENCODER = tiktoken.get_encoding("cl100k_base")
OUTPUT_PATH = REPO_ROOT / "v4.0" / "read_path_baseline.json"

# Seven tables that participate in the read path.
# `task_sla` excluded — covered by scripts/capture_sla_token_baseline.py.
TABLES = [
    "incident",
    "change_request",
    "sc_req_item",
    "sc_task",
    "universal_request",
    "kb_knowledge",
    "vtb_task",
]


def count_tokens(payload: Any) -> int:
    return len(ENCODER.encode(json.dumps(payload, default=str)))


async def measure(
    tool_name: str,
    args_repr: str,
    call: Callable[[], Awaitable[Any]],
) -> dict[str, Any]:
    """Run `call`, capture outgoing URL and response payload."""
    captured_urls: list[str] = []

    # Lazy import — service_now_api_oauth uses module-level make_oauth_request.
    import service_now_api_oauth as svc

    original = svc.make_oauth_request

    async def recording_oauth_request(url: str) -> Any:
        captured_urls.append(url)
        return await original(url)

    try:
        with patch.object(svc, "make_oauth_request", new=recording_oauth_request):
            response = await call()
    except Exception as exc:  # noqa: BLE001
        return {
            "tool": tool_name,
            "args": args_repr,
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }

    rows = (
        len(response["result"])
        if isinstance(response, dict) and isinstance(response.get("result"), list)
        else None
    )

    # Probe URLs for the v3 read-path invariants. Sprint 3 must preserve all.
    sample_url = captured_urls[0] if captured_urls else ""
    return {
        "tool": tool_name,
        "args": args_repr,
        "ok": True,
        "rows": rows,
        "response_chars": len(json.dumps(response, default=str)),
        "response_tokens": count_tokens(response),
        "outgoing_urls": captured_urls,
        "url_invariants": {
            "has_exclude_reference_link": "sysparm_exclude_reference_link=true" in sample_url,
            "has_no_count": "sysparm_no_count=true" in sample_url,
            "has_display_value": "sysparm_display_value=true" in sample_url,
            "has_orderby_sort": "ORDERBYDESCsys_created_on" in sample_url
            or "ORDERBYsys_created_on" in sample_url,
        },
    }


async def main() -> int:
    records: list[dict[str, Any]] = []

    # search_records and filter_records across all tables
    for table in TABLES:
        records.append(
            await measure(
                "search_records",
                f'table={table!r}, input_text="test"',
                lambda t=table: search_records(t, "test"),
            )
        )
        records.append(
            await measure(
                "filter_records",
                f'table={table!r}, filters={{}}, fields=None',
                lambda t=table: filter_records(t, {}, None),
            )
        )

    # Consolidated read tools (not table-parametric)
    records.append(
        await measure(
            "get_priority_incidents",
            'priorities=["1","2"]',
            lambda: get_priority_incidents(["1", "2"]),
        )
    )
    records.append(
        await measure(
            "similar_knowledge_for_text",
            'input_text="error"',
            lambda: similar_knowledge_for_text("error"),
        )
    )
    records.append(
        await measure(
            "get_active_knowledge_articles",
            'input_text="error"',
            lambda: get_active_knowledge_articles("error"),
        )
    )

    baseline = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "encoder": "cl100k_base",
        "tools": records,
        "totals": {
            "tools_measured": sum(1 for r in records if r.get("ok")),
            "tools_failed": sum(1 for r in records if not r.get("ok")),
            "total_response_tokens": sum(r.get("response_tokens") or 0 for r in records),
            "total_response_chars": sum(r.get("response_chars") or 0 for r in records),
            "invariant_violations": sum(
                1 for r in records
                if r.get("ok") and not all(r.get("url_invariants", {}).values())
            ),
        },
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(baseline, indent=2), encoding="utf-8")

    print(f"Baseline written to {OUTPUT_PATH}")
    print(
        f"  Tools measured: {baseline['totals']['tools_measured']}/"
        f"{baseline['totals']['tools_measured'] + baseline['totals']['tools_failed']}"
    )
    print(f"  Total tokens: {baseline['totals']['total_response_tokens']:,}")
    print(f"  Total chars:  {baseline['totals']['total_response_chars']:,}")
    print(f"  URL invariant violations: {baseline['totals']['invariant_violations']}")
    print()
    print(f"{'Tool':<32} {'Table':<22} {'Rows':>6} {'Tokens':>10}  Invariants")
    print("-" * 95)
    for r in records:
        if not r.get("ok"):
            print(f"{r['tool']:<32} FAILED: {r.get('error','?')[:60]}")
            continue
        # Pull the table out of args if present
        args = r.get("args", "")
        table = "-"
        if "table=" in args:
            table = args.split("table=")[1].split(",")[0].strip("'\" ")
        inv = r.get("url_invariants", {})
        status = "OK" if all(inv.values()) else "MISSING: " + ",".join(
            k for k, v in inv.items() if not v
        )
        print(
            f"{r['tool']:<32} {table:<22} {r.get('rows') or '-':>6} "
            f"{r['response_tokens']:>10,}  {status}"
        )

    return 0 if baseline["totals"]["tools_failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
