"""v4.4.1 — the encoded-query value boundary, asserted against what ServiceNow decodes.

Three layers, because the defect had three separate failure modes and a test that
only covers one of them passes while the query is still wrong:

1. **Characters** — every character from the 2026-08-05 measurement, pushed
   through the real producer encoder and the real transport encoder, asserting the
   value ServiceNow's parser ends up with. Never the URL string.
2. **Seams** — each place a caller-supplied value becomes part of a query, end to
   end through ``make_nws_request`` (stubbed at the OAuth boundary, so the
   encoding under test genuinely runs), for the character that actually broke.
3. **Refusal** — ``^`` is unrepresentable; every seam must refuse rather than
   answer, and must not send a request.

The failure signatures being pinned, from the measurement:

    'Cost^Center'  -> two conditions          (the '^' split)
    'A&B'          -> two URL parameters      (the '&' escape)
    'Deal 20%2C'   -> ServiceNow sees 'Deal 20,'   (the silent unquote)

All three ran BROADER than the caller asked for, which is why an assertion on
condition count and on parameter count belongs beside every value assertion.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from filter import QueryValueError, encode_query_value
from filter.value_encoding import QUERY_VALUE_SAFE
from http_layer.url_builder import QUERY_OPERATOR_SAFE, ensure_query_encoded
from tests.sn_query_probe import (
    assert_no_smuggled_parameter,
    servicenow_conditions,
    servicenow_params,
    servicenow_value_after,
)

TEXT_PREFIX = "short_descriptionLIKE"


# ---------------------------------------------------------------------------
# Layer 1 — characters
# ---------------------------------------------------------------------------

def _wire(value: str, prefix: str = TEXT_PREFIX) -> str:
    """Push *value* through both encoders and return what ServiceNow decodes.

    Composes the two halves in production order — the producer's
    ``encode_query_value``, then the transport's ``ensure_query_encoded`` — so a
    change to either half that breaks the round trip fails here. Running only one
    of them is how the defect survived: each looked correct alone.
    """
    url = (
        "https://x/api/now/table/incident"
        f"?sysparm_fields=number&sysparm_query={prefix}{encode_query_value(value)}"
        "&sysparm_limit=10"
    )
    encoded = ensure_query_encoded(url)
    assert_no_smuggled_parameter(encoded)
    assert len(servicenow_conditions(encoded)) == 1, servicenow_conditions(encoded)
    return servicenow_value_after(encoded, prefix)


# Every character from the measurement. Grouped only for readability — the
# assertion is identical for all of them: ServiceNow must receive the value it
# was given, and the query must stay one condition and one parameter.
FAITHFUL_VALUES = [
    # The structural character that was broken in transport (v4.4.0: truncated
    # the condition and appended a stray URL parameter).
    "Sales & Marketing",
    "A&B&C",
    # Previously fine, must stay fine: the rest of the operator safe-set. These
    # survive because ServiceNow splits conditions on '^' alone.
    "Cost=Center",
    "a<b",
    "a>b",
    "f(x)",
    "ratio:1",
    "user@host",
    "urgent!",
    # Escape-adjacent. v4.4.0 decoded these, so ServiceNow was searched for a
    # different string with nothing announcing it (`unquote` never raises).
    "Deal 20%2C off",
    "Reset %41dmin password",
    "Up 20%DB backups",
    "50% off",
    "100%",
    "%",
    "%%",
    # Ordinary text that has always needed escaping.
    "server down",
    "issue #123",
    "a+b",
    "what?",
    "a,b",
    "it's broken",
    "café naïve",
    "日本語のテキスト",
]


@pytest.mark.parametrize("value", FAITHFUL_VALUES, ids=repr)
def test_servicenow_receives_the_value_it_was_given(value):
    assert _wire(value) == value


@pytest.mark.parametrize("value", FAITHFUL_VALUES, ids=repr)
def test_encoding_a_value_is_idempotent_through_the_transport(value):
    """Re-encoding an already-encoded URL changes nothing.

    The property the old ``unquote()``-first implementation bought, kept without
    it. It matters because ``query_table_with_filters`` encodes the assembled
    query itself and ``make_nws_request`` encodes it again — two passes on the
    same string, and before v4.4.1 they were two different encoders.
    """
    once = ensure_query_encoded(
        f"https://x/api?sysparm_query={TEXT_PREFIX}{encode_query_value(value)}"
    )
    assert ensure_query_encoded(once) == once


def test_caret_is_refused_not_escaped():
    """No encoding can carry it: ServiceNow splits on the DECODED value."""
    with pytest.raises(QueryValueError) as excinfo:
        encode_query_value("Cost^Center")
    assert excinfo.value.code == "VALIDATION"
    assert "Cost^Center" in excinfo.value.message


def test_a_caret_would_have_produced_two_conditions():
    """The premise of the refusal, asserted rather than assumed.

    Percent-encode ``^`` end to end, by hand, as correctly as anyone could, and
    ServiceNow still receives two conditions. This is what makes ``^``
    unrepresentable rather than merely mis-transported, and it is the reason the
    refusal is not a missing feature.
    """
    hand_encoded = ensure_query_encoded(
        f"https://x/api?sysparm_query={TEXT_PREFIX}Cost%5ECenter"
    )
    assert servicenow_conditions(hand_encoded) == ["short_descriptionLIKECost", "Center"]


def test_a_non_string_value_passes_through_instead_of_raising():
    """An `int` arriving from the JSON boundary must still interpolate.

    MCP clients stringify inconsistently (see the param_coercion module), so a
    filter value can reach here as an int. `quote` would raise TypeError on it,
    turning a harmless filter into a crash.
    """
    assert encode_query_value(3) == 3
    assert encode_query_value(None) is None


def test_a_long_value_is_truncated_in_the_refusal_message():
    """The message echoes the value; a 5000-character description must not fill it."""
    long_value = "x" * 500 + "^"
    with pytest.raises(QueryValueError) as excinfo:
        encode_query_value(long_value)
    assert "..." in excinfo.value.message
    assert len(excinfo.value.message) < 500
    assert excinfo.value.value == long_value, "the full value stays on the exception"


def test_the_two_safe_sets_differ_only_by_the_caret():
    """The relationship the design rests on, pinned so a future edit must be deliberate.

    The value safe-set is the transport's minus ``^``. If they drift apart, either
    a value stops round-tripping (transport escapes something the producer left
    alone) or ``^`` becomes carryable again (it is not).
    """
    assert set(QUERY_OPERATOR_SAFE) - set(QUERY_VALUE_SAFE) == {"^"}


def test_a_bare_equals_in_a_filter_value_is_still_read_as_an_operator():
    """Known limitation, pinned rather than left unrecorded. Not an encoding bug.

    ``_has_operator_in_value`` treats any ``=`` in a value as caller-supplied
    operator syntax, so ``{"short_description": "Cost=Center"}`` builds
    ``short_descriptionCost=Center`` — a condition on a field that does not
    exist, which ServiceNow drops silently, widening the query. Escaping cannot
    fix it: the ambiguity is in deciding whether the caller meant an operator.
    The value round-trips fine once an operator is explicit
    (``LIKECost=Center``), which is what `FAITHFUL_VALUES` covers.
    """
    from Table_Tools.generic_table_tools import _build_query_condition

    assert _build_query_condition("short_description", "Cost=Center") == (
        "short_descriptionCost=Center"
    )


# ---------------------------------------------------------------------------
# Layer 2 — seams, end to end
# ---------------------------------------------------------------------------

async def _send(call):
    """Run *call* with the transport stubbed at the OAuth boundary.

    Patched at ``http_layer.request_dispatcher.make_oauth_request`` and NOT at
    each module's ``make_nws_request``: the transport half of the encoder lives
    inside ``make_nws_request``, so stubbing that would test every producer
    against an encoder that never ran — and pass.
    """
    urls: list[str] = []

    async def fake_oauth(url):
        urls.append(url)
        return {"result": []}

    with patch("http_layer.request_dispatcher.make_oauth_request", new=fake_oauth):
        result = await call()
    return urls, result


async def _query_via_generic(table, filters):
    """Route a filters dict through the live main assembly path.

    v5.0 "Boron" (Tier 2.5) deleted `query_table_with_generic_filters` (only the
    culled KB thin-wrappers reached it). Its `_build_query_string` value handlers
    are the same ones `query_table_with_filters` uses, so the seams below keep
    exercising them through the surviving function — the encoder contract is
    unchanged.
    """
    from Table_Tools.generic_table_tools import query_table_with_filters
    from filter import TableFilterParams

    return await query_table_with_filters(
        table, TableFilterParams(filters=filters, fields=["number"])
    )


async def _seam_filter_records(value):
    from Table_Tools.generic_table_tools import query_table_with_filters
    from filter import TableFilterParams

    return await _send(lambda: query_table_with_filters(
        "incident",
        TableFilterParams(filters={"short_description": f"LIKE{value}"}, fields=["number"]),
    ))


async def _seam_generic_filters(value):

    return await _send(lambda: _query_via_generic(
        "incident", {"short_description": f"LIKE{value}"}
    ))


async def _seam_exact_match(value):
    """A bare value, so `_build_query_condition` falls through to exact match.

    The default handler, and therefore the one most callers hit. It had no seam
    coverage in the first draft of this file: every other filter seam passes an
    explicit `LIKE`, which diverts to the operator handler instead. A mutation
    that dropped the escaping from exact match passed the whole suite.
    """

    return await _send(lambda: _query_via_generic(
        "incident", {"assigned_to": value}
    ))


async def _seam_suffix_operator(value):
    """`assigned_to_gte` -> `assigned_to>=`, a third terminal handler."""

    return await _send(lambda: _query_via_generic(
        "incident", {"assigned_to_gte": value}
    ))


async def _seam_priority_single(value):
    """`_format_single_priority`, reached only via P-notation with no comma.

    A distinct code path from the comma list, and it had only the source-scan
    guard behind it until this seam existed.
    """

    return await _send(lambda: _query_via_generic(
        "incident", {"priority": f"P{value}"}
    ))


async def _seam_date_range_operator(value):
    """`_handle_date_range_condition`'s `>=`/`<=` branch — its terminal branch.

    Its sibling branches are structural (a BETWEEN/javascript fragment), so this
    is the only part of that handler that escapes, and it shares its exact source
    line with the operator handler — which is how a mutation aimed at one of them
    silently hit the other.
    """

    return await _send(lambda: _query_via_generic(
        "incident", {"sys_created_on": f">={value}"}
    ))


async def _seam_priority_builder_single(value):
    """`_build_priority_filter`'s single-priority branch — a THIRD priority path.

    Distinct from `_parse_priority_list`'s two helpers, reached from
    `get_priority_incidents` whenever exactly one priority is asked for, which is
    the common case. Review caught that it was escaped and entirely unasserted:
    reverting it left 1108 passed.
    """
    from Table_Tools.generic_table_tools import get_records_by_priority

    return await _send(lambda: get_records_by_priority("incident", [value]))


async def _seam_priority_builder_multi(value):
    """`_build_priority_filter`'s OR-joined branch. Sibling of the above."""
    from Table_Tools.generic_table_tools import get_records_by_priority

    return await _send(lambda: get_records_by_priority("incident", ["1", value]))


async def _seam_cmdb_ip_address(value):
    from Table_Tools.cmdb_tools import search_cis_by_attributes

    return await _send(lambda: search_cis_by_attributes(ip_address=value))


async def _seam_cmdb_location(value):
    from Table_Tools.cmdb_tools import search_cis_by_attributes

    return await _send(lambda: search_cis_by_attributes(location=value))


async def _seam_cmdb_status(value):
    from Table_Tools.cmdb_tools import search_cis_by_attributes

    return await _send(lambda: search_cis_by_attributes(status=value))


async def _seam_priority_comma_list(value):
    """`_parse_priority_list` -> `_process_comma_separated_priorities`.

    Reached only by a comma in the value, which is why it is its own seam: the
    priority handler claims the filter before any generic handler sees it.
    """

    return await _send(lambda: _query_via_generic(
        "incident", {"priority": f"1,{value}"}
    ))


async def _seam_priority_additional_filters(value):
    from Table_Tools.generic_table_tools import get_records_by_priority

    return await _send(lambda: get_records_by_priority(
        "incident", ["1"], additional_filters={"assigned_to": value}
    ))


async def _seam_cmdb_attributes(value):
    from Table_Tools.cmdb_tools import search_cis_by_attributes

    return await _send(lambda: search_cis_by_attributes(name=value))


async def _seam_cmdb_quick_search(value):
    from Table_Tools.cmdb_tools import quick_ci_search

    return await _send(lambda: quick_ci_search(value))


async def _seam_kb_duplicate_check(value):
    from Table_Tools.kb_article_tools import _check_kb_duplicates

    return await _send(lambda: _check_kb_duplicates(value, "KB0001234"))


async def _seam_vtb_sys_id_lookup(value):
    from Table_Tools.vtb_task_tools import _get_task_sys_id

    return await _send(lambda: _get_task_sys_id(value))


# The write-target lookups. These resolve a record by `number=` and hand the
# sys_id to a PATCH, so an unescaped '^' could OR in a second condition and
# resolve a DIFFERENT record than the one named. Added after review: the first
# draft of this file covered only the VTB one, so reverting the escaping on the
# other four left the suite green while restoring exactly the defect the release
# claims to close.

async def _seam_kb_sys_id_lookup(value):
    from Table_Tools.kb_article_tools import _get_kb_article_sys_id

    return await _send(lambda: _get_kb_article_sys_id(value))


async def _seam_kb_meta_lookup(value):
    from Table_Tools.kb_article_tools import _get_kb_article_meta

    return await _send(lambda: _get_kb_article_meta(value))


async def _seam_kb_publish_verify(value):
    from Table_Tools.kb_article_tools import _verify_kb_published

    return await _send(lambda: _verify_kb_published(value))


async def _seam_cmdb_ci_probe(value):
    from Table_Tools.cmdb_tools import _probe_ci_table

    return await _send(lambda: _probe_ci_table("cmdb_ci_server", value))


# (seam, condition prefix ServiceNow should see). Derived from the code, not from
# a plan document: every module that pastes a caller value into a sysparm_query.
VALUE_SEAMS = [
    (_seam_filter_records, "short_descriptionLIKE"),
    (_seam_generic_filters, "short_descriptionLIKE"),
    (_seam_exact_match, "assigned_to="),
    (_seam_suffix_operator, "assigned_to>="),
    (_seam_priority_comma_list, "ORpriority="),
    (_seam_priority_single, "priority="),
    (_seam_date_range_operator, "sys_created_on>="),
    (_seam_priority_additional_filters, "assigned_to="),
    (_seam_priority_builder_single, "priority="),
    (_seam_priority_builder_multi, "ORpriority="),
    (_seam_cmdb_attributes, "nameLIKE"),
    (_seam_cmdb_ip_address, "ip_address="),
    (_seam_cmdb_location, "locationLIKE"),
    (_seam_cmdb_status, "operational_status="),
    (_seam_cmdb_quick_search, "nameLIKE"),
    (_seam_kb_duplicate_check, "short_descriptionLIKE"),
    (_seam_vtb_sys_id_lookup, "number="),
    (_seam_kb_sys_id_lookup, "number="),
    (_seam_kb_meta_lookup, "number="),
    (_seam_kb_publish_verify, "number="),
    (_seam_cmdb_ci_probe, "number="),
]

SEAM_IDS = [seam.__name__.removeprefix("_seam_") for seam, _ in VALUE_SEAMS]

# One value per failure mode, run through every seam. The exhaustive character
# sweep is layer 1; this layer proves each producer is wired into it.
SEAM_VALUES = ["Sales & Marketing", "Deal 20%2C off", "issue #123"]


@pytest.mark.parametrize("seam, prefix", VALUE_SEAMS, ids=SEAM_IDS)
@pytest.mark.parametrize("value", SEAM_VALUES, ids=repr)
@pytest.mark.asyncio
async def test_every_seam_carries_the_value_faithfully(seam, prefix, value):
    urls, _ = await seam(value)

    assert urls, "the seam sent no request, so nothing was asserted"
    sent = urls[0]
    assert_no_smuggled_parameter(sent)
    assert servicenow_value_after(sent, prefix) == value


@pytest.mark.parametrize("seam, prefix", VALUE_SEAMS, ids=SEAM_IDS)
@pytest.mark.asyncio
async def test_every_seam_refuses_a_caret_without_sending_a_request(seam, prefix):
    """A refusal that still sends the request would defeat the point.

    The KB duplicate check answers in its own fail-closed vocabulary
    (`KbDuplicateCheckInconclusive`) because for a publish "could not check" has
    to block, not just report. Everywhere else the refusal is a `QueryValueError`,
    surfaced as a VALIDATION error dict.
    """
    from Table_Tools.kb_article_tools import KbDuplicateCheckInconclusive

    try:
        urls, result = await seam("Cost^Center")
    except (QueryValueError, KbDuplicateCheckInconclusive):
        # Helper-level seams (not registered tools) propagate; their callers map it.
        return

    assert not urls, f"a request was sent with an unqueryable value: {urls!r}"
    assert isinstance(result, dict), result
    assert result.get("error", {}).get("code") == "VALIDATION", result


@pytest.mark.asyncio
async def test_a_caller_exclusion_list_escapes_each_sys_id():
    """The join is ours, the elements are values. Both have to be right.

    `exclude_caller` produces `caller_id!=a^caller_id!=b`: escaping the whole
    string would destroy the join, escaping nothing lets an element's '&' truncate
    the query. Not in the seam matrix because its condition shape is its own.
    """

    urls, _ = await _send(lambda: _query_via_generic(
        "incident", {"exclude_caller": "a&b,c&d"}
    ))
    sent = urls[0]
    assert_no_smuggled_parameter(sent)
    conditions = servicenow_conditions(sent)
    assert "caller_id!=a&b" in conditions
    assert "caller_id!=c&d" in conditions


@pytest.mark.asyncio
async def test_a_javascript_date_operand_is_sent_byte_for_byte():
    """The reason the value safe-set is not `safe=''`.

    ServiceNow evaluates `javascript:` operands server-side, and `( ) :` survive
    inside a value, so escaping them would be a gratuitous change to a working
    feature. Pinned because `safe=''` is the obvious thing to reach for.
    """

    urls, _ = await _send(lambda: _query_via_generic(
        "incident", {"sys_created_on": ">=javascript:gs.daysAgoStart(14)"}
    ))
    sent = urls[0]
    assert "sys_created_on>=javascript:gs.daysAgoStart(14)" in sent
    assert servicenow_value_after(sent, "sys_created_on>=") == (
        "javascript:gs.daysAgoStart(14)"
    )


@pytest.mark.asyncio
async def test_get_ci_details_maps_a_refusal_instead_of_re_raising_it():
    """`get_ci_details` gathers its probes with `return_exceptions=True`.

    Its loop re-raises anything that is not a classified read failure, so without
    an explicit arm a `QueryValueError` from the number would escape the tool as an
    exception rather than an error response. The arm has to precede the
    `BaseException` one, which is not something a coverage number would reveal.
    """
    from Table_Tools.cmdb_tools import get_ci_details

    urls, result = await _send(lambda: get_ci_details("Cost^Center"))
    assert not urls, f"a probe was sent with an unqueryable number: {urls!r}"
    assert isinstance(result, dict), result
    assert result["error"]["code"] == "VALIDATION"


def test_no_module_interpolates_a_record_number_unescaped():
    """Cross-module scan for the write-target class specifically.

    The handler scan below only reads `generic_table_tools`, so it says nothing
    about the `number=` lookups in the KB, CMDB and VTB modules — and those are the
    ones whose sys_id feeds a PATCH. Reverting the escaping on four of the five left
    the suite green until the seams above existed; this makes the *next* one a named
    failure rather than a silent regression.

    Scanned over the AST rather than over lines: a line-based version flagged three
    docstrings that merely *describe* `number={x}`, and missed that an escaped value
    can arrive through a local variable. Prose is not code and a variable is not a
    defect, so this reads f-strings and follows a one-hop assignment.
    """
    import ast
    from pathlib import Path

    def escaped_names(func: ast.AST) -> set[str]:
        """Locals assigned directly from `encode_query_value(...)` in this function."""
        names = set()
        for node in ast.walk(func):
            if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
                continue
            called = node.value.func
            if isinstance(called, ast.Name) and called.id == "encode_query_value":
                names.update(t.id for t in node.targets if isinstance(t, ast.Name))
        return names

    def is_escaped(expr: ast.AST, safe_locals: set[str]) -> bool:
        if isinstance(expr, ast.Call):
            return isinstance(expr.func, ast.Name) and expr.func.id == "encode_query_value"
        return isinstance(expr, ast.Name) and expr.id in safe_locals

    offenders = []
    for module in sorted((Path(__file__).resolve().parent.parent / "Table_Tools").glob("*.py")):
        tree = ast.parse(module.read_text(encoding="utf-8"))
        for func in ast.walk(tree):
            if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            safe_locals = escaped_names(func)
            for fstring in (n for n in ast.walk(func) if isinstance(n, ast.JoinedStr)):
                parts = fstring.values
                for literal, following in zip(parts, parts[1:]):
                    if not (isinstance(literal, ast.Constant) and isinstance(literal.value, str)):
                        continue
                    if not literal.value.endswith("number="):
                        continue
                    if not isinstance(following, ast.FormattedValue):
                        continue
                    if not is_escaped(following.value, safe_locals):
                        offenders.append(f"{module.name}:{func.name}:{fstring.lineno}")

    assert not offenders, (
        f"{offenders} paste a record number into a query without encode_query_value. "
        "These lookups pick the record a write then targets, so a '^' in the number "
        "can resolve a different record than the one named."
    )


def test_every_terminal_condition_handler_escapes_its_value():
    """Derived from the code, not from a list of handlers someone maintained.

    Same guard shape as `tests/test_http_layer_errors.py`'s read-path consumer
    scan, and for the same reason: a hand-kept list of the places that needed
    migrating was already wrong once in this project, by one module, and the
    missed one had no handling at all. Here the first draft missed three — the
    exact-match default and both priority helpers — and every existing test
    stayed green.

    Anything derived from a function's parameters and interpolated into an f-string
    is a caller value being pasted into a query, and must go through
    `encode_query_value`. STRUCTURAL exceptions are listed with why, so adding one
    is a decision rather than an omission.

    **Taint-propagating AST walk, not a regex over source.** The first version was
    a regex requiring a literal double-quoted f-string and a hardcoded whitelist of
    variable names — `f'{x}={y}'` in single quotes would have slipped past it, and
    `priorities[0]` demonstrably did, because a subscript is not a bare name. That
    miss was a real unescaped call site found in review. Taint starts at the
    parameters and follows assignments and comprehension targets, so it does not
    care what anything is named.

    Field names are exempt, because they are guarded by
    `_reject_unsafe_field_name`'s shape check rather than by escaping — but the
    exemption is *earned*, not granted by name: a name drops out of the taint set
    when the same function actually calls that validator on it. Delete the guard call
    and the interpolation is flagged again. The one exception is a parameter literally
    named `field`, which a handler receives already validated by
    `_build_query_condition`. `TestFieldNamesAreCallerSuppliedToo` holds up the
    validator itself.
    """
    import ast
    import inspect

    from Table_Tools import generic_table_tools as gtt

    STRUCTURAL = {
        # The value IS a query fragment; escaping it would destroy the operators it
        # is built from. Guarded by `_reject_unsafe_fragment` instead.
        "_handle_complete_query_condition",
        "_handle_servicenow_filter_condition",
        "_handle_bare_or_value_condition",
    }
    SYNTHESISED = {
        # Interpolate a value they built themselves rather than the caller's bytes,
        # so there is nothing to escape.
        #   date range: `f"{year}-{month:02d}-{day:02d}"` from regex-matched ints.
        #               Its one terminal branch (`>=`/`<=`) does escape.
        #   caller map: `known_callers[value_lower]` — the caller's text is a dict
        #               KEY into a hardcoded map; the interpolated result is one of
        #               our own sys_id constants.
        "_handle_date_range_condition",
        "_parse_caller_exclusions",
    }

    # The functions whose job is to turn a field and a value into a condition —
    # derived by following calls from the three query-assembly entry points, so a
    # new handler or a new helper under one is covered without editing this test.
    # Scoping matters: taint from parameters legitimately reaches table names, field
    # lists and message strings everywhere else in the module.
    def call_closure(seeds: set[str]) -> set[str]:
        seen, frontier = set(), set(seeds)
        while frontier:
            name = frontier.pop()
            if name in seen:
                continue
            seen.add(name)
            target = getattr(gtt, name, None)
            if not inspect.isfunction(target) or target.__module__ != gtt.__name__:
                continue
            tree = ast.parse(inspect.getsource(target).lstrip())
            frontier |= {
                node.func.id
                for node in ast.walk(tree)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            } - seen
        return seen

    CONDITION_BUILDERS = call_closure({
        "_build_query_condition",      # the main filter path
        "_build_additional_filters",   # the second assembly path
        "_build_priority_filter",      # the third priority path
    })

    def tainted_names(func: ast.AST) -> set[str]:
        """Parameter names plus everything that flows out of them."""
        args = func.args
        names = {
            a.arg
            for a in (*args.posonlyargs, *args.args, *args.kwonlyargs)
            if a.arg != "field"
        }
        # Fixed-point: an assignment can chain (value -> parsed -> parts[0]).
        for _ in range(len(list(ast.walk(func)))):
            grew = False
            for node in ast.walk(func):
                targets = []
                if isinstance(node, ast.Assign):
                    targets, source = node.targets, node.value
                elif isinstance(node, ast.comprehension):
                    targets, source = [node.target], node.iter
                elif isinstance(node, ast.For):
                    targets, source = [node.target], node.iter
                else:
                    continue
                if not (names & {n.id for n in ast.walk(source) if isinstance(n, ast.Name)}):
                    continue
                for target in targets:
                    for bound in ast.walk(target):
                        if isinstance(bound, ast.Name) and bound.id not in names:
                            names.add(bound.id)
                            grew = True
            if not grew:
                break
        # A name this function passes to the field-name validator is guarded by shape
        # instead of by escaping. Earned per call site: remove the call and the
        # interpolation below is flagged again.
        for node in ast.walk(func):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
                continue
            if node.func.id != "_reject_unsafe_field_name" or not node.args:
                continue
            if isinstance(node.args[0], ast.Name):
                names.discard(node.args[0].id)
        return names

    offenders = []
    for name in sorted(CONDITION_BUILDERS):
        obj = getattr(gtt, name, None)
        if name in STRUCTURAL or name in SYNTHESISED or not inspect.isfunction(obj):
            continue
        if obj.__module__ != gtt.__name__:
            continue
        func = ast.parse(inspect.getsource(obj).lstrip()).body[0]
        tainted = tainted_names(func)
        for interpolation in (n for n in ast.walk(func) if isinstance(n, ast.FormattedValue)):
            expr = interpolation.value
            if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) \
                    and expr.func.id == "encode_query_value":
                continue
            referenced = {n.id for n in ast.walk(expr) if isinstance(n, ast.Name)}
            if referenced & tainted:
                offenders.append(f"{name} (interpolates {sorted(referenced & tainted)})")

    assert not offenders, (
        f"{offenders} paste a caller value into a query without "
        "encode_query_value. Either escape it, or add the function to STRUCTURAL "
        "with a reason — a value that reaches ServiceNow unescaped widens the "
        "query instead of failing."
    )


class TestPreBuiltFragmentChannels:
    """The three filter keys that take a fragment instead of a value.

    `_date_range`, `_complete_caller_exclusion` and `_complete_query` hand a
    pre-built fragment through, complete with its own operators. They cannot be
    escaped — `build_date_filter` legitimately emits
    `sys_created_on>=A^sys_created_on<=B`, so `^` has to be allowed — which makes
    them the one place where a guard, not an encoder, is the only defence.

    Both were live holes found in review, verified by execution before fixing:
    `get_priority_incidents(additional_filters={"_date_range": "1^NQstate=99"})`
    and `filter_records({"_complete_caller_exclusion": "caller_id!=x^NQstate=99"})`
    each sent the reset to ServiceNow verbatim and returned rows, in a release
    whose stated purpose was refusing exactly that. The `^NQ` check sat *after* the
    fragment early-returns, and `_build_additional_filters` never reached it at all
    because it is a second, parallel assembly path.
    """

    @pytest.mark.asyncio
    async def test_date_range_refuses_a_new_query_reset(self):
        from Table_Tools.consolidated_tools import get_priority_incidents

        urls, result = await _send(lambda: get_priority_incidents(
            priorities=["1"], additional_filters={"_date_range": "1^NQstate=99^active=false"}
        ))
        assert not urls, f"the reset reached ServiceNow: {urls!r}"
        assert result["error"]["code"] == "VALIDATION"

    @pytest.mark.asyncio
    async def test_date_range_refuses_an_ampersand(self):
        """It cannot be escaped, and a raw '&' truncates the fragment silently."""
        from Table_Tools.consolidated_tools import get_priority_incidents

        urls, result = await _send(lambda: get_priority_incidents(
            priorities=["1"], additional_filters={"_date_range": "sys_created_on>=A&B"}
        ))
        assert not urls
        assert result["error"]["code"] == "VALIDATION"

    @pytest.mark.asyncio
    async def test_a_legitimate_date_range_still_carries_its_own_caret(self):
        """The guard must not be so broad it refuses the real thing.

        `build_date_filter(start, end)` joins two conditions with '^'. Refusing '^'
        in a fragment — the obvious over-correction — would break every dated query.
        """
        from Table_Tools.consolidated_tools import get_priority_incidents

        urls, _ = await _send(lambda: get_priority_incidents(
            priorities=["1"], start_date="2026-01-01", end_date="2026-01-31"
        ))
        assert urls, "the legitimate date range was refused"
        conditions = servicenow_conditions(urls[0])
        assert "sys_created_on>=2026-01-01 00:00:00" in conditions
        assert "sys_created_on<=2026-01-31 23:59:59" in conditions

    @pytest.mark.parametrize("payload", [
        "caller_id!=x^NQstate=99^active=false",
        "caller_id!=x&y",
    ], ids=["new_query_reset", "ampersand"])
    @pytest.mark.asyncio
    async def test_complete_caller_exclusion_is_guarded(self, payload):
        from Table_Tools.generic_tool_wrappers import filter_records

        urls, result = await _send(lambda: filter_records(
            "incident", {"_complete_caller_exclusion": payload}
        ))
        assert not urls, f"an unguarded fragment reached ServiceNow: {urls!r}"
        assert result["error"]["code"] == "VALIDATION"

    @pytest.mark.asyncio
    async def test_a_legitimate_caller_exclusion_still_works(self):
        from Table_Tools.generic_tool_wrappers import filter_records

        urls, _ = await _send(lambda: filter_records(
            "incident", {"_complete_caller_exclusion": "caller_id!=a^caller_id!=b"}
        ))
        assert urls, "the legitimate exclusion list was refused"
        conditions = servicenow_conditions(urls[0])
        assert "caller_id!=a" in conditions
        assert "caller_id!=b" in conditions

    def test_complete_query_is_guarded_when_the_flag_enables_it(self):
        """Gated off by default, so the guard behind the gate needs its own test."""
        from unittest.mock import patch as _patch

        from Table_Tools.generic_table_tools import _build_query_condition

        with _patch("Table_Tools.generic_table_tools.ENABLE_COMPLETE_QUERY", True):
            with pytest.raises(QueryValueError):
                _build_query_condition("_complete_query", "priority=1^NQstate=99")
            with pytest.raises(QueryValueError):
                _build_query_condition("_complete_query", "priority=1&state=2")


class TestStructuralPastesRefuseAnAmpersand:
    """The last `&` hole: structural handlers paste a caller fragment verbatim.

    A structural handler cannot escape its value — the value IS the query fragment,
    operators included — so `&` has to be refused there, exactly as it is for the
    three underscore fragment keys. Four such pastes: the bare-OR repair, a complete
    `^OR` filter, the `BETWEEN` early return, and `_parse_caller_exclusions`'
    already-`caller_id!=` passthrough.

    Found in the second review. It was invisible from `filter_records`, which routes
    through `query_table_with_filters` and so gets an `_encode_query_string` pass
    that escapes the `&` before the URL is built. `query_table_with_generic_filters`
    had no such pass, so the raw `&` met `ensure_query_encoded`'s first-`&` split:

        {"priority": "1^ORpriority=2&x"}
          -> ServiceNow got  priority=1^ORpriority=2   plus a stray `x` parameter

    The `query_table_with_generic_filters` second path was reached by the v4 KB
    thin-wrappers (`similar_knowledge_for_text`, `get_knowledge_by_category`),
    culled in v5.0 and removed with that path in the Tier 2.5 sweep. The
    registered-surface guard is now demonstrated through `filter_records`, whose
    caller values run the main assembly path's guards. Both assembly paths encode
    before interpolating, so a future structural paste that forgets truncates
    nothing — but the refusal is the fix, because turning a `&` inside
    caller-built *structure* into a literal is a guess.
    """

    STRUCTURAL_WITH_AMPERSAND = [
        ("bare_or_repair", {"priority": "1^ORpriority=2&x"}),
        ("complete_sn_filter", {"_f": "priority=1^ORpriority=2&x"}),
        ("between_early_return", {"sys_created_on": "BETWEENa&b@c"}),
        ("caller_id_passthrough", {"exclude_caller": "caller_id!=a&b"}),
    ]

    @pytest.mark.parametrize(
        "filters", [f for _, f in STRUCTURAL_WITH_AMPERSAND],
        ids=[name for name, _ in STRUCTURAL_WITH_AMPERSAND],
    )
    @pytest.mark.asyncio
    async def test_a_structural_paste_refuses_an_ampersand(self, filters):

        urls, result = await _send(lambda: _query_via_generic("incident", filters))
        assert not urls, f"a truncated query reached ServiceNow: {urls!r}"
        assert result["error"]["code"] == "VALIDATION"

    @pytest.mark.asyncio
    async def test_the_registered_kb_tool_refuses_it_too(self):
        """The reachable surface, not just the internal function.

        v5.0: filter_records is the registered entry point after the KB
        thin-wrappers were culled; a caller value carrying `^OR` is a structural
        paste on the main path and must be refused, not escaped.
        """
        from Table_Tools.generic_tool_wrappers import filter_records

        urls, result = await _send(
            lambda: filter_records("kb_knowledge", {"kb_category": "1^ORkb_category=2&evil"})
        )
        assert not urls
        assert result["error"]["code"] == "VALIDATION"

    @pytest.mark.parametrize("filters, expected", [
        ({"priority": "1^ORpriority=2"}, "priority=1^ORpriority=2"),
        ({"_f": "priority=1^ORpriority=2"}, "priority=1^ORpriority=2"),
        ({"exclude_caller": "caller_id!=abc"}, "caller_id!=abc"),
        (
            {"sys_created_on": "BETWEENjavascript:gs.beginningOfWeek()@javascript:gs.endOfWeek()"},
            "BETWEENjavascript:gs.beginningOfWeek()@javascript:gs.endOfWeek()",
        ),
    ], ids=["bare_or", "complete_filter", "caller_list", "between_javascript"])
    @pytest.mark.asyncio
    async def test_legitimate_structural_values_are_untouched(self, filters, expected):
        """The guard refuses `&` only. Everything these fragments are made of stays."""

        urls, _ = await _send(lambda: _query_via_generic("incident", filters))
        assert urls, "a legitimate structural fragment was refused"
        assert_no_smuggled_parameter(urls[0])
        conditions = servicenow_conditions(urls[0])
        for condition in expected.split("^"):
            assert condition in conditions, (conditions, expected)

    @pytest.mark.asyncio
    async def test_an_ampersand_in_an_ordinary_value_still_works(self):
        """The non-regression that matters: a real KB category contains '&'.

        "Payroll & Benefits" is a terminal value, so it is escaped, not refused —
        refusing it would make the guard worse than the bug.
        """
        from Table_Tools.generic_tool_wrappers import filter_records

        urls, _ = await _send(
            lambda: filter_records("kb_knowledge", {"kb_category": "Payroll & Benefits"})
        )
        assert urls, "an ordinary category containing '&' was refused"
        assert_no_smuggled_parameter(urls[0])
        assert servicenow_value_after(urls[0], "kb_category=") == "Payroll & Benefits"


@pytest.mark.parametrize("filters", [
    {"priority": "1"},
    {"short_description": "LIKESales & Marketing"},
    {"assigned_to": "Deal 20%2C off"},
    {"priority": "1^ORpriority=2"},
], ids=["plain", "ampersand", "percent_escape", "structural_or"])
@pytest.mark.asyncio
async def test_all_three_assembly_paths_build_the_same_query(filters):
    """The same filters must produce the same query however they are assembled.

    Historically three paths reached ServiceNow — `query_table_with_filters`,
    `query_table_with_generic_filters` and `get_records_by_priority` — and only
    the first encoded its assembled query, which is what hid the structural `&`
    truncation. v5.0 "Boron" (Tier 2.5) deleted `query_table_with_generic_filters`
    (the `_query_via_generic` shim now routes through `query_table_with_filters`),
    so two live paths remain; asserting they agree pins that both still encode
    before interpolating.
    """
    from Table_Tools.generic_table_tools import (
        get_records_by_priority,
        query_table_with_filters,
    )
    from filter import TableFilterParams

    fields = ["number"]
    typed_urls, _ = await _send(lambda: query_table_with_filters(
        "incident", TableFilterParams(filters=filters, fields=fields)
    ))
    generic_urls, _ = await _send(lambda: _query_via_generic("incident", filters))
    priority_urls, _ = await _send(lambda: get_records_by_priority(
        "incident", ["1"], additional_filters={"assigned_to": "x"}
    ))

    assert typed_urls
    assert generic_urls
    assert priority_urls
    assert servicenow_params(typed_urls[0])["sysparm_query"] == \
        servicenow_params(generic_urls[0])["sysparm_query"]
    # The priority path takes its filters differently, so agreement is asserted on
    # the property that matters rather than on the whole string.
    for url in (typed_urls[0], generic_urls[0], priority_urls[0]):
        assert_no_smuggled_parameter(url)


class TestFieldNamesAreCallerSuppliedToo:
    """A filters dict's KEYS come from the caller and nothing validated them.

    `{"x^NQstate=99": "1"}` built `x^NQstate=99=1` — the same unscoped-table-read
    injection the value guard refuses, arriving through the key instead. Found while
    auditing the two fragment holes: the guards all read `value` and none read
    `field`.
    """

    @pytest.mark.parametrize("field", [
        "x^NQstate=99",
        "a&b",
        "a^b",
        "a=b",
        "a b",
        "",
        "1field",
    ])
    @pytest.mark.asyncio
    async def test_a_field_name_carrying_query_syntax_is_refused(self, field):
        from Table_Tools.generic_tool_wrappers import filter_records

        urls, result = await _send(lambda: filter_records("incident", {field: "1"}))
        assert not urls, f"field name {field!r} reached ServiceNow: {urls!r}"
        assert result["error"]["code"] == "VALIDATION"

    @pytest.mark.parametrize("field", [
        "priority",
        "assigned_to",
        "task.priority",
        "sys_created_on",
        "assigned_to_gte",
    ])
    @pytest.mark.asyncio
    async def test_ordinary_and_dot_walked_field_names_are_accepted(self, field):
        """Dot-walking is how `task_sla` is queried at all — it must survive."""
        from Table_Tools.generic_tool_wrappers import filter_records

        urls, result = await _send(lambda: filter_records("incident", {field: "1"}))
        assert urls, f"field name {field!r} was refused: {result!r}"

    @pytest.mark.asyncio
    async def test_additional_filters_validates_its_keys_too(self):
        """The second assembly path has to repeat the check, not inherit it."""
        from Table_Tools.generic_table_tools import get_records_by_priority

        urls, result = await _send(lambda: get_records_by_priority(
            "incident", ["1"], additional_filters={"x^NQstate=99": "1"}
        ))
        assert not urls
        assert result["error"]["code"] == "VALIDATION"


# ---------------------------------------------------------------------------
# Layer 3 — the incidental protection nobody designed
# ---------------------------------------------------------------------------

class TestTextSearchTokenizerImmunity:
    """`query_table_by_text` is safe by accident, so the accident is pinned.

    `utils.extract_keywords` tokenizes on `\\b[a-zA-Z]{4,}\\b`, so a keyword
    cannot contain `^`, `&` or `%` no matter what the caller typed. That is real
    protection and it is the reason the text-search path never needed a fix — but
    nobody chose it, and widening the character class would remove it silently
    while every existing test stayed green.
    """

    @pytest.mark.parametrize("text", [
        "Cost^Center outage",
        "Sales & Marketing incident",
        "Deal 20%2C discount problem",
        "server down issue #123",
    ])
    def test_no_keyword_can_carry_a_structural_character(self, text):
        from utils import extract_keywords

        for keyword in extract_keywords(text):
            assert not set(keyword) & set("^&%"), keyword

    def test_the_tokenizer_pattern_is_still_letters_only(self):
        """Pins the mechanism, not just today's outputs.

        A test that only checks sample strings passes if the class is widened to
        `[a-zA-Z0-9^&%]` and no sample happens to hit it. Equality on the pattern
        makes a widening deliberate and points at what it costs.
        """
        import utils

        assert utils._CONTENT_KEYWORD_PATTERN.pattern == r"\b[a-zA-Z]{4,}\b", (
            "extract_keywords no longer tokenizes on letters only — the text "
            "search is no longer immune to structural characters by construction, "
            "so `query_table_by_text` now depends on encode_query_value for real "
            "rather than as a no-op. Verify the seam tests cover it."
        )

    @pytest.mark.parametrize("text", FAITHFUL_VALUES + ["INC0012345 and Cost^Center"], ids=repr)
    def test_every_token_the_tokenizer_emits_is_alphanumeric(self, text):
        """Covers the record-number branch too, which has its own patterns.

        `extract_keywords` returns record numbers (`inc\\d+`, `kb\\d+`, ...) ahead
        of content keywords, so pinning only the content pattern would leave half
        the function unpinned.
        """
        from utils import extract_keywords

        for keyword in extract_keywords(text):
            assert keyword.isalnum(), keyword

    @pytest.mark.asyncio
    async def test_text_search_sends_one_condition_per_keyword_and_no_stray_params(self):
        from Table_Tools.generic_table_tools import query_table_by_text
        from utils import extract_keywords

        text = "Sales & Marketing outage report"
        expected_keywords = extract_keywords(text)
        assert expected_keywords, "premise of the test"

        urls, _ = await _send(lambda: query_table_by_text("incident", text))
        sent = urls[0]
        assert_no_smuggled_parameter(sent)

        # One LIKE condition per keyword — the '&' contributes no token at all —
        # plus the injected ORDERBY, which is one more condition.
        conditions = servicenow_conditions(sent)
        like_conditions = [c for c in conditions if "short_descriptionLIKE" in c]
        assert len(like_conditions) == len(expected_keywords)
        assert all("&" not in c for c in like_conditions)
        assert any("ORDERBYDESC" in c for c in conditions)


# ---------------------------------------------------------------------------
# The ^NQ reset — refused now, not silently dropped
# ---------------------------------------------------------------------------

class TestNewQueryResetRefusal:
    """`^NQ` discards every condition before it, so a scoped query becomes a table read."""

    def test_a_new_query_reset_is_refused(self):
        from Table_Tools.generic_table_tools import _build_query_condition

        with pytest.raises(QueryValueError) as excinfo:
            _build_query_condition("short_description", "fooLIKEbar^NQactive=true")
        assert "NQ" in excinfo.value.message

    def test_it_is_refused_even_when_a_structural_handler_would_claim_it(self):
        """Why the check runs before the handlers rather than inside the encoder.

        `1^ORpriority=2^NQactive=true` is claimed by the bare-OR repair handler as
        a caller-built fragment and passed straight through, so it would never
        reach a value encoder. The reset has to be caught first.
        """
        from Table_Tools.generic_table_tools import _build_query_condition

        with pytest.raises(QueryValueError):
            _build_query_condition("priority", "1^ORpriority=2^NQactive=true")

    @pytest.mark.asyncio
    async def test_the_tool_reports_it_instead_of_querying(self):

        urls, result = await _send(lambda: _query_via_generic(
            "incident", {"short_description": "fooLIKEbar^NQactive=true"}
        ))
        assert not urls, "a query ran despite an unqueryable filter value"
        assert result["error"]["code"] == "VALIDATION"
