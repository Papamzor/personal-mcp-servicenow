"""Golden intent set — tool-selection baseline (v4.4 Tier 0.1).

Measures whether the *registered tool surface* is discriminating enough for a
client to pick the right tool from an intent. Scoring uses name + parameter
names + docstring, concatenated, because that is what an MCP client actually
sends to the model — a docstring-only score would flatter tools whose names
carry the signal (and vice versa).

The router here is deliberately dumb (weighted token overlap, no LLM, no
synonym table). It is a *regression fence*, not a claim about real model
behavior: it catches a rename or docstring edit that makes the surface less
discriminating. Per plan decision 5, an LLM pass gates the Tier 1 and Tier 2
exits; this static baseline is not sufficient on its own, because Tier 1 would
otherwise just optimize against a bag-of-words scorer.

Both rates are recorded as floors below. Raising them is the point of Tier 1;
lowering them requires editing this file, which is the intended speed bump.
"""
import inspect
import re

import pytest

import tools

# Weight per match site. A hit in the tool *name* is the strongest signal a
# client has, a parameter name is next, prose is weakest.
_WEIGHT_NAME = 3
_WEIGHT_PARAM = 2
_WEIGHT_DOC = 1

# Ambiguity band: tools scoring at least this fraction of the top score count
# as plausible alternative paths for an intent.
_AMBIGUITY_BAND = 0.8

_STOPWORDS = frozenset("""
a an the and or of for to in on at by with from is are was were be been am
me my mine i you your we our it its this that these those all any some
show give get list find tell please can could would should do does did
what which who whom whose when where why how much many
""".split())


def _stem(token: str) -> str:
    """Strip a single trailing plural 's' so 'slas'/'sla' and 'incidents'/'incident' unify."""
    return token[:-1] if len(token) > 3 and token.endswith('s') else token


def _tokens(text: str) -> frozenset:
    """Lowercase alphanumeric tokens, snake_case split, stopwords dropped, plural-stemmed."""
    out = set()
    for raw in re.findall(r'[A-Za-z0-9_]+', text.lower()):
        for part in raw.split('_'):
            if len(part) < 2 or part in _STOPWORDS:
                continue
            out.add(_stem(part))
    return frozenset(out)


def _tool_profile(fn) -> tuple:
    """(name_tokens, param_tokens, doc_tokens) for one registered tool."""
    params = ' '.join(inspect.signature(fn).parameters)
    return (
        _tokens(fn.__name__),
        _tokens(params),
        _tokens(inspect.getdoc(fn) or ''),
    )


def _score(intent_tokens: frozenset, profile: tuple) -> int:
    """Weighted overlap. Each intent token scores once, at its strongest match site."""
    name_toks, param_toks, doc_toks = profile
    total = 0
    for token in intent_tokens:
        if token in name_toks:
            total += _WEIGHT_NAME
        elif token in param_toks:
            total += _WEIGHT_PARAM
        elif token in doc_toks:
            total += _WEIGHT_DOC
    return total


def _profiles() -> dict:
    return {fn.__name__: _tool_profile(fn) for fn in tools.tools}


def _rank(intent: str, profiles: dict) -> list:
    """Tools ranked by score, descending. Ties break on name so results are deterministic."""
    intent_tokens = _tokens(intent)
    scored = [(name, _score(intent_tokens, prof)) for name, prof in profiles.items()]
    return sorted(scored, key=lambda pair: (-pair[1], pair[0]))


def _plausible_paths(ranked: list) -> list:
    """Names scoring within the ambiguity band of the top score."""
    top = ranked[0][1]
    if top <= 0:
        return [name for name, _ in ranked]
    return [name for name, score in ranked if score >= top * _AMBIGUITY_BAND]


# ---------------------------------------------------------------------------
# The golden set: 30 intents phrased the way a user actually asks.
#
# `preferred` — the tool the surface *should* steer to.
# `acceptable` — a wrong pick that still returns correct data (plan decision 3).
#   A tool is NOT acceptable if picking it yields wrong data or silent
#   truncation; those collisions are what Tier 2 is allowed to cull.
# ---------------------------------------------------------------------------
GOLDEN_INTENTS = (
    # --- incidents / generic table reads -----------------------------------
    {
        'intent': 'show me all P1 incidents from last week',
        'preferred': 'get_priority_incidents',
        'acceptable': {'filter_records', 'intelligent_search'},
        'note': 'seeded collision — 4 plausible paths at baseline',
    },
    {
        'intent': 'find incidents about a server crashing during backup',
        'preferred': 'search_records',
        'acceptable': {'intelligent_search', 'filter_records'},
    },
    {
        'intent': 'what is the short description of INC0012345',
        'preferred': 'get_record_summary',
        'acceptable': {'get_record'},
    },
    {
        'intent': 'give me the full details of incident INC0012345',
        'preferred': 'get_record',
        'acceptable': {'get_record_summary'},
    },
    {
        'intent': 'find other incidents similar to INC0012345',
        'preferred': 'find_similar',
        'acceptable': {'search_records'},
    },
    {
        'intent': 'list change requests where state is 3 and category is network',
        'preferred': 'filter_records',
        'acceptable': {'intelligent_search'},
    },
    # --- knowledge reads ---------------------------------------------------
    {
        'intent': 'knowledge articles about password reset',
        'preferred': 'similar_knowledge_for_text',
        'acceptable': {'search_records', 'get_knowledge_by_category', 'intelligent_search'},
        'note': 'seeded collision — 3 plausible paths at baseline',
    },
    {
        'intent': 'all knowledge articles in the Workplace category',
        'preferred': 'get_knowledge_by_category',
        'acceptable': {'similar_knowledge_for_text', 'filter_records'},
    },
    {
        'intent': 'which knowledge articles are currently in published state',
        'preferred': 'get_kb_articles_by_state',
        'acceptable': {'get_active_knowledge_articles', 'filter_records'},
    },
    # --- knowledge writes --------------------------------------------------
    {
        'intent': 'update the body text of KB0001234',
        'preferred': 'update_knowledge_article',
        'acceptable': set(),
    },
    {
        'intent': 'publish knowledge article KB0001234',
        'preferred': 'publish_knowledge_article',
        'acceptable': {'publish_knowledge_articles'},
    },
    {
        'intent': 'publish KB0001234, KB0001235 and KB0001236 in one go',
        'preferred': 'publish_knowledge_articles',
        'acceptable': {'publish_knowledge_article'},
    },
    {
        'intent': 'retire knowledge article KB0004321',
        'preferred': 'retire_knowledge_article',
        'acceptable': set(),
    },
    {
        'intent': 'check whether KB0001234 has duplicates before I publish it',
        'preferred': 'check_kb_duplicates',
        'acceptable': set(),
    },
    # --- private task CRUD -------------------------------------------------
    {
        'intent': 'create a private task to review the firewall configuration',
        'preferred': 'create_private_task',
        'acceptable': set(),
    },
    {
        'intent': 'set my private task VTB0001234 to closed complete',
        'preferred': 'update_private_task',
        'acceptable': set(),
    },
    # --- SLA ---------------------------------------------------------------
    {
        'intent': 'which SLAs are breached',
        'preferred': 'query_slas_by_status',
        'acceptable': {'query_slas_custom', 'filter_records'},
        'note': 'seeded collision — 3 plausible paths at baseline',
    },
    {
        'intent': 'all SLA records attached to INC0012345',
        'preferred': 'query_slas_by_task',
        'acceptable': {'query_slas_custom', 'filter_records'},
    },
    {
        'intent': 'SLAs whose task description mentions an email outage',
        'preferred': 'similar_slas_for_text',
        'acceptable': {'query_slas_custom'},
    },
    {
        'intent': 'SLA query with a filter shape the presets do not cover',
        'preferred': 'query_slas_custom',
        'acceptable': {'filter_records'},
    },
    # --- CMDB --------------------------------------------------------------
    {
        'intent': 'list every Linux server configuration item',
        'preferred': 'find_cis_by_type',
        'acceptable': {'search_cis_by_attributes', 'quick_ci_search'},
    },
    {
        'intent': 'configuration items at location Brussels with status installed',
        'preferred': 'search_cis_by_attributes',
        'acceptable': {'find_cis_by_type'},
    },
    {
        'intent': 'full details for configuration item SRV0001234',
        'preferred': 'get_ci_details',
        'acceptable': {'quick_ci_search'},
    },
    {
        'intent': 'which CI classes exist in this CMDB',
        'preferred': 'get_all_ci_types',
        'acceptable': set(),
    },
    # --- health / auth -----------------------------------------------------
    {
        'intent': 'is the ServiceNow connection up',
        'preferred': 'now_test_oauth',
        'acceptable': {'nowtest', 'nowtestauth', 'now_auth_info'},
        'note': 'seeded collision — 5 plausible paths at baseline',
    },
    # --- natural language / help surface -----------------------------------
    {
        'intent': 'search for unresolved P2 tickets from May using plain English',
        'preferred': 'intelligent_search',
        'acceptable': {'search_records', 'filter_records', 'get_priority_incidents'},
    },
    {
        'intent': 'what does the filter priority=1 and state=2 actually do',
        'preferred': 'explain_servicenow_filters',
        'acceptable': {'get_query_syntax_help'},
    },
    {
        'intent': 'turn "open P1 incidents" into a ServiceNow filter without running it',
        'preferred': 'build_smart_servicenow_filter',
        'acceptable': {'explain_servicenow_filters'},
    },
    {
        'intent': 'which encoded query operators does ServiceNow support',
        'preferred': 'get_query_syntax_help',
        'acceptable': {'get_query_examples', 'get_servicenow_filter_templates'},
    },
    {
        'intent': 'give me a ready made filter template for open incidents',
        'preferred': 'get_servicenow_filter_templates',
        'acceptable': {'get_query_examples'},
    },
)

# Tools with no golden intent. Kept explicit so adding or renaming a tool
# forces a decision here rather than silently escaping measurement.
UNCOVERED_TOOLS = frozenset({
    'get_active_knowledge_articles',   # appears as `acceptable` only
    'get_sla_details',                 # sys_id lookup — no natural-language ambiguity
    'similar_cis_for_ci',
    'quick_ci_search',                 # appears as `acceptable` only
    'nowtest',                         # appears as `acceptable` only
    'now_auth_info',                   # appears as `acceptable` only
    'nowtestauth',                     # appears as `acceptable` only
    'nowtest_auth_input',
    'get_query_examples',              # appears as `acceptable` only
})

# ---------------------------------------------------------------------------
# Recorded floors. Floors, not targets: a tier raises them, nothing may lower
# them silently. Measured by test_report_baseline below
# (`pytest tests/test_tool_selection.py -s`).
#
# v4.4.0 (39 tools, pre-Tier-1 docstrings): preferred 21/30, acceptable 22/30,
# plausible paths 66. The four worst offenders then — full-details-of-incident
# -> get_sla_details, connection-up -> build_smart_servicenow_filter,
# all-SLA-attached -> get_record_summary, password-reset ->
# get_active_knowledge_articles.
#
# v4.5.0 (Tier 1 docstring protocol): raised to preferred 29/30, acceptable
# 29/30, plausible paths 50. The single remaining preferred miss is
# 'is the ServiceNow connection up' -> build_smart_servicenow_filter: a
# name-bound collision ('servicenow' in the rival's name wins the alphabetical
# tie no docstring can break), deferred to Tier 2's diagnostic/filter cull. The
# static router is a floor only — the Tier 1 exit gate is the LLM pass (§3.2).
# ---------------------------------------------------------------------------
BASELINE_PREFERRED_HITS = 29
BASELINE_ACCEPTABLE_HITS = 29
BASELINE_TOTAL_PLAUSIBLE_PATHS = 50


def _evaluate() -> dict:
    """Run the whole golden set once and return per-intent + aggregate results."""
    profiles = _profiles()
    rows = []
    for case in GOLDEN_INTENTS:
        ranked = _rank(case['intent'], profiles)
        top = ranked[0][0]
        allowed = {case['preferred']} | case['acceptable']
        rows.append({
            'intent': case['intent'],
            'preferred': case['preferred'],
            'top': top,
            'preferred_hit': top == case['preferred'],
            'acceptable_hit': top in allowed,
            'plausible': _plausible_paths(ranked),
        })
    return {
        'rows': rows,
        'preferred_hits': sum(1 for r in rows if r['preferred_hit']),
        'acceptable_hits': sum(1 for r in rows if r['acceptable_hit']),
        'plausible_paths': sum(len(r['plausible']) for r in rows),
    }


@pytest.fixture(scope='module')
def evaluation() -> dict:
    return _evaluate()


class TestGoldenSetIntegrity:
    """The set is worthless if it drifts out of sync with the registry."""

    def test_thirty_intents(self):
        assert len(GOLDEN_INTENTS) == 30

    def test_intents_are_unique(self):
        intents = [case['intent'] for case in GOLDEN_INTENTS]
        assert len(set(intents)) == len(intents)

    def test_every_referenced_tool_is_registered(self):
        registered = {fn.__name__ for fn in tools.tools}
        referenced = set()
        for case in GOLDEN_INTENTS:
            referenced.add(case['preferred'])
            referenced |= case['acceptable']
        unknown = referenced - registered
        assert not unknown, f"golden set references unregistered tools: {sorted(unknown)}"

    def test_preferred_never_also_acceptable(self):
        for case in GOLDEN_INTENTS:
            assert case['preferred'] not in case['acceptable'], case['intent']

    def test_uncovered_tools_are_declared(self):
        """Adding or renaming a tool must be a deliberate decision here."""
        registered = {fn.__name__ for fn in tools.tools}
        preferred = {case['preferred'] for case in GOLDEN_INTENTS}
        assert registered - preferred == UNCOVERED_TOOLS


class TestSelectionBaseline:
    """Ratchet: the surface may get more discriminating, never less."""

    def test_preferred_rate_holds(self, evaluation):
        misses = [
            f"{r['intent']!r} -> {r['top']} (wanted {r['preferred']})"
            for r in evaluation['rows'] if not r['preferred_hit']
        ]
        assert evaluation['preferred_hits'] >= BASELINE_PREFERRED_HITS, (
            f"preferred-hit rate regressed to {evaluation['preferred_hits']}/30; "
            f"misses:\n  " + "\n  ".join(misses)
        )

    def test_acceptable_rate_holds(self, evaluation):
        misses = [
            f"{r['intent']!r} -> {r['top']}"
            for r in evaluation['rows'] if not r['acceptable_hit']
        ]
        assert evaluation['acceptable_hits'] >= BASELINE_ACCEPTABLE_HITS, (
            f"acceptable-hit rate regressed to {evaluation['acceptable_hits']}/30; "
            f"top pick returned wrong data for:\n  " + "\n  ".join(misses)
        )

    def test_ambiguity_does_not_grow(self, evaluation):
        """Total plausible paths across the set — the overlap metric of plan decision 3."""
        assert evaluation['plausible_paths'] <= BASELINE_TOTAL_PLAUSIBLE_PATHS, (
            f"ambiguity grew to {evaluation['plausible_paths']} plausible paths "
            f"(baseline {BASELINE_TOTAL_PLAUSIBLE_PATHS})"
        )

    def test_report_baseline(self, evaluation):
        """Not an assertion — prints the per-intent table. Run with -s to read it."""
        print(
            f"\ntool-selection baseline: "
            f"preferred {evaluation['preferred_hits']}/30, "
            f"acceptable {evaluation['acceptable_hits']}/30, "
            f"plausible paths {evaluation['plausible_paths']}"
        )
        for row in evaluation['rows']:
            mark = 'OK ' if row['preferred_hit'] else ('alt' if row['acceptable_hit'] else 'X  ')
            print(f"  {mark} [{len(row['plausible'])}] {row['top']:<32} {row['intent']}")


class TestSeededCollisions:
    """The four collisions that motivated the plan.

    The plan's §4 counts (4 / 3 / 3 / 5) were derived by hand from reading the
    tool surface. The static router measures (3 / 6 / 1 / 3) instead. Both
    numbers are kept: the hand count is the human judgement of how many tools a
    user could reasonably land on, the router count is what bag-of-words
    scoring sees inside the 80% ambiguity band. They diverge because the router
    over-weights a token appearing in a tool *name* — which is exactly why
    decision 5 puts an LLM pass, not this router, on the Tier 1 and Tier 2
    exits. The assertions ratchet the router number.

    Tier 1 (4.5.0) re-derivation — password-reset moved 5 -> 6. The docstring
    protocol lifted `similar_knowledge_for_text` to the top of that intent (a
    preferred-hit gain — it lost to `get_active_knowledge_articles` before), so
    the 80%-band threshold rose to 5.6 and now admits the whole cluster of KB
    tools scoring 6. Those six are name-bound: `knowledge`+`article` both sit in
    their names, four of them WRITE tools (publish x2 / retire / update) that a
    real client would never pick for a read. Tier 1 cannot rename them out of
    the band; folding/renaming the KB surface is a Tier 2 target. Net across all
    30 intents ambiguity fell (66 -> 50); this one collision rose by one as the
    direct cost of fixing its top pick.
    """

    @pytest.mark.parametrize('intent,plan_count,router_count', [
        ('show me all P1 incidents from last week', 4, 3),
        ('knowledge articles about password reset', 3, 6),
        ('which SLAs are breached', 3, 1),
        ('is the ServiceNow connection up', 5, 3),
    ])
    def test_collision_path_count_recorded(self, intent, plan_count, router_count):
        """A change here means the surface shifted — re-derive both counts, don't tweak."""
        ranked = _rank(intent, _profiles())
        assert len(_plausible_paths(ranked)) <= router_count
