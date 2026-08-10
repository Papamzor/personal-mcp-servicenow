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


async def _seam_filter_records(value):
    from Table_Tools.generic_table_tools import query_table_with_filters
    from filter import TableFilterParams

    return await _send(lambda: query_table_with_filters(
        "incident",
        TableFilterParams(filters={"short_description": f"LIKE{value}"}, fields=["number"]),
    ))


async def _seam_generic_filters(value):
    from Table_Tools.generic_table_tools import query_table_with_generic_filters

    return await _send(lambda: query_table_with_generic_filters(
        "incident", {"short_description": f"LIKE{value}"}
    ))


async def _seam_exact_match(value):
    """A bare value, so `_build_query_condition` falls through to exact match.

    The default handler, and therefore the one most callers hit. It had no seam
    coverage in the first draft of this file: every other filter seam passes an
    explicit `LIKE`, which diverts to the operator handler instead. A mutation
    that dropped the escaping from exact match passed the whole suite.
    """
    from Table_Tools.generic_table_tools import query_table_with_generic_filters

    return await _send(lambda: query_table_with_generic_filters(
        "incident", {"assigned_to": value}
    ))


async def _seam_suffix_operator(value):
    """`assigned_to_gte` -> `assigned_to>=`, a third terminal handler."""
    from Table_Tools.generic_table_tools import query_table_with_generic_filters

    return await _send(lambda: query_table_with_generic_filters(
        "incident", {"assigned_to_gte": value}
    ))


async def _seam_priority_single(value):
    """`_format_single_priority`, reached only via P-notation with no comma.

    A distinct code path from the comma list, and it had only the source-scan
    guard behind it until this seam existed.
    """
    from Table_Tools.generic_table_tools import query_table_with_generic_filters

    return await _send(lambda: query_table_with_generic_filters(
        "incident", {"priority": f"P{value}"}
    ))


async def _seam_date_range_operator(value):
    """`_handle_date_range_condition`'s `>=`/`<=` branch — its terminal branch.

    Its sibling branches are structural (a BETWEEN/javascript fragment), so this
    is the only part of that handler that escapes, and it shares its exact source
    line with the operator handler — which is how a mutation aimed at one of them
    silently hit the other.
    """
    from Table_Tools.generic_table_tools import query_table_with_generic_filters

    return await _send(lambda: query_table_with_generic_filters(
        "incident", {"sys_created_on": f">={value}"}
    ))


async def _seam_priority_comma_list(value):
    """`_parse_priority_list` -> `_process_comma_separated_priorities`.

    Reached only by a comma in the value, which is why it is its own seam: the
    priority handler claims the filter before any generic handler sees it.
    """
    from Table_Tools.generic_table_tools import query_table_with_generic_filters

    return await _send(lambda: query_table_with_generic_filters(
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
    (_seam_cmdb_attributes, "nameLIKE"),
    (_seam_cmdb_quick_search, "nameLIKE"),
    (_seam_kb_duplicate_check, "short_descriptionLIKE"),
    (_seam_vtb_sys_id_lookup, "number="),
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
    from Table_Tools.generic_table_tools import query_table_with_generic_filters

    urls, _ = await _send(lambda: query_table_with_generic_filters(
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
    from Table_Tools.generic_table_tools import query_table_with_generic_filters

    urls, _ = await _send(lambda: query_table_with_generic_filters(
        "incident", {"sys_created_on": ">=javascript:gs.daysAgoStart(14)"}
    ))
    sent = urls[0]
    assert "sys_created_on>=javascript:gs.daysAgoStart(14)" in sent
    assert servicenow_value_after(sent, "sys_created_on>=") == (
        "javascript:gs.daysAgoStart(14)"
    )


def test_every_terminal_condition_handler_escapes_its_value():
    """Derived from the code, not from a list of handlers someone maintained.

    Same guard shape as `tests/test_http_layer_errors.py`'s read-path consumer
    scan, and for the same reason: a hand-kept list of the places that needed
    migrating was already wrong once in this project, by one module, and the
    missed one had no handling at all. Here the first draft missed three — the
    exact-match default and both priority helpers — and every existing test
    stayed green.

    A function that interpolates a bare `{value}`-family name into an f-string is
    pasting a caller value into a query and must escape it. STRUCTURAL exceptions
    are listed with why, so adding one is a decision rather than an omission.
    """
    import inspect
    import re

    from Table_Tools import generic_table_tools as gtt

    # Names that hold a caller-supplied value at the point of interpolation.
    VALUE_NAMES = ("value", "p", "priority_num", "caller_id", "keyword")
    STRUCTURAL = {
        # value IS a query fragment; escaping it would destroy the operators
        # it is built from.
        "_handle_complete_query_condition",
        "_handle_servicenow_filter_condition",
        "_handle_bare_or_value_condition",
    }
    pattern = re.compile(
        r"f\"[^\"\n]*\{(?:" + "|".join(VALUE_NAMES) + r")\}[^\"\n]*\""
    )

    offenders = []
    for name, obj in vars(gtt).items():
        if name in STRUCTURAL or not inspect.isfunction(obj):
            continue
        if obj.__module__ != gtt.__name__:
            continue
        if pattern.search(inspect.getsource(obj)):
            offenders.append(name)

    assert not offenders, (
        f"{offenders} paste a caller value into a query without "
        "encode_query_value. Either escape it, or add the function to STRUCTURAL "
        "with a reason — a value that reaches ServiceNow unescaped widens the "
        "query instead of failing."
    )


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
        from Table_Tools.generic_table_tools import query_table_with_generic_filters

        urls, result = await _send(lambda: query_table_with_generic_filters(
            "incident", {"short_description": "fooLIKEbar^NQactive=true"}
        ))
        assert not urls, "a query ran despite an unqueryable filter value"
        assert result["error"]["code"] == "VALIDATION"
