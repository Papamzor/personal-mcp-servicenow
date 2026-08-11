"""Surface-wide response-contract test (v5.0 "Boron", plan §3.1).

Every registered tool in `tools.tools` must return one of the §3.1 shapes:

    list success   {"result": [...], "returned_count": int, "truncated": bool}
    single record  {"record": {...} | None}
    write success  {"record": {...}, "message": str}
    failure        {"error": {"code": <ERROR_CODES>, "message": str}}
    partial page   list shape + {"partial": true, "error": {...}}   (data + error)

Forbidden: a bare `str` return; a `{"message": ...}` success dialect parallel to
`error`; `result`/`record` sitting next to `error` (outside the partial-page and
diagnostic exceptions); `code` values outside the seven-code vocabulary.

The tools are driven through the REAL dispatcher (`http_layer.request_dispatcher`)
so this exercises the shapes the modules actually build, not a mock of them. Two
transports: one that makes every round-trip succeed, one that makes every
round-trip fail with a classified timeout.

Documented intentional exceptions (see `_EXCEPTION_TOOLS`):
  * `health_check` returns a diagnostic STATUS BAG — `error` may sit beside
    `connection`/`server`/`auth`. It is not a data tool.
  * `publish_knowledge_article` can return a fail-closed guard outcome
    (duplicates / inconclusive / unconfirmed) carrying `success: False` and, in
    the unconfirmed case, `error` beside status flags. Covered explicitly below.
  * the partial-page shape carries rows AND `error` together by design.

`test_every_registered_tool_has_a_contract_case` derives the tool set from
`tools.tools` at run time ([[derive_lists_from_code]]) — adding a tool without a
contract case fails the suite by name, so this cannot silently under-cover.
"""
from __future__ import annotations

import inspect
from unittest.mock import AsyncMock, MagicMock

import pytest

import tools
from Table_Tools.response import ERROR_CODES

# A row rich enough to satisfy every reader: generic (number/short_description),
# CMDB (name/sys_class_name/location/operational_status), KB dedup/meta (sys_id).
_ROW = {
    "sys_id": "26bc0f3b47c1120010c43d3171e36d99",
    "number": "REC0001234",
    "short_description": "sample record",
    "name": "host-01",
    "sys_class_name": "cmdb_ci_server",
    "location": "Brussels",
    "operational_status": "1",
    "workflow_state": "Published",
    "state": "3",
}

# Tools that touch ServiceNow via the dispatcher (so the failure pass applies).
# get_query_syntax_help is pure reference data — it never calls the transport.
_NO_TRANSPORT = {"get_query_syntax_help"}

# Batch tools run each article independently and record a per-row failure inside
# the row; the batch itself still succeeds, so a transport failure yields a valid
# list_response with error-bearing rows, NOT a top-level error.
_BATCH_TOOLS = {"publish_knowledge_articles", "check_kb_duplicates"}


async def _invoke(factory):
    """Call a case factory, awaiting only if it produced a coroutine.

    get_query_syntax_help is a plain sync function; every other tool is async."""
    resp = factory()
    if inspect.isawaitable(resp):
        resp = await resp
    return resp

# Tools whose success/failure shape legitimately carries companions to `error`
# or is a non-data payload (see module docstring).
_EXCEPTION_TOOLS = {"health_check", "publish_knowledge_article"}


def _success_read(url: str):
    """A GET that succeeds for every caller. Dedup queries come back clear so a
    publish is allowed to proceed to its verify step."""
    if "short_descriptionLIKE" in url:
        return {"result": []}  # KB dedup: no duplicates -> clear to publish
    if "sys_db_object" in url:
        return {"result": [{"name": "cmdb_ci_server", "label": "Server", "number_ref": "x"}]}
    return {"result": [dict(_ROW)]}


def _fail_read(url: str):
    raise TimeoutError("transport down")


class _FakeOAuthClient:
    """Write branch: make_authenticated_request returns a single-record body."""

    def __init__(self, *, fail: bool = False):
        self._fail = fail

    async def make_authenticated_request(self, method, url, **kwargs):
        if self._fail:
            import httpx

            response = MagicMock()
            response.status_code = 500
            raise httpx.HTTPStatusError("boom", request=MagicMock(), response=response)
        return {"result": dict(_ROW)}


@pytest.fixture
def transport(monkeypatch):
    """Patch the dispatcher's read + write seams. `mode` picks success/failure."""
    import http_layer.request_dispatcher as dispatcher
    import Table_Tools.kb_article_tools as kb

    def install(mode: str):
        read = _success_read if mode == "success" else _fail_read

        async def _read(url):
            return read(url)

        monkeypatch.setattr(dispatcher, "make_oauth_request", _read)
        monkeypatch.setattr(
            dispatcher, "get_oauth_client", lambda: _FakeOAuthClient(fail=(mode != "success"))
        )
        # publish polls with asyncio.sleep between fire and verify — skip the wait.
        monkeypatch.setattr(kb.asyncio, "sleep", AsyncMock())

    return install


# Each case: name, a zero-arg coroutine factory, and the success kind.
# kind ∈ {"list", "record", "diagnostic", "reference"}.
def _cases():
    from Table_Tools.generic_tool_wrappers import (
        search_records, get_record, find_similar, filter_records,
    )
    from Table_Tools.consolidated_tools import (
        get_priority_incidents, get_kb_articles_by_state,
        get_sla_details, query_slas_by_task, query_slas_by_status, query_slas_custom,
    )
    from Table_Tools.vtb_task_tools import create_private_task, update_private_task
    from Table_Tools.kb_article_tools import (
        update_knowledge_article, publish_knowledge_article, publish_knowledge_articles,
        retire_knowledge_article, check_kb_duplicates,
    )
    from Table_Tools.cmdb_tools import (
        find_cis_by_type, search_cis_by_attributes, get_ci_details,
        similar_cis_for_ci, get_all_ci_types, quick_ci_search,
    )
    from utility_tools import health_check
    from Table_Tools.intelligent_query_tools import get_query_syntax_help

    return [
        ("health_check", lambda: health_check(), "diagnostic"),
        ("search_records", lambda: search_records("incident", "server down"), "list"),
        ("get_record", lambda: get_record("incident", "INC0012345"), "record_read"),
        ("find_similar", lambda: find_similar("incident", "INC0012345"), "list"),
        ("filter_records", lambda: filter_records("incident", {"priority": "1"}), "list"),
        ("get_priority_incidents", lambda: get_priority_incidents(["1"]), "list"),
        ("get_kb_articles_by_state", lambda: get_kb_articles_by_state(), "list"),
        ("create_private_task", lambda: create_private_task({"short_description": "x"}), "record_write"),
        ("update_private_task", lambda: update_private_task("VTB0001234", {"comments": "x"}), "record_write"),
        ("update_knowledge_article", lambda: update_knowledge_article("KB0001234", {"short_description": "x"}), "record_write"),
        ("publish_knowledge_article", lambda: publish_knowledge_article("KB0001234"), "record_write"),
        ("publish_knowledge_articles", lambda: publish_knowledge_articles(["KB0001234"]), "list"),
        ("retire_knowledge_article", lambda: retire_knowledge_article("KB0001234"), "record_write"),
        ("check_kb_duplicates", lambda: check_kb_duplicates(["KB0001234"]), "list"),
        ("get_sla_details", lambda: get_sla_details(_ROW["sys_id"]), "list"),
        ("query_slas_by_task", lambda: query_slas_by_task("INC0012345"), "list"),
        ("query_slas_by_status", lambda: query_slas_by_status("active"), "list"),
        ("query_slas_custom", lambda: query_slas_custom({"active": "true"}), "list"),
        ("find_cis_by_type", lambda: find_cis_by_type("cmdb_ci_server"), "list"),
        ("search_cis_by_attributes", lambda: search_cis_by_attributes(name="host-01"), "list"),
        ("get_ci_details", lambda: get_ci_details("CI0001000"), "record"),
        ("similar_cis_for_ci", lambda: similar_cis_for_ci("CI0001000"), "list"),
        ("get_all_ci_types", lambda: get_all_ci_types(), "list"),
        ("quick_ci_search", lambda: quick_ci_search("host-01"), "list"),
        ("get_query_syntax_help", lambda: get_query_syntax_help(), "reference"),
    ]


CASES = _cases()


def _assert_error_shape(err):
    assert isinstance(err, dict), f"error must be a dict, got {type(err)}"
    assert set(err) >= {"code", "message"}, f"error must carry code+message, got {err}"
    assert err["code"] in ERROR_CODES, f"code {err['code']!r} outside the vocabulary"
    assert isinstance(err["message"], str) and err["message"]


def assert_contract(resp, *, tool_name):
    """The §3.1 invariants. `error` present with companions is allowed only for
    the documented exception tools and the partial-page shape."""
    assert isinstance(resp, dict), f"{tool_name} returned a non-dict {type(resp)} — bare returns are forbidden"

    if "error" in resp:
        _assert_error_shape(resp["error"])
        is_partial = resp.get("partial") is True
        if not is_partial and tool_name not in _EXCEPTION_TOOLS:
            assert "result" not in resp and "record" not in resp, (
                f"{tool_name}: error must not sit beside result/record (got keys {sorted(resp)})"
            )

    if "result" in resp:
        assert isinstance(resp["result"], list), f"{tool_name}: result must be a list"
        assert isinstance(resp.get("returned_count"), int), f"{tool_name}: list needs int returned_count"
        assert isinstance(resp.get("truncated"), bool), f"{tool_name}: list needs bool truncated"
        # A list success must NOT carry a top-level prose `message` — that is the
        # {"result": [...], "message": "Found N records"} dialect this tier removed.
        # `message` is legal only beside `record` (write success) or on a
        # documented exception tool.
        if tool_name not in _EXCEPTION_TOOLS:
            assert "message" not in resp, (
                f"{tool_name}: list success must not carry a prose `message` "
                f"(reintroduced success dialect): {sorted(resp)}"
            )

    if "record" in resp:
        rec = resp["record"]
        assert rec is None or isinstance(rec, dict), f"{tool_name}: record must be dict|None"

    # The forbidden success dialect: a top-level `message` with neither error,
    # record, nor result to anchor it (that is the killed {"message": ...} shape).
    if "message" in resp and not ({"error", "record", "result"} & set(resp)):
        pytest.fail(f"{tool_name}: bare top-level message dialect {resp}")


@pytest.mark.asyncio
@pytest.mark.parametrize("name,factory,kind", CASES, ids=[c[0] for c in CASES])
async def test_success_shape_conforms(name, factory, kind, transport):
    transport("success")
    resp = await _invoke(factory)
    assert_contract(resp, tool_name=name)

    if kind == "list":
        assert "result" in resp and isinstance(resp["result"], list)
    elif kind == "record_read":
        # Read hit: {"record": {...}} with NO top-level message (reads never
        # carry the write-success message).
        assert "record" in resp, f"{name} should return a single-record shape, got {sorted(resp)}"
        assert "message" not in resp, f"{name}: a read must not carry a top-level message"
    elif kind == "record_write":
        # Write success: {"record": {...}, "message": str}. The §3.1 write shape
        # REQUIRES the message, so dropping success_message= now fails here.
        assert "record" in resp and resp["record"] is not None, f"{name}: write should return a record"
        assert isinstance(resp.get("message"), str) and resp["message"], (
            f"{name}: write success must carry a non-empty `message` (§3.1 write shape)"
        )
    elif kind == "diagnostic":
        assert "connection" in resp  # health_check status bag
    elif kind == "reference":
        assert isinstance(resp, dict) and "error" not in resp


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name,factory,kind",
    [c for c in CASES if c[0] not in _NO_TRANSPORT],
    ids=[c[0] for c in CASES if c[0] not in _NO_TRANSPORT],
)
async def test_failure_shape_conforms(name, factory, kind, transport):
    """Every transport-touching tool maps a classified failure to the contract."""
    transport("failure")
    resp = await _invoke(factory)
    assert_contract(resp, tool_name=name)

    if name == "health_check":
        # Documented exception: diagnostic status bag reports the failure under
        # `error` alongside connection="failed".
        assert resp["connection"] == "failed"
        _assert_error_shape(resp["error"])
    elif name in _BATCH_TOOLS:
        # A batch stays a valid list; the per-article failure lands inside its row.
        assert isinstance(resp["result"], list) and resp["result"]
    else:
        assert "error" in resp, f"{name} should surface a failure as {{'error': ...}}, got {sorted(resp)}"
        _assert_error_shape(resp["error"])


def test_every_registered_tool_has_a_contract_case():
    """Derive the tool set from tools.tools, never from a hand-list.

    A new registered tool with no contract case fails here by name, so this
    cannot silently under-cover the surface ([[derive_lists_from_code]]).
    """
    registered = {fn.__name__ for fn in tools.tools}
    covered = {c[0] for c in CASES}
    missing = registered - covered
    extra = covered - registered
    assert not missing, f"registered tools with no contract case: {sorted(missing)}"
    assert not extra, f"contract cases for tools that are not registered: {sorted(extra)}"


class TestDocumentedExceptions:
    """The shapes that intentionally deviate — pinned so the deviation stays deliberate."""

    @pytest.mark.asyncio
    async def test_publish_unconfirmed_carries_error_beside_status_flags(self, transport):
        """publish_knowledge_article: verify-read failure => unconfirmed, an
        intentional exception where `error` coexists with success flags."""
        import Table_Tools.kb_article_tools as kb
        transport("success")

        async def meta(number, workflow_state=None):
            return {"sys_id": _ROW["sys_id"], "short_description": "x"}

        async def clear(short_description, exclude_number):
            return []

        from http_layer.errors import ErrorCode, ServiceNowRequestError

        async def verify_fails(article_number):
            raise ServiceNowRequestError(ErrorCode.TIMEOUT, "verify timed out", retryable=True)

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(kb, "_get_kb_article_meta", meta)
            mp.setattr(kb, "_check_kb_duplicates", clear)
            mp.setattr(kb, "_verify_kb_published", verify_fails)
            mp.setattr(kb, "_fire_publish", AsyncMock(return_value=None))
            resp = await kb.publish_knowledge_article("KB0001234")

        assert resp["publish_confirmed"] is False
        _assert_error_shape(resp["error"])

    @pytest.mark.asyncio
    async def test_partial_page_carries_rows_and_error(self):
        """The one sanctioned data+error shape."""
        from Table_Tools.generic_table_tools import _partial_envelope, PartialPageReadError
        from Table_Tools.response import list_response
        from http_layer.errors import ErrorCode, ServiceNowRequestError

        partial = PartialPageReadError(
            [dict(_ROW)], ServiceNowRequestError(ErrorCode.TIMEOUT, "page 2 died", retryable=True)
        )
        resp = _partial_envelope(list_response([dict(_ROW)], truncated=False), partial)
        assert_contract(resp, tool_name="filter_records")
        assert resp["partial"] is True
        assert resp["result"] and "error" in resp
