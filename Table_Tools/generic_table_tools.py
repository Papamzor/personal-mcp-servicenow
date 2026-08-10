import sys
from http_layer import (
    NWS_API_BASE,
    ServiceNowRequestError,
    encode_query_string,
    make_nws_request,
)
from utils import extract_keywords
from typing import Any, Dict, Optional, List
import re
from constants import (
    ESSENTIAL_FIELDS,
    DETAIL_FIELDS,
    NO_RECORDS_FOUND,
    RECORD_NOT_FOUND,
    NO_SIMILAR_RECORDS_FOUND,
    CONNECTION_ERROR,
    NO_DESCRIPTION_FOUND,
    REQUEST_FAILED_ERROR,
    NO_FIELD_CONFIG_ERROR,
    NO_VALID_PRIORITIES_ERROR,
    TABLE_NO_PRIORITY_SUPPORT_ERROR,
    MONTH_NAME_TO_NUMBER,
    text_search_field_for,
    LOGICMONITOR_CALLER_SYS_ID,
    ENABLE_COMPLETE_QUERY,
    QUERY_FIELD_NAME_ERROR,
    QUERY_FRAGMENT_AMPERSAND_ERROR,
    QUERY_VALUE_NEW_QUERY_ERROR,
    TABLE_CONFIGS
)
from .read_helpers import carry_partial, carry_partial_after_filter, is_read_failure
from filter import (
    QueryExplainer,
    QueryIntelligence,
    QueryValueError,
    TableFilterParams,
    build_pagination_params,
    build_smart_filter,
    encode_query_value,
    explain_existing_filter,
    suggest_query_improvements,
    validate_query_filters,
    validate_result_count,
)


# ---------------------------------------------------------------------------
# Read-failure contract (v4.4 Tier 0.3). A failed GET arrives here as a raised
# `ServiceNowRequestError` instead of `None`. This module was migrated first, so
# the rules below were settled here and are reused by every other consumer:
#
#   1. A raise returns `error.to_error_dict()` -> {"error": {code, message}}
#      and nothing else. `retryable` is for our own retry logic, not the client,
#      and the code is never translated into prose.
#   2. An empty result stays not-found. HTTP 200 + {"result": []} keeps the
#      existing RECORD_NOT_FOUND / NO_RECORDS_FOUND message: empty is success.
#      The only thing that changes is that a *failure* no longer shares it.
#   3. A page failing mid-pagination keeps the rows already collected and marks
#      the response `partial` (see `PartialPageReadError` / `_partial_envelope`).
#      Page 1 failing has no rows to keep, so it is a plain error with no
#      `partial` key.
#   4. `except ServiceNowRequestError` always precedes a bare `except Exception`
#      so the typed failure is never flattened into a message string.
# ---------------------------------------------------------------------------
# Encoded-query value boundary (v4.4.1). Every caller-supplied value that ends up
# as the operand of a condition is escaped here, by `encode_query_value`, and the
# transport preserves that escaping instead of unquoting it away. Two rules:
#
#   * A condition handler is either STRUCTURAL — the value IS a query fragment
#     (`priority=1^ORpriority=2`, a BETWEEN/javascript range, a `^`-joined
#     exclusion list) — or TERMINAL, pasting the value after `field=` or after an
#     operator. Only terminal handlers encode. Encoding a structural value would
#     escape the operators it is made of.
#   * `^` inside a terminal value is refused (`QueryValueError`), not escaped:
#     ServiceNow's parser splits on the DECODED value, so no encoding can carry
#     it. Every public entry point below maps that refusal to
#     `{"error": {"code": "VALIDATION", ...}}`, because a filter that cannot be
#     expressed must not become a filter that quietly matches more.
# ---------------------------------------------------------------------------


class PartialPageReadError(Exception):
    """A page after the first failed; the rows already collected are attached.

    Deliberately NOT a `ServiceNowRequestError` subclass. If it were, every
    `except ServiceNowRequestError` arm would silently absorb it and throw away
    the rows it carries — the exact "discard 250 good rows because page 2 died"
    behavior this replaces. Being a separate type means a call site that forgets
    it degrades to a plain error rather than to a wrong-looking empty result.

    Only raised when at least one row was already collected; a first-page
    failure propagates as `ServiceNowRequestError`.
    """

    def __init__(self, rows: List[Dict[str, Any]], error: ServiceNowRequestError) -> None:
        super().__init__(error.message)
        self.rows = rows
        self.error = error


def _partial_envelope(base: Dict[str, Any], partial: PartialPageReadError) -> Dict[str, Any]:
    """Mark an otherwise-normal response as a partial read.

    The one sanctioned shape where rows and `error` coexist (plan §3.1): the
    rows are real and usable, and the error says why the set is incomplete.
    """
    return {**base, "partial": True, **partial.error.to_error_dict()}


def _validate_regex_input(text: str) -> bool:
    """Pre-validate input to prevent ReDoS attacks."""
    if not isinstance(text, str):
        return False
    # Reject overly long strings that could cause ReDoS
    if len(text) > 200:
        return False
    # Reject strings with suspicious patterns
    if text.count(' ') > 50 or text.count('-') > 20:
        return False
    return True


def _is_safe_record_number(record_number: str) -> bool:
    """Reject record numbers that carry query operators/whitespace instead of a plain number.

    `get_record_description` / `get_record_details` interpolate record_number
    directly into `number={record_number}`. A record_number containing `^`
    (AND/OR/NQ), whitespace, `&`, or a comparison operator could append
    conditions to that query, or smuggle a `^NQ` new-query-reset that discards
    the `number=` scoping entirely and turns a single-record lookup into an
    unbounded table read.
    """
    if not record_number:
        return False
    if re.search(r'[\^\s&=<>]', record_number):
        return False
    return True


async def query_table_by_text(
    table_name: str,
    input_text: str,
    detailed: bool = False,
    search_field: Optional[str] = None,
) -> dict[str, Any]:
    """Generic function to query any ServiceNow table by text similarity.

    Builds ONE OR-combined query across every extracted keyword
    (``short_descriptionLIKEa^ORshort_descriptionLIKEb``) so a single request
    matches any keyword — replacing the old per-keyword sequential request
    loop (N round-trips, single-keyword recall). LIKE is ServiceNow's
    encoded-query "contains" operator; CONTAINS is GlideRecord scripting-only
    and is silently ignored in sysparm_query strings (returns zero rows), so
    it must never appear here.

    ``search_field`` defaults to whatever ``text_search_field_for(table_name)``
    resolves to, NOT to a fixed ``short_description``. That matters because a
    filter against a field the table does not have is **silently dropped** by
    ServiceNow: the query degenerates to no conditions and the caller gets an
    arbitrary page of rows presented as matches. ``task_sla`` has no
    ``short_description`` of its own, so it resolves to the dot-walked
    ``task.short_description``. Resolving from the table rather than requiring
    each caller to pass the right field means a new call site cannot
    reintroduce the bug by forgetting.

    This path is immune to the encoded-query value defect for a reason nobody
    designed: ``utils.extract_keywords`` tokenizes on ``\\b[a-zA-Z]{4,}\\b``, so a
    keyword cannot contain ``^``, ``&`` or ``%``. The keywords are escaped anyway
    (a no-op today) and ``tests/test_query_value_encoding.py`` pins the
    tokenizer's character class, because the protection is incidental and a
    widened tokenizer would remove it silently.
    """
    search_field = search_field or text_search_field_for(table_name)
    fields = DETAIL_FIELDS[table_name] if detailed else ESSENTIAL_FIELDS[table_name]
    keywords = extract_keywords(input_text)
    if not keywords:
        return {"result": [], "message": NO_RECORDS_FOUND}

    # OR-group the keyword conditions so one request matches any keyword.
    try:
        query = "^OR".join(
            f"{search_field}LIKE{encode_query_value(keyword)}" for keyword in keywords
        )
    except QueryValueError as refusal:
        return refusal.to_error_dict()
    base_url = f"{NWS_API_BASE}/api/now/table/{table_name}?sysparm_fields={','.join(fields)}&sysparm_query={query}"
    # Single paginated request; text searches capped at 50 results.
    try:
        all_results = await _make_paginated_request(base_url, max_results=50)
    except PartialPageReadError as partial:
        return _partial_envelope(_text_search_envelope(partial.rows, input_text), partial)
    except ServiceNowRequestError as error:
        return error.to_error_dict()

    return _text_search_envelope(all_results, input_text)


def _text_search_envelope(rows: List[Dict[str, Any]], input_text: str) -> dict[str, Any]:
    """Response shape for a text search. No rows is not-found, never a failure."""
    if not rows:
        return {"result": [], "message": NO_RECORDS_FOUND}
    result_count = len(rows)
    limit_note = " (limited to 50)" if result_count == 50 else ""
    return {
        "result": rows,
        "message": f"Found {result_count} records matching '{input_text}'{limit_note}",
    }


async def get_record_description(table_name: str, record_number: str) -> dict[str, Any]:
    """Generic function to get short_description for any record."""
    if not _is_safe_record_number(record_number):
        return {"result": [], "message": RECORD_NOT_FOUND}
    # `encode_query_value` cannot refuse here: `_is_safe_record_number` already
    # rejected `^`. It is applied for the `%` case — an unescaped "INC%41" used to
    # be decoded by the transport into "INCA", a lookup for a different record.
    query = f"number={encode_query_value(record_number)}"
    url = f"{NWS_API_BASE}/api/now/table/{table_name}?sysparm_fields=short_description&sysparm_query={query}"
    try:
        data = await make_nws_request(url)
    except ServiceNowRequestError as error:
        # A failed lookup is not a missing record. RECORD_NOT_FOUND below is
        # reserved for a successful read that returned no rows.
        return error.to_error_dict()
    return _record_envelope(data)

async def get_record_details(table_name: str, record_number: str) -> dict[str, Any]:
    """Generic function to get detailed information for any record."""
    if not _is_safe_record_number(record_number):
        return {"result": [], "message": RECORD_NOT_FOUND}
    fields = DETAIL_FIELDS.get(table_name, ["number", "short_description"])
    # See `get_record_description`: guarded against `^` upstream, escaped for `%`.
    query = f"number={encode_query_value(record_number)}"
    url = f"{NWS_API_BASE}/api/now/table/{table_name}?sysparm_fields={','.join(fields)}&sysparm_query={query}&sysparm_display_value=true"
    try:
        data = await make_nws_request(url)
    except ServiceNowRequestError as error:
        return error.to_error_dict()
    return _record_envelope(data)


def _record_envelope(data: Optional[dict[str, Any]]) -> dict[str, Any]:
    """Single-record read shape. A successful read with no rows is not-found.

    Before v4.4 this label was also produced when the request itself failed
    (the read path returned `None` for both). Failures are mapped by the caller
    now, so RECORD_NOT_FOUND means only what it says.
    """
    if not data or not data.get("result"):
        return {"result": [], "message": RECORD_NOT_FOUND}
    return data


def _first_short_description(desc_data: dict[str, Any]) -> str:
    """Pull the first row's short_description out of a description response."""
    rows = desc_data.get('result') or []
    if not rows:
        return ""
    return (rows[0].get('short_description') or "").strip()


def _exclude_original_record(similar_data: dict[str, Any], record_number: str) -> dict[str, Any]:
    """Drop the source record from a text-search result, preserving partial state.

    Filtering can empty a partial set, in which case NO_SIMILAR_RECORDS_FOUND
    would be a confident answer drawn from an unfinished read — the pages that
    failed could hold similar records. `carry_partial_after_filter` returns the
    failure instead.
    """
    rows = similar_data.get('result') or []
    if not rows:
        return similar_data  # nothing to filter — pass the inner response through
    filtered_results = [record for record in rows if record.get('number') != record_number]
    if filtered_results:
        response = {
            "result": filtered_results,
            "message": f"Found {len(filtered_results)} similar records (excluding original record)",
        }
    else:
        response = {"result": [], "message": NO_SIMILAR_RECORDS_FOUND}
    return carry_partial_after_filter(response, similar_data)


async def find_similar_records(table_name: str, record_number: str) -> dict[str, Any]:
    """Generic function to find similar records based on a given record's description.

    Both inner calls return their own failure dicts now, so a transport failure
    is passed through as-is rather than being reported as "no description found"
    or as the generic CONNECTION_ERROR string.
    """
    try:
        desc_data = await get_record_description(table_name, record_number)
        if is_read_failure(desc_data):
            return desc_data

        desc_text = _first_short_description(desc_data)
        if not desc_text:
            return {"result": [], "message": NO_DESCRIPTION_FOUND}

        similar_data = await query_table_by_text(table_name, desc_text)
        if is_read_failure(similar_data):
            return similar_data
        return _exclude_original_record(similar_data, record_number)
    except ServiceNowRequestError as error:
        # Defensive: the calls above map their own failures, so reaching this
        # arm means a new raise path appeared. Map it into the error vocabulary
        # rather than letting CONNECTION_ERROR become a fourth error dialect.
        return error.to_error_dict()
    except Exception:
        return {"result": [], "message": CONNECTION_ERROR}

# TableFilterParams moved to filter/models.py in v4.0 Sprint 1.
# Re-exported above via `from filter import ...` so existing imports of
# the name from this module continue to work.

# ServiceNow encoded-query text/date operators written as a prefix on the value
# (e.g. "LIKEfoo", "ONLast week", "BETWEENa@b"). These are the operators that are
# VALID inside a sysparm_query string. CONTAINS / NOTCONTAINS are deliberately
# absent: they are GlideRecord *scripting* operators, silently ignored in encoded
# queries, and are rewritten to LIKE / NOT LIKE by `_normalize_operator` before
# this check runs.
_OP_NOT_LIKE = 'NOT LIKE'
_SN_PREFIX_OPERATORS = (
    _OP_NOT_LIKE, 'NOTLIKE', 'LIKE', 'STARTSWITH', 'ENDSWITH',
    'ISNOTEMPTY', 'ISEMPTY', 'BETWEEN', 'SAMEAS', 'NSAMEAS',
    'INSTANCEOF', 'NOT IN', 'NOTIN', 'ONLAST', 'ONTODAY', 'ON',
)
# 'IN' collides with ordinary words ("INTERNAL"). Treat it as an operator only
# when not followed by another letter, so "IN1,2" and bare "IN" match but
# "INTERNAL" does not. ('ON' stays a plain prefix above — it legitimately
# precedes date keywords like "ONToday"/"ONLast week".)
_SN_AMBIGUOUS_OPERATORS = ('IN',)


def _normalize_operator(value: str) -> str:
    """Rewrite GlideRecord-only operators to their encoded-query equivalents.

    ``CONTAINS`` / ``NOTCONTAINS`` are valid in GlideRecord scripting but NOT in
    encoded query strings (sysparm_query), where they are silently ignored and
    return zero rows. The encoded-query equivalents are ``LIKE`` / ``NOT LIKE``.
    Applied before condition building so a caller-supplied ``"CONTAINSfoo"`` (as
    the public docstring historically advertised) still works.
    """
    if not isinstance(value, str):
        return value
    for bad, good in (('NOTCONTAINS', _OP_NOT_LIKE), ('NOT CONTAINS', _OP_NOT_LIKE), ('CONTAINS', 'LIKE')):
        if value.startswith(bad):
            return good + value[len(bad):]
    return value


def _has_operator_in_value(value: str) -> bool:
    """Check if value already contains a comparison operator or ServiceNow text operator."""
    if not isinstance(value, str):
        return False
    # Standard comparison operators
    if any(op in value for op in ['>=', '<=', '>', '<', '=', '!=']):
        return True
    # ServiceNow text/date operators that prefix the value (e.g., "ONLast week", "LIKEfoo")
    if any(value.startswith(op) for op in _SN_PREFIX_OPERATORS):
        return True
    # Ambiguous 2-letter operators: require the next char to not be a letter so
    # ordinary words ("INTERNAL", "ONLINE") are not misread as operators.
    return any(
        value.startswith(op) and (len(value) == len(op) or not value[len(op)].isalpha())
        for op in _SN_AMBIGUOUS_OPERATORS
    )

def _is_complete_servicenow_filter(value: str) -> bool:
    """Check if value is already a complete ServiceNow filter (e.g., priority=1^ORpriority=2).

    A complete filter must have field=value structure before any ^OR operator.
    Values like "1^ORpriority=2" are NOT complete filters (missing field name before first value).
    """
    if not isinstance(value, str):
        return False
    if '^OR' in value:
        # Verify it's truly a complete filter: text before ^OR must contain '=' (field=value)
        before_or = value.split('^OR')[0]
        return '=' in before_or
    return False

def _month_name_to_num(name: str) -> Optional[int]:
    """Resolve an English month name (full or 3+ letter abbrev) to its 1-12 number."""
    return MONTH_NAME_TO_NUMBER.get(name.lower())


def _iso_range_from_month_names(
    start_month_name: str, start_day: int, start_year: int,
    end_month_name: str, end_day: int, end_year: int,
) -> Optional[tuple]:
    """Build an (ISO start, ISO end) date tuple from month-name components.

    Returns None when either month name is unknown — caller treats that as
    a non-match so the next parser in the registry gets a chance.
    """
    start_month = _month_name_to_num(start_month_name)
    end_month = _month_name_to_num(end_month_name)
    if not (start_month and end_month):
        return None

    start_date = f"{start_year}-{start_month:02d}-{start_day:02d}"
    end_date = f"{end_year}-{end_month:02d}-{end_day:02d}"
    return (start_date, end_date)


def _parse_week_format(text: str) -> Optional[tuple]:
    """Parse 'Week X YYYY' format. Complexity: 3"""
    from datetime import datetime, timedelta

    week_match = re.search(r'week (\d{1,2}) (?:of )?(\d{4})', text)
    if not week_match:
        return None

    week_num = int(week_match.group(1))
    year = int(week_match.group(2))

    # Calculate start date of the week (assuming week starts on Monday)
    jan_4 = datetime(year, 1, 4)
    week_start = jan_4 - timedelta(days=jan_4.weekday()) + timedelta(weeks=week_num - 1)
    week_end = week_start + timedelta(days=6)

    return (week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d'))

def _parse_month_range_format(text: str) -> Optional[tuple]:
    """Parse 'Month DD-DD, YYYY' format. Complexity: 3"""
    match = re.search(r'(\w{3,9}) (\d{1,2})-(\d{1,2}), ?(\d{4})', text)
    if not match:
        return None

    month_name = match.group(1)
    start_day = int(match.group(2))
    end_day = int(match.group(3))
    year = int(match.group(4))

    return _iso_range_from_month_names(
        month_name, start_day, year,
        month_name, end_day, year,
    )

def _parse_iso_date_range(text: str) -> Optional[tuple]:
    """Parse 'YYYY-MM-DD to YYYY-MM-DD' format. Complexity: 2"""
    date_range_match = re.search(r'(\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})', text)
    if not date_range_match:
        return None

    return (date_range_match.group(1), date_range_match.group(2))

def _parse_cross_month_range(text: str) -> Optional[tuple]:
    """Parse 'Month DD YYYY to Month DD YYYY' format. Complexity: 3"""
    match = re.search(
        r'(?:from )?(\w{3,9}) (\d{1,2}),? (\d{4}) to (\w{3,9}) (\d{1,2}),? (\d{4})',
        text,
    )
    if not match:
        return None

    return _iso_range_from_month_names(
        match.group(1), int(match.group(2)), int(match.group(3)),
        match.group(4), int(match.group(5)), int(match.group(6)),
    )

def _parse_between_format(text: str) -> Optional[tuple]:
    """Parse 'between Month DD, YYYY and Month DD, YYYY' format. Complexity: 3"""
    match = re.search(
        r'between (\w{3,9}) (\d{1,2}),? (\d{4}) and (\w{3,9}) (\d{1,2}),? (\d{4})',
        text,
    )
    if not match:
        return None

    return _iso_range_from_month_names(
        match.group(1), int(match.group(2)), int(match.group(3)),
        match.group(4), int(match.group(5)), int(match.group(6)),
    )

def _parse_year_at_end_format(text: str) -> Optional[tuple]:
    """Parse 'Month DD to Month DD YYYY' format (year at end). Complexity: 3"""
    match = re.search(
        r'(?:from )?(\w{3,9}) (\d{1,2}) to (\w{3,9}) (\d{1,2}),? (\d{4})',
        text,
    )
    if not match:
        return None

    year = int(match.group(5))
    return _iso_range_from_month_names(
        match.group(1), int(match.group(2)), year,
        match.group(3), int(match.group(4)), year,
    )

def _parse_date_range_from_text(text: str) -> Optional[tuple]:
    """Parse date range from natural language text with ReDoS protection.

    Handles formats like:
    - "Week 35 2025" or "week 35 of 2025"
    - "August 25-31, 2025"
    - "2025-08-25 to 2025-08-31"
    - "last week", "this week"

    Complexity: 8 (reduced from ~30-35)
    """
    # Pre-validate input length/shape to prevent ReDoS attacks before any regex runs.
    if not _validate_regex_input(text):
        return None

    text = text.lower().strip()

    # Date parser registry - try each parser in sequence until one succeeds.
    parsers = [
        _parse_week_format,
        _parse_month_range_format,
        _parse_iso_date_range,
        _parse_cross_month_range,
        _parse_between_format,
        _parse_year_at_end_format,
    ]
    for parser in parsers:
        result = parser(text)
        if result:
            return result
    return None

def _normalize_priority_value(priority: str) -> str:
    """Convert P-notation to number (e.g., 'P1' -> '1', '2' -> '2')."""
    if priority.upper().startswith("P") and len(priority) > 1:
        return priority[1:]  # Remove 'P' prefix
    return priority


def _clean_priority_input(value: str) -> str:
    """Clean brackets, quotes from priority input."""
    return value.strip("[]\"'")


def _process_comma_separated_priorities(value: str) -> str:
    """Process comma-separated priority list into OR syntax.

    Structural overall — the `^OR` join is ours — but each element is a terminal
    value and is escaped as one. `_normalize_priority_value` only strips a leading
    "P", so anything else the caller sent arrives here intact.
    """
    clean_value = _clean_priority_input(value)
    priorities = [p.strip().strip("\"'") for p in clean_value.split(",")]

    # Convert P1/P2 notation to numbers
    priority_nums = [_normalize_priority_value(p) for p in priorities if p]

    # Build OR syntax
    priority_conditions = [f"priority={encode_query_value(p)}" for p in priority_nums]
    return "^OR".join(priority_conditions)


def _format_single_priority(value: str) -> str:
    """Format single priority value. Terminal."""
    priority_num = _normalize_priority_value(value)
    return f"priority={encode_query_value(priority_num)}"


def _parse_priority_list(value: str) -> str:
    """Parse priority list and convert to proper OR syntax.
    
    Handles formats like:
    - "1" -> "priority=1"
    - "1,2" -> "priority=1^ORpriority=2"
    - ["1", "2"] as string -> "priority=1^ORpriority=2"
    - "P1,P2" -> "priority=1^ORpriority=2"
    """
    # Early validation - reduces nesting
    if not isinstance(value, str) or not value.strip():
        return ""
    
    value = value.strip()
    
    # Early return for already processed values
    if "^OR" in value:
        return value
    
    # Handle comma-separated values
    if "," in value:
        return _process_comma_separated_priorities(value)
    
    # Handle single priority value
    if value:
        return _format_single_priority(value)
    
    return value

def _parse_caller_exclusions(value: str) -> str:
    """Parse caller exclusion list and convert to NOT EQUALS syntax.
    
    Handles formats like:
    - "logicmonitor" -> "caller_id!=1727339e47d99190c43d3171e36d43ad"
    - "sys_id1,sys_id2" -> "caller_id!=sys_id1^caller_id!=sys_id2"
    """
    if not isinstance(value, str) or not value.strip():
        return ""
    
    value = value.strip()
    
    # Handle known caller names
    known_callers = {
        "logicmonitor": LOGICMONITOR_CALLER_SYS_ID
    }
    
    value_lower = value.lower()
    if value_lower in known_callers:
        return f"caller_id!={known_callers[value_lower]}"
    
    # Handle comma-separated sys_ids. Structural overall (the "^" join is ours),
    # but each sys_id is a terminal value and is escaped as one.
    if "," in value:
        clean_value = value.strip("[]\"'")
        caller_ids = [c.strip().strip("\"'") for c in clean_value.split(",")]
        exclusions = [
            f"caller_id!={encode_query_value(caller_id)}"
            for caller_id in caller_ids
            if caller_id
        ]
        return "^".join(exclusions)

    # Single caller exclusion
    if value and not value.startswith("caller_id!="):
        return f"caller_id!={encode_query_value(value)}"

    return value

def _handle_complete_query_condition(value: str) -> str:
    """Handle complete query condition."""
    return value


def _handle_date_range_condition(field: str, value: str) -> Optional[str]:
    """Handle date range parsing for sys_created_on field.

    Structural on the BETWEEN and natural-language branches (both produce a
    complete fragment, operators and `@` separator included). Terminal on the
    `>=`/`<=` branch — the operand is escaped there. `>` `<` `=` `:` `(` `)` are
    in the value safe-set, so a `>=javascript:gs.daysAgoStart(14)` operand is
    still sent byte-for-byte as before.
    """
    if field == "sys_created_on":
        # If already in BETWEEN format, return as-is
        if "BETWEEN" in value:
            return value
        # If already has operator, return as-is
        if value.startswith((">=", "<=")):
            return f"{field}{encode_query_value(value)}"
        # Try to parse natural language date range
        date_range = _parse_date_range_from_text(value)
        if date_range:
            start_date, end_date = date_range
            return f"sys_created_onBETWEENjavascript:gs.dateGenerate('{start_date}','00:00:00')@javascript:gs.dateGenerate('{end_date}','23:59:59')"
    return None


def _handle_priority_condition(field: str, value: str) -> Optional[str]:
    """Handle priority list parsing."""
    if field == "priority" and ("," in value or value.upper().startswith("P")):
        return _parse_priority_list(value)
    return None


def _handle_caller_exclusion_condition(field: str, value: str) -> Optional[str]:
    """Handle caller exclusions."""
    if field == "exclude_caller" or field == "caller_exclusion":
        return _parse_caller_exclusions(value)
    return None


def _handle_bare_or_value_condition(field: str, value: str) -> Optional[str]:
    """Handle values with ^OR where the first segment is a bare value (missing field name).

    When an LLM constructs a filter like {"priority": "1^ORpriority=2"}, the "1" before
    ^OR is missing its field name. This handler prepends the field name to produce a valid
    ServiceNow query: "priority=1^ORpriority=2".

    Works for any field (priority, task.priority, state, etc.).

    STRUCTURAL, so the value is not escaped: it carries its own `^OR` and its own
    `field=value` segments after the first. That makes `^OR` in a filter value
    always read as structure, never as literal text — the one place the caret
    refusal does not apply, because the handler exists precisely to honour an
    LLM's intent to write an OR. A title genuinely containing "^OR" is
    unqueryable here, the same as any other `^`.
    """
    if "^OR" not in value:
        return None
    before_or = value.split("^OR")[0]
    if "=" not in before_or:
        return f"{field}={value}"
    return None


def _handle_servicenow_filter_condition(field: str, value: str) -> Optional[str]:
    """Handle complete ServiceNow filters."""
    if _is_complete_servicenow_filter(value):
        return value
    return None


def _handle_operator_condition(field: str, value: str) -> Optional[str]:
    """Handle direct operator syntax.

    Terminal: the operator is a prefix ON the value (`LIKEserver down`,
    `>=2024-01-01`), so the whole value is escaped. Every operator character is
    either in the value safe-set or was already being escaped by the transport —
    `NOT LIKE` has always reached ServiceNow as `NOT%20LIKE`.
    """
    if _has_operator_in_value(value):
        return f"{field}{encode_query_value(value)}"
    return None


# Suffix-to-operator mapping. Order matters: longer suffixes ('_gte', '_lte') must be
# checked before shorter ones ('_gt', '_lt') so 'priority_gte' is not parsed as 'priority_g'.
_SUFFIX_OPERATORS = (
    ('_gte', '>='),
    ('_lte', '<='),
    ('_gt', '>'),
    ('_lt', '<'),
)


def _handle_suffix_operator_condition(field: str, value: str) -> Optional[str]:
    """Handle suffix-based operators (foo_gte=5 -> foo>=5). Terminal."""
    for suffix, operator in _SUFFIX_OPERATORS:
        if field.endswith(suffix):
            return f"{field[:-len(suffix)]}{operator}{encode_query_value(value)}"
    return None


def _handle_exact_match_condition(field: str, value: str) -> str:
    """Handle exact match condition. Terminal, and the default — so this is the
    handler that refuses a `^`-bearing value that no structural handler claimed."""
    return f"{field}={encode_query_value(value)}"


# Condition handler registry, ordered by specificity. Built once at import
# (mirrors the _SUFFIX_OPERATORS pattern) rather than per _build_query_condition call.
_CONDITION_HANDLERS = (
    _handle_date_range_condition,
    _handle_priority_condition,
    _handle_caller_exclusion_condition,
    _handle_bare_or_value_condition,
    _handle_servicenow_filter_condition,
    _handle_operator_condition,
    _handle_suffix_operator_condition,
)


# A legitimate field name: identifier characters, '.' for dot-walked references
# (task.priority), and a leading '_' for the internal fragment keys.
_FIELD_NAME_PATTERN = re.compile(r'[A-Za-z_][A-Za-z0-9_.]*')


def _reject_new_query_reset(value: str) -> None:
    """Refuse a `^NQ` new-query-reset anywhere in a caller-supplied string.

    `^NQ` starts a brand-new query, discarding every condition built before it, so
    one poisoned filter turns a scoped query into an unbounded table read.

    Called at the TOP of `_build_query_condition`, ahead of the fragment
    early-returns. It used to sit after them, so `_complete_caller_exclusion` and
    `_complete_query` walked straight past it — and `_build_additional_filters`,
    a second assembly path, never reached it at all.
    """
    if isinstance(value, str) and "^NQ" in value.upper():
        raise QueryValueError.refused(value, QUERY_VALUE_NEW_QUERY_ERROR)


def _reject_unsafe_fragment(value: str) -> None:
    """Guard for the three keys that take a pre-built fragment instead of a value.

    A fragment carries its own operators, so it cannot be escaped and `^` has to be
    allowed. `&` cannot be: it is not an encoded-query operator, so it only ever
    ends the query string and drops the rest of the fragment. See
    `QUERY_FRAGMENT_AMPERSAND_ERROR`.
    """
    _reject_new_query_reset(value)
    if isinstance(value, str) and "&" in value:
        raise QueryValueError.refused(value, QUERY_FRAGMENT_AMPERSAND_ERROR)


def _reject_unsafe_field_name(field: str) -> None:
    """Refuse a field name that is not a plain field name.

    The keys of a `filters` dict are caller-supplied and were never checked, so
    `{"x^NQstate=99": "1"}` built `x^NQstate=99=1` — the value guard refuses that
    payload in a value and used to wave it through in a key.
    """
    if not isinstance(field, str) or not _FIELD_NAME_PATTERN.fullmatch(field):
        raise QueryValueError.refused(str(field), QUERY_FIELD_NAME_ERROR)


def _build_query_condition(field: str, value: str) -> str:
    """Build a single query condition based on field and value."""
    _reject_unsafe_field_name(field)
    # Ahead of every early return below: a fragment key must not be a way past it.
    _reject_new_query_reset(value)

    # Handle special complete query cases first. Both are pre-built fragments, so
    # both get the fragment guard rather than value escaping — and both are reached
    # only after the `^NQ` refusal above, which is the point.
    if field == "_complete_query":
        # `_complete_query` hands a raw, caller-built encoded query straight
        # through, bypassing every per-field handler. Gated off by default; drop it
        # entirely (rather than call the handler) unless explicitly re-enabled.
        if not ENABLE_COMPLETE_QUERY:
            return ""
        _reject_unsafe_fragment(value)
        return _handle_complete_query_condition(value)
    if field == "_complete_caller_exclusion":
        _reject_unsafe_fragment(value)
        return value  # Already in complete ServiceNow format

    # Rewrite GlideRecord-only operators (CONTAINS/NOTCONTAINS) to their
    # encoded-query equivalents (LIKE/NOT LIKE) before any handler runs.
    #
    # The `^NQ` refusal runs BEFORE this, at the top of the function: it has to
    # precede the fragment early-returns above, and normalisation cannot introduce
    # or remove a `^NQ`. The structural handlers below would otherwise claim
    # `1^ORpriority=2^NQactive=true` as a caller-built fragment and never reach an
    # encoder, which is why the check is not left to `encode_query_value`.
    value = _normalize_operator(value)

    # Try each condition handler until one matches
    for handler in _CONDITION_HANDLERS:
        result = handler(field, value)
        if result is not None:
            return result

    # Default to exact match if no specialized handler applies
    return _handle_exact_match_condition(field, value)

def _build_query_string(filters: Dict[str, str]) -> str:
    """Build the complete query string from filters.

    Raises:
        QueryValueError: a filter value cannot be carried by encoded-query
            syntax (`^`, or a `^NQ` reset). Every caller maps it to a VALIDATION
            error dict; none of them may swallow it, because the alternative is
            a query that runs broader than the one requested.
    """
    if not filters:
        return ""

    query_parts = []
    for field, value in filters.items():
        query_parts.append(_build_query_condition(field, value))

    # A condition handler (e.g. the ENABLE_COMPLETE_QUERY gate, or the ^NQ
    # defense) may now return "" to drop a condition entirely. Skip empties
    # so a dropped condition doesn't leave a dangling "^^" or a leading/
    # trailing "^" in the joined query.
    return "^".join(part for part in query_parts if part)

def _encode_query_string(query_string: str) -> str:
    """URL encode query string while preserving ServiceNow JavaScript functions and operators.

    Thin alias for the transport's encoder since v4.4.1 — it used to be a second,
    independent `quote(safe=...)` with different rules and no idempotency, so a
    value could pass through two encoders that disagreed and be round-trip-stable
    only by luck. One implementation now: escapes already applied by
    `encode_query_value` survive both passes, and applying this before
    `make_nws_request` is a no-op rather than a second opinion.
    """
    return encode_query_string(query_string)

def _inject_sort_order(url: str, sort_directive: str) -> str:
    """Inject a sort directive into the URL's sysparm_query if no ORDERBY is present.

    Args:
        url: The full API URL (may or may not contain sysparm_query)
        sort_directive: e.g. "ORDERBYDESCsys_created_on"

    Returns:
        URL with the sort directive appended to sysparm_query
    """
    if "ORDERBY" in url:
        return url
    if "sysparm_query=" in url:
        return re.sub(r'(sysparm_query=[^&]*)', rf'\1^{sort_directive}', url)
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}sysparm_query={sort_directive}"


async def _make_paginated_request(
    url: str,
    max_results: int = 100,  # More reasonable default limit
    page_size: int = 250,
    default_sort: str = "ORDERBYDESCsys_created_on"
) -> List[Dict[str, Any]]:
    """Make paginated requests to get complete result sets.

    Raises:
        PartialPageReadError: a page after the first failed. Carries the rows
            collected so far — they are real records and are not discarded
            because a later page timed out.
        ServiceNowRequestError: the first page failed, so there is nothing to
            keep and the whole read is a failure.
    """
    if default_sort:
        url = _inject_sort_order(url, default_sort)
    all_results = []
    offset = 0

    while len(all_results) < max_results:
        paginated_url = f"{url}&sysparm_offset={offset}&sysparm_limit={page_size}"
        try:
            data = await make_nws_request(paginated_url)
        except ServiceNowRequestError as error:
            # No slicing needed: the loop condition guarantees
            # len(all_results) < max_results at the top of every iteration.
            if all_results:
                raise PartialPageReadError(all_results, error) from error
            raise

        # A 200 with no rows ends the walk normally — empty is success.
        if not data or not data.get('result'):
            break

        batch_results = data['result']
        if not batch_results:
            break
        
        all_results.extend(batch_results)
        
        # If we got less than page_size, we've reached the end
        if len(batch_results) < page_size:
            break
        
        offset += page_size
    
    return all_results[:max_results]


def _warn_on_validation_issues(validation: Optional[Any], label: str) -> None:
    """Log a validation result's warnings to stderr, if it has any.

    Extracted because the caller ran this shape twice — once for the filters and
    once for the result count — and each copy nested an `if has_issues()` inside
    another branch. Warnings go to stderr only: stdout is reserved for the MCP
    JSON-RPC frame stream.
    """
    if validation and validation.has_issues():
        print(f"[generic_table_tools] {label}: {validation.warnings}", file=sys.stderr)


async def query_table_with_filters(table_name: str, params: TableFilterParams) -> dict[str, Any]:
    """Generic function to query table with custom filters and fields.

    Supports multiple date filtering formats:
    - Standard dates: "2024-01-01" or "2024-01-01 12:00:00"
    - ServiceNow JavaScript: ">=javascript:gs.daysAgoStart(14)"
    - Relative operators: field_gte, field_lte, field_gt, field_lt

    Examples:
    - sys_created_on_gte: "2024-01-01"
    - sys_created_on: ">=javascript:gs.daysAgoStart(14)"

    Response always includes returned_count + truncated + max_results so the
    caller can detect silent caps. truncated=True is a heuristic — it fires when
    returned_count == max_results (may be a false positive on exact-boundary
    result sets, but never a false negative).

    A read failure returns {"error": {code, message}}. A failure *after* some
    pages succeeded returns the collected rows plus `partial: true` and the
    error, so the caller can use the rows and still know the set is incomplete.
    """
    fields = params.fields or ESSENTIAL_FIELDS.get(table_name, ["number", "short_description"])

    # Validate filters before making the request; warnings do not stop the query.
    validation_result = validate_query_filters(params.filters) if params.filters else None
    _warn_on_validation_issues(validation_result, "Query validation warnings")

    try:
        query_string = _build_query_string(params.filters)
    except QueryValueError as refusal:
        # A filter that cannot be expressed is an error, never a dropped
        # condition: dropping it would answer a broader question and label the
        # rows as matches.
        return refusal.to_error_dict()
    encoded_query = _encode_query_string(query_string)

    base_url = f"{NWS_API_BASE}/api/now/table/{table_name}?sysparm_fields={','.join(fields)}&sysparm_display_value=true"

    if encoded_query:
        base_url += f"&sysparm_query={encoded_query}"

    max_results = params.max_results
    partial_read: Optional[PartialPageReadError] = None
    try:
        all_results = await _make_paginated_request(base_url, max_results=max_results)
    except PartialPageReadError as partial:
        all_results, partial_read = partial.rows, partial
    except ServiceNowRequestError as error:
        return error.to_error_dict()
    returned_count = len(all_results)
    truncated = returned_count >= max_results

    if all_results:
        # Validate result completeness. Only on a non-empty set — an empty result
        # has nothing to check, and this costs a pass over the filters.
        _warn_on_validation_issues(
            validate_result_count(table_name, params.filters or {}, returned_count),
            "Result validation warnings",
        )

        response = {
            "result": all_results,
            "returned_count": returned_count,
            "truncated": truncated,
            "max_results": max_results,
        }
        return _partial_envelope(response, partial_read) if partial_read else response

    empty_response = {
        "result": [],
        "message": NO_RECORDS_FOUND,
        "returned_count": 0,
        "truncated": False,
        "max_results": max_results,
    }
    # Surface validation suggestions (e.g. reference-field dot-walk hint) on an
    # empty result so the caller can tell a genuine no-match from a silent
    # query-syntax mistake. Warnings here previously only went to stderr.
    if validation_result and validation_result.suggestions:
        empty_response["suggestions"] = validation_result.suggestions
    return empty_response


def _determine_filter_sources(
    intelligence_filters: Dict,
    filters_from_nl: Dict,
    filters_from_context: Dict
) -> Dict[str, str]:
    """Determine the source of each filter. Complexity: 4"""
    filter_sources = {}
    for field in intelligence_filters.keys():
        if field in filters_from_context:
            filter_sources[field] = "context"
        elif field in filters_from_nl:
            filter_sources[field] = "natural_language"
        else:
            filter_sources[field] = "combined"
    return filter_sources

def _build_debug_info(
    intelligence_result: Dict,
    context: Optional[Dict],
    filters_from_nl: Dict,
    filters_from_context: Dict,
    encoded_query: str
) -> Dict[str, Any]:
    """Build debug information dictionary. Complexity: 2"""
    return {
        "encoded_query_sent_to_servicenow": encoded_query,
        "context_received": context,
        "filters_from_context": filters_from_context,
        "filters_from_nl": filters_from_nl,
        "final_merged_filters": intelligence_result["filters"]
    }

def _build_debug_extras(
    intelligence_result: Dict,
    natural_language_query: str,
    table_name: str,
    context: Optional[Dict],
) -> Dict[str, Any]:
    """Recompute filter-source attribution + encoded-query debug block.

    Only invoked when the caller opts into ``debug`` — this is the extra work
    (NL re-parse, context re-apply, query re-encode) that previously ran on
    every intelligent query just to populate the debug payload.
    """
    from filter import QueryIntelligence
    filters_from_nl = QueryIntelligence.parse_natural_language(natural_language_query, table_name).get("filters", {})
    filters_from_context = QueryIntelligence._apply_context_filters(context, table_name) if context else {}
    filter_sources = _determine_filter_sources(intelligence_result["filters"], filters_from_nl, filters_from_context)
    encoded_query = _encode_query_string(_build_query_string(intelligence_result["filters"]))
    debug_info = _build_debug_info(intelligence_result, context, filters_from_nl, filters_from_context, encoded_query)
    return {"filter_sources": filter_sources, "debug": debug_info}


def _build_intelligence_response(
    query_result: Dict,
    intelligence_result: Dict,
    debug_extras: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build successful intelligence response. Debug extras attached only on opt-in."""
    intelligence: Dict[str, Any] = {
        "explanation": intelligence_result["explanation"],
        "confidence": intelligence_result["confidence"],
        "suggestions": intelligence_result["suggestions"],
        "template_used": intelligence_result.get("template_used"),
        "sql_equivalent": intelligence_result.get("sql_equivalent"),
        "filters_used": intelligence_result["filters"],
    }
    if debug_extras:
        intelligence.update(debug_extras)
    return {
        "result": query_result["result"],
        "intelligence": intelligence,
    }

def _build_fallback_response(
    fallback_result: Dict,
    natural_language_query: str,
    table_name: str,
    context: Optional[Dict],
    debug: bool = False,
) -> Dict[str, Any]:
    """Build fallback keyword search response. Debug block attached only on opt-in."""
    intelligence: Dict[str, Any] = {
        "explanation": f"Fallback keyword search for: {natural_language_query}",
        "confidence": 0.3,
        "suggestions": ["Try being more specific with priorities, dates, or states"],
        "template_used": None,
        "sql_equivalent": f"SELECT * FROM {table_name} WHERE short_description LIKE '%{natural_language_query}%'",
        "filters_used": {"short_description": f"short_descriptionLIKE{natural_language_query}"},
    }
    if debug:
        intelligence["filter_sources"] = {"short_description": "fallback"}
        intelligence["debug"] = {
            "encoded_query_sent_to_servicenow": f"short_descriptionLIKE{natural_language_query}",
            "context_received": context,
            "filters_from_context": {},
            "filters_from_nl": {},
            "final_merged_filters": {},
        }
    return {
        "result": fallback_result.get("result", []) if isinstance(fallback_result, dict) else [],
        "intelligence": intelligence,
    }

async def query_table_intelligently(
    table_name: str,
    natural_language_query: str,
    context: Optional[Dict] = None,
    debug: bool = False,
) -> Dict[str, Any]:
    """Query table using natural language with intelligent filter conversion.

    Args:
        table_name: ServiceNow table to query
        natural_language_query: Natural language description of what to find
        context: Optional context for enhancing the query
        debug: When True, attach filter-source attribution + the encoded query
            actually sent. Off by default — building it re-parses the NL query,
            re-applies context, and re-encodes the filter, all purely for the
            debug payload, so it is skipped on the normal path.

    Returns:
        Dictionary containing query results and intelligence metadata

    Complexity: 8 (reduced from ~18-22)
    """
    if table_name not in TABLE_CONFIGS:
        return {"error": f"Invalid table '{table_name}'."}

    intelligence_result = build_smart_filter(natural_language_query, table_name, context)

    # If we got filters, execute the query
    if intelligence_result["filters"]:
        params = TableFilterParams(
            filters=intelligence_result["filters"],
            fields=ESSENTIAL_FIELDS.get(table_name, ["number", "short_description"])
        )

        query_result = await query_table_with_filters(table_name, params)

        # A failed query is not a reason to fall back to a keyword search: the
        # transport just failed, so the second request would fail the same way
        # and the client would be told "no filters matched" instead of why.
        if is_read_failure(query_result):
            return query_result

        # Return successful response if we got results
        if isinstance(query_result, dict) and query_result.get('result'):
            debug_extras = (
                _build_debug_extras(intelligence_result, natural_language_query, table_name, context)
                if debug else None
            )
            response = _build_intelligence_response(query_result, intelligence_result, debug_extras)
            return carry_partial(response, query_result)

    # Fallback to keyword-based search
    fallback_result = await query_table_by_text(table_name, natural_language_query)
    if is_read_failure(fallback_result):
        return fallback_result
    response = _build_fallback_response(
        fallback_result, natural_language_query, table_name, context, debug=debug
    )
    return carry_partial(response, fallback_result)


def explain_filter_query(
    table_name: str,
    filters: Dict[str, str]
) -> Dict[str, Any]:
    """Explain what a filter query will do and provide suggestions.
    
    Args:
        table_name: ServiceNow table name
        filters: Dictionary of filters to explain
        
    Returns:
        Dictionary with explanation and suggestions
    """
    explanation_result = explain_existing_filter(filters, table_name)
    
    return {
        "explanation": explanation_result["explanation"],
        "sql_equivalent": explanation_result["sql_equivalent"],
        "potential_issues": explanation_result["potential_issues"],
        "suggestions": explanation_result["suggestions"],
        "estimated_result_size": explanation_result["estimated_result_size"],
        "filter_analysis": {
            "field_count": len(filters),
            "has_date_filter": any("created_on" in field or "updated_on" in field for field in filters.keys()),
            "has_priority_filter": "priority" in filters,
            "has_state_filter": "state" in filters,
            "complexity": "Simple" if len(filters) <= 2 else "Complex"
        }
    }


def build_and_validate_smart_filter(
    natural_language: str,
    table_name: str,
    context: Optional[Dict] = None
) -> Dict[str, Any]:
    """Build and validate an intelligent filter without executing the query.
    
    This is useful for testing and debugging filter generation.
    """
    intelligence_result = build_smart_filter(natural_language, table_name, context)
    
    # Validate the generated filters
    if intelligence_result["filters"]:
        validation_result = validate_query_filters(intelligence_result["filters"])
        
        return {
            "filters": intelligence_result["filters"],
            "intelligence": intelligence_result,
            "validation": {
                "is_valid": validation_result.is_valid,
                "warnings": validation_result.warnings,
                "suggestions": validation_result.suggestions
            }
        }
    else:
        return {
            "filters": {},
            "intelligence": intelligence_result,
            "validation": {
                "is_valid": False,
                "warnings": ["No filters could be generated from the input"],
                "suggestions": ["Try using more specific terms like priorities, dates, or states"]
            }
        }

# Generic priority and filtering functions to replace individual table tools

def _build_priority_filter(priorities: List[str]) -> str:
    """Helper function to build OR-based priority filter with cognitive complexity < 15."""
    if not priorities:
        return ""
    
    # Handle single priority
    if len(priorities) == 1:
        return f"priority={encode_query_value(priorities[0])}"

    # Build OR filter for multiple priorities. The "^OR" join is ours; each
    # priority is a terminal value.
    priority_filters = [f"priority={encode_query_value(p)}" for p in priorities]
    return "^OR".join(priority_filters)

def _build_url_with_params(table_name: str, fields: List[str], query: str) -> str:
    """Helper function to build ServiceNow API URL with cognitive complexity < 15."""
    base_url = f"{NWS_API_BASE}/api/now/table/{table_name}"
    field_param = f"sysparm_fields={','.join(fields)}"
    query_param = f"sysparm_query={query}"
    
    return f"{base_url}?{field_param}&{query_param}"

def _build_additional_filters(additional_filters: Optional[Dict[str, str]]) -> List[str]:
    """Convert additional_filters dict into a list of filter strings.

    The second filter-assembly path (the first is `_build_query_string`), so it
    escapes its values the same way — and it has to repeat the guards, because it
    does not route through `_build_query_condition` and so reaches none of them.
    That gap was live: `get_priority_incidents(additional_filters={"_date_range":
    "1^NQstate=99"})` sent the reset to ServiceNow verbatim, past a release whose
    whole claim was that it refuses exactly that.

    `_date_range` is the one fragment key here: pre-built, complete with its
    operators, and legitimately containing `^` (`build_date_filter` emits
    `sys_created_on>=A^sys_created_on<=B`). So it gets the fragment guard, not
    escaping.
    """
    if not additional_filters:
        return []
    result = []
    for field, value in additional_filters.items():
        if field == "_date_range":
            # Pre-built date filter string (e.g., "sys_created_on>=2026-01-01 00:00:00")
            _reject_unsafe_fragment(value)
            result.append(value)
        else:
            _reject_unsafe_field_name(field)
            _reject_new_query_reset(value)
            result.append(f"{field}={encode_query_value(value)}")
    return result


def _format_priority_results(all_results: list, max_results: int) -> Dict[str, Any]:
    """Format paginated results into a standard response dict."""
    if not all_results:
        return {"result": [], "message": NO_RECORDS_FOUND}
    result_count = len(all_results)
    limit_note = f" (limited to {max_results})" if result_count == max_results else ""
    return {
        "result": all_results,
        "message": f"Found {result_count} records{limit_note}"
    }


async def get_records_by_priority(
    table_name: str,
    priorities: List[str],
    additional_filters: Optional[Dict[str, str]] = None,
    detailed: bool = False
) -> Dict[str, Any]:
    """Generic function to get records by priority for any table that supports priority."""
    from constants import TABLE_CONFIGS

    # Validate table supports priority
    table_config = TABLE_CONFIGS.get(table_name)
    if not table_config or not table_config.get("priority_field"):
        return {"error": TABLE_NO_PRIORITY_SUPPORT_ERROR.format(table_name=table_name)}

    fields = DETAIL_FIELDS.get(table_name, []) if detailed else ESSENTIAL_FIELDS.get(table_name, [])
    if not fields:
        return {"error": NO_FIELD_CONFIG_ERROR.format(table_name=table_name)}

    # Build priority filter + the additional-filter list. Both escape their
    # values, so both can refuse one.
    try:
        priority_filter = _build_priority_filter(priorities)
        if not priority_filter:
            return {"error": NO_VALID_PRIORITIES_ERROR}
        filters = [priority_filter] + _build_additional_filters(additional_filters)
    except QueryValueError as refusal:
        return refusal.to_error_dict()

    final_query = "^".join(filters)
    base_url = f"{NWS_API_BASE}/api/now/table/{table_name}?sysparm_fields={','.join(fields)}&sysparm_display_value=true"

    if final_query:
        base_url += f"&sysparm_query={final_query}"

    max_results = 100
    try:
        all_results = await _make_paginated_request(base_url, max_results=max_results)
        return _format_priority_results(all_results, max_results)
    except PartialPageReadError as partial:
        return _partial_envelope(_format_priority_results(partial.rows, max_results), partial)
    except ServiceNowRequestError as error:
        # Must precede the bare `except Exception` below, or the typed failure
        # is flattened into the REQUEST_FAILED_ERROR string and the code is lost.
        return error.to_error_dict()
    except Exception as e:
        return {"error": REQUEST_FAILED_ERROR.format(error=str(e))}

async def query_table_with_generic_filters(
    table_name: str,
    filters: Dict[str, str],
    detailed: bool = False
) -> Dict[str, Any]:
    """Generic function to query any table with filters."""
    fields = DETAIL_FIELDS.get(table_name, []) if detailed else ESSENTIAL_FIELDS.get(table_name, [])
    if not fields:
        return {"error": NO_FIELD_CONFIG_ERROR.format(table_name=table_name)}
    
    # Build query via _build_query_string so the ENABLE_COMPLETE_QUERY gate
    # (which can drop a condition to "") doesn't leave a dangling "^^" or
    # leading/trailing "^" in the joined query.
    try:
        query = _build_query_string(filters)
    except QueryValueError as refusal:
        return refusal.to_error_dict()
    base_url = f"{NWS_API_BASE}/api/now/table/{table_name}?sysparm_fields={','.join(fields)}&sysparm_display_value=true"

    if query:
        base_url += f"&sysparm_query={query}"
    
    try:
        # Use pagination to prevent excessive results
        all_results = await _make_paginated_request(base_url, max_results=75)  # Limit generic filters to 75 results
        return _generic_filter_envelope(all_results)
    except PartialPageReadError as partial:
        return _partial_envelope(_generic_filter_envelope(partial.rows), partial)
    except ServiceNowRequestError as error:
        return error.to_error_dict()
    except Exception as e:
        return {"error": REQUEST_FAILED_ERROR.format(error=str(e))}


def _generic_filter_envelope(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Response shape for query_table_with_generic_filters. Empty stays not-found."""
    if not rows:
        return {"result": [], "message": NO_RECORDS_FOUND}
    result_count = len(rows)
    return {
        "result": rows,
        "message": f"Found {result_count} records" + (" (limited to 75)" if result_count == 75 else ""),
    }
