"""Diagnostic MCP tool.

Read-failure contract (v4.4 Tier 0.3): a failed GET raises
`ServiceNowRequestError` instead of returning None, so this module — which
probes ServiceNow through `make_nws_request` — is a read-path consumer and
carries an `except ServiceNowRequestError` arm (enforced by
tests/test_http_layer_errors.py::test_every_read_path_consumer_handles_the_raise).

v5.0 "Boron" (Tier 2): `health_check` is the single diagnostic tool. It absorbs
the five v4 diagnostics — `nowtest` (process liveness), `now_test_oauth` /
`nowtestauth` (live ServiceNow probe, identical endpoint), `now_auth_info`
(auth config), and `nowtest_auth_input` (table schema peek, now `probe_table`).
"""
from typing import Any, Dict, Optional

from http_layer import (
    ServiceNowRequestError,
    NWS_API_BASE,
    get_auth_info,
    make_nws_request,
)
from constants import TABLE_CONFIGS


async def health_check(probe_table: Optional[str] = None) -> Dict[str, Any]:
    """Check this server, its ServiceNow auth config, and the live connection.

    WHEN TO USE: confirm the server is up and ServiceNow is reachable — "is the
        ServiceNow connection up", "test ServiceNow authentication". Pass
        probe_table to also list one supported table's field names.
    WHEN NOT TO USE: querying records (filter_records / search_records);
        building or explaining a filter (get_query_syntax_help).
    PREFER OVER: nothing — this is the single diagnostic entry point. It
        replaces the former nowtest / now_test_oauth / now_auth_info /
        nowtestauth / nowtest_auth_input tools.
    TABLES: probe_table accepts any supported table; omit it for a plain
        connectivity check.
    SIDE EFFECT: read-only — one lightweight authenticated GET against
        ServiceNow (sys_user, or probe_table when given). The auth-config
        fields contact nothing.
    EXAMPLE: is the ServiceNow connection up.

    Returns a status dict: `server` liveness, `auth` config, and `connection`
    ("ok"/"failed"). A failed probe reports the classified failure under
    `error` ({"code", "message"}) rather than blaming auth for a timeout. With
    probe_table set, a successful probe adds `sample_fields` and `has_records`.
    """
    status: Dict[str, Any] = {
        "server": "running",
        "auth": get_auth_info(),
    }

    if probe_table is not None and probe_table not in TABLE_CONFIGS:
        status["connection"] = "skipped"
        status["error"] = {
            "code": "VALIDATION",
            "message": f"Invalid table '{probe_table}'. Not in the supported allowlist.",
        }
        return status

    table = probe_table or "sys_user"
    url = f"{NWS_API_BASE}/api/now/table/{table}?sysparm_limit=1"
    if probe_table is None:
        url += "&sysparm_fields=sys_id,name"
    try:
        data = await make_nws_request(url)
    except ServiceNowRequestError as error:
        # A diagnostic that says "auth failed" for a timeout sends the reader
        # after the wrong problem. classify_read_failure distinguishes them.
        status["connection"] = "failed"
        status.update(error.to_error_dict())
        return status

    status["connection"] = "ok"
    result = (data or {}).get("result", [])
    if probe_table is not None:
        sample = result[0] if result else {}
        status["table"] = probe_table
        status["sample_fields"] = list(sample.keys())[:10]
        status["total_fields"] = len(sample)
        status["has_records"] = bool(result)
    return status
