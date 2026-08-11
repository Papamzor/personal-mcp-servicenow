#!/usr/bin/env python3

"""
ServiceNow CMDB (Configuration Management Database) Tools
Provides CI discovery, search, and analysis functionality.
"""

import asyncio
import re
from http_layer import ServiceNowRequestError, make_nws_request, NWS_API_BASE
from filter import QueryValueError, encode_query_value
from utils import extract_keywords
from typing import Any, Dict, Optional, List
from .read_helpers import is_read_failure
from .response import error_response, list_response, record_response
from constants import (
    CI_NUMBER_REQUIRED,
    CI_TYPE_REQUIRED,
    INVALID_CI_TYPE,
    ERROR_SEARCHING_CIS,
    ERROR_SEARCHING_CIS_BY_TYPE,
    ERROR_FINDING_SIMILAR_CIS,
    ERROR_GETTING_CI_TYPES,
    ERROR_QUICK_CI_SEARCH
)

# Default probe order for get_ci_details when no ci_type is given —
# most-specific class first, base cmdb_ci last.
DEFAULT_CI_PROBE_TABLES = [
    "cmdb_ci_server", "cmdb_ci_computer", "cmdb_ci_database",
    "cmdb_ci_hardware", "cmdb_ci_network_gear", "cmdb_ci_service", "cmdb_ci",
]

# A ci_type is interpolated into the REST URL path, so it is validated by
# shape rather than against a static class list. The old static CI_TABLES
# list drifted from real instances and rejected valid common types; a
# genuinely unknown table simply returns no rows. The pattern also stops a
# value like "cmdb_ci_server?sysparm_limit=9999" — which passes a bare
# startswith("cmdb_ci") check — from smuggling query parameters into the path.
#
# Matched with fullmatch(), not match(): Python's `$` also matches immediately
# before a single trailing newline, so match() would accept
# "cmdb_ci_server\n". fullmatch() requires the whole string to be consumed.
_CI_TYPE_PATTERN = re.compile(r'cmdb_ci[a-z0-9_]*')

# ---------------------------------------------------------------------------
# Response contract (v5.0 "Boron" Tier 3.1; read-failure contract v4.4 Tier 0.3).
# Every tool here returns a shape from Table_Tools/response.py — the 16 bare
# strings this module used through v4.5 are gone:
#
#   * Caller errors (missing/invalid ci_type or ci_number, no attribute given)
#     -> error_response("VALIDATION", ...).
#   * A classified read failure -> error.to_error_dict() ({"error": {code, msg}}).
#     `except ServiceNowRequestError` precedes every bare `except Exception`.
#   * A bare `except Exception` -> error_response("INTERNAL", ERROR_* base text).
#   * An empty result set is SUCCESS: list_response([], ...) for the list tools,
#     record_response(None) for the single-record get_ci_details. Deciding empty
#     means "not found" is the caller's call, not the transport's.
#   * Single record -> record_response(...) under `record`, never `result`
#     (kills the result-is-sometimes-a-dict polymorphism at the old :302).
#   * These reads are single-request (sysparm_limit, no pagination), so there is
#     no `partial` shape in this module; `truncated` is len == the limit.
# ---------------------------------------------------------------------------

def _ci_type_error(ci_type: str) -> Optional[str]:
    """Return an error message if ci_type is not a usable cmdb_ci* table, else None.

    Single policy shared by find_cis_by_type, search_cis_by_attributes and
    get_ci_details. Callers must return the message rather than falling back
    to another table: silently querying base cmdb_ci (or every table) returns
    rows the caller did not ask for, with nothing in the response to say so.
    """
    if not _CI_TYPE_PATTERN.fullmatch(ci_type):
        return INVALID_CI_TYPE.format(ci_type=ci_type)
    return None

# Essential fields for CI discovery
ESSENTIAL_CI_FIELDS = [
    "number", "name", "sys_class_name", "operational_status", 
    "install_status", "sys_created_on", "sys_updated_on"
]

# Detailed fields for comprehensive CI information
DETAILED_CI_FIELDS = [
    "number", "name", "sys_class_name", "operational_status", "install_status",
    "ip_address", "serial_number", "model_category", "location", "assigned_to", 
    "assignment_group", "sys_created_on", "sys_updated_on", "short_description",
    "manufacturer", "model_number", "cost_center", "environment"
]

async def find_cis_by_type(ci_type: str, detailed: bool = False) -> Dict[str, Any]:
    """Find all Configuration Items of a specific type/class.

    TABLES: any cmdb_ci* class table.
    SIDE EFFECT: read-only.
    EXAMPLE: list every Linux server configuration item.

    Args:
        ci_type: CI class/table name (e.g., 'cmdb_ci_server', 'cmdb_ci_computer')
        detailed: If True, returns detailed CI information

    Returns:
        Dictionary with CI results or error dict

    ci_type is validated by shape (see _ci_type_error), not against a static
    class list — that list drifted from real instances and rejected valid,
    common types (e.g. cmdb_ci_server). A well-formed but unknown table
    simply yields no results rather than a misleading "invalid type".
    """
    if not ci_type:
        return error_response("VALIDATION", CI_TYPE_REQUIRED)
    type_error = _ci_type_error(ci_type)
    if type_error:
        return error_response("VALIDATION", type_error)

    fields = DETAILED_CI_FIELDS if detailed else ESSENTIAL_CI_FIELDS

    try:
        url = f"{NWS_API_BASE}/api/now/table/{ci_type}?sysparm_fields={','.join(fields)}&sysparm_display_value=true&sysparm_limit=100"
        data = await make_nws_request(url)

        rows = data['result'] if data and data.get('result') else []
        return list_response(rows, truncated=len(rows) >= 100, ci_type=ci_type)

    except ServiceNowRequestError as error:
        # Ahead of the bare except below: a failed read is not "this type has
        # no CIs" (which is now an empty list_response), and the INTERNAL
        # fallback would drop the classified code.
        return error.to_error_dict()
    except Exception:
        return error_response("INTERNAL", ERROR_SEARCHING_CIS_BY_TYPE)

async def search_cis_by_attributes(
    name: Optional[str] = None,
    ip_address: Optional[str] = None, 
    location: Optional[str] = None,
    status: Optional[str] = None,
    ci_type: Optional[str] = None,
    detailed: bool = False
) -> Dict[str, Any]:
    """Search Configuration Items by multiple attributes.

    TABLES: cmdb_ci (or a given cmdb_ci* class).
    SIDE EFFECT: read-only.
    EXAMPLE: configuration items at location Brussels with status installed.

    Args:
        name: CI name/hostname to search for
        ip_address: IP address to search for
        location: Location to filter by
        status: Operational status to filter by  
        ci_type: Specific CI type to search in (optional). Must be a cmdb_ci*
            table name; an unusable value is an error, never a fallback to the
            base cmdb_ci table.
        detailed: If True, returns detailed CI information

    Returns:
        Dictionary with CI results or error dict
    """
    if not any([name, ip_address, location, status]):
        return error_response("VALIDATION", "At least one search attribute must be provided")

    table = "cmdb_ci"
    if ci_type:
        type_error = _ci_type_error(ci_type)
        if type_error:
            return error_response("VALIDATION", type_error)
        table = ci_type

    fields = DETAILED_CI_FIELDS if detailed else ESSENTIAL_CI_FIELDS
    
    # Build query conditions. Each user value is escaped at this boundary and the
    # escaping now SURVIVES: through v4.4.0 the transport unquoted before
    # re-quoting, so the `quote(safe='')` here was undone and a `&` in a CI name
    # still escaped sysparm_query= into a second URL parameter. A `^` is refused
    # outright — no encoding can carry it (see filter/value_encoding.py).
    try:
        query_parts = []
        if name:
            query_parts.append(f"nameLIKE{encode_query_value(name)}")
        if ip_address:
            query_parts.append(f"ip_address={encode_query_value(ip_address)}")
        if location:
            query_parts.append(f"locationLIKE{encode_query_value(location)}")
        if status:
            query_parts.append(f"operational_status={encode_query_value(status)}")
    except QueryValueError as refusal:
        return refusal.to_error_dict()

    query_string = "^".join(query_parts)

    search_criteria = {
        "name": name,
        "ip_address": ip_address,
        "location": location,
        "status": status,
    }

    try:
        url = f"{NWS_API_BASE}/api/now/table/{table}?sysparm_fields={','.join(fields)}&sysparm_query={query_string}&sysparm_display_value=true&sysparm_limit=100"
        data = await make_nws_request(url)

        rows = data['result'] if data and data.get('result') else []
        return list_response(
            rows, truncated=len(rows) >= 100, table=table, search_criteria=search_criteria
        )

    except ServiceNowRequestError as error:
        return error.to_error_dict()
    except Exception:
        return error_response("INTERNAL", ERROR_SEARCHING_CIS)

async def _probe_ci_table(table: str, ci_number: str) -> Optional[Dict[str, Any]]:
    """Fetch a CI by number from one table; return the first row, or None if absent.

    None means "probed this table, the CI is not in it" and nothing else. The
    previous `except Exception: return None` made a failed probe identical to an
    absent CI: under the concurrent gather in `get_ci_details`, a timeout on
    cmdb_ci_server made a server CI look like it lives in the base cmdb_ci table
    — the wrong table, reported confidently. Failures propagate now and
    `get_ci_details` decides what a missing probe means.
    """
    url = (
        f"{NWS_API_BASE}/api/now/table/{table}"
        f"?sysparm_fields={','.join(DETAILED_CI_FIELDS)}"
        f"&sysparm_query=number={encode_query_value(ci_number)}"
        f"&sysparm_display_value=true"
    )
    data = await make_nws_request(url)
    if data and data.get('result'):
        return data['result'][0]
    return None

async def get_ci_details(ci_number: str, ci_type: Optional[str] = None) -> Dict[str, Any]:
    """Get comprehensive details for a specific Configuration Item by number.

    TABLES: probes the cmdb_ci* class tables (most-specific first).
    SIDE EFFECT: read-only.
    EXAMPLE: get all details for configuration item SRV0001234.

    Args:
        ci_number: CI number (e.g., CI0001000)
        ci_type: Specific CI table to search in (optional). When given it is
            the only table searched; an unusable value is an error, never a
            silent fall back to probing every table.

    Returns:
        Dictionary with detailed CI information or error dict

    When ci_type is not given, the candidate tables are probed concurrently
    (bounded) instead of one-at-a-time; the most-specific-first priority is
    preserved by returning the first table (in order) that yields a row. If a
    probe fails before any table yields a row, the failure is returned.
    """
    if not ci_number:
        return error_response("VALIDATION", CI_NUMBER_REQUIRED)

    if ci_type:
        type_error = _ci_type_error(ci_type)
        if type_error:
            return error_response("VALIDATION", type_error)
        tables_to_search = [ci_type]
    else:
        tables_to_search = list(DEFAULT_CI_PROBE_TABLES)

    semaphore = asyncio.Semaphore(3)

    async def _bounded(table: str) -> Optional[Dict[str, Any]]:
        async with semaphore:
            return await _probe_ci_table(table, ci_number)

    # A failed probe ends the lookup rather than counting as absence: every CI
    # also lives in the base cmdb_ci table, so treating a failure as "not in
    # this table" let a timeout on cmdb_ci_server attribute a server to cmdb_ci
    # — the wrong table, reported confidently. An incomplete probe set supports
    # neither "not found anywhere" nor attribution to a less specific table. A
    # failure *after* a hit is irrelevant: the higher-priority table already
    # decided the answer, which is why this loop runs in priority order.
    #
    # return_exceptions keeps the results positional so a failure stays attached
    # to the table it belongs to instead of aborting the whole gather.
    outcomes = await asyncio.gather(
        *(_bounded(table) for table in tables_to_search), return_exceptions=True
    )
    for table, outcome in zip(tables_to_search, outcomes):
        if isinstance(outcome, ServiceNowRequestError):
            return outcome.to_error_dict()
        if isinstance(outcome, QueryValueError):
            # The ci_number itself is unqueryable, so every probe refused it
            # identically. Must precede the BaseException arm below, which would
            # re-raise it out of the tool.
            return outcome.to_error_dict()
        if isinstance(outcome, BaseException):
            # Not a classified read failure — a real bug. Propagate as before
            # rather than silently degrading it to a not-found string.
            raise outcome
        if outcome:
            # Single record under `record`, never `result` — this is the fix for
            # the old result-is-sometimes-a-dict polymorphism.
            return record_response(outcome, ci_table=table, ci_number=ci_number)

    # Probed every candidate table, all answered 200-empty: a genuine miss, not
    # a transport failure. Empty is success; the caller reads record is None.
    return record_response(None, ci_number=ci_number)

def _extract_ci_search_attributes(ci_data: Dict, ci_table: str) -> Dict[str, str]:
    """Extract search attributes from CI data. Complexity: 4"""
    search_attrs = {}

    if ci_data.get('sys_class_name'):
        search_attrs['ci_type'] = ci_table
    if ci_data.get('location') and ci_data['location'] != '':
        search_attrs['location'] = ci_data['location']
    if ci_data.get('operational_status'):
        search_attrs['status'] = ci_data['operational_status']

    return search_attrs

def _filter_and_limit_ci_results(similar_cis: Dict, ci_number: str, limit: int = 20) -> List[Dict]:
    """Filter out original CI and limit results. Complexity: 3"""
    if not isinstance(similar_cis, dict) or not similar_cis.get('result'):
        return []

    filtered_results = [
        ci for ci in similar_cis['result']
        if ci.get('number') != ci_number
    ]

    return filtered_results[:limit]

def _build_similar_ci_response(ci_number: str, search_attrs: Dict, filtered_results: List[Dict]) -> Dict[str, Any]:
    """Build the list-contract response for similar CIs. Complexity: 2"""
    return list_response(
        filtered_results, original_ci=ci_number, similar_criteria=search_attrs
    )

async def similar_cis_for_ci(ci_number: str) -> Dict[str, Any]:
    """Find Configuration Items similar to a given CI, by shared attributes.

    TABLES: cmdb_ci* class tables.
    SIDE EFFECT: read-only.
    EXAMPLE: find configuration items similar to CI0001000.

    Args:
        ci_number: CI number to find similar CIs for

    Returns:
        Dictionary with similar CIs or error dict

    Complexity: 8 (reduced from ~15-17)
    """
    try:
        # The lookup is inside this try, not before it: get_ci_details converts
        # a classified read failure to a dict but re-raises anything else, and a
        # bug in the lookup half should read the same as a bug in the search
        # half rather than escaping to the client from one arm of one function.
        ci_details = await get_ci_details(ci_number)

        # get_ci_details answers with a failure dict (no 'record' key) — pass it
        # through instead of indexing into it.
        if is_read_failure(ci_details):
            return ci_details
        # A seed CI that does not exist (record is None) has no attributes to
        # match on: no similar CIs, reported as an empty list, not an error.
        if ci_details.get("record") is None:
            return list_response([], original_ci=ci_number)

        # Extract key attributes for similarity search
        search_attrs = _extract_ci_search_attributes(
            ci_details['record'], ci_details['ci_table']
        )

        # search_cis_by_attributes requires at least one of name/ip_address/
        # location/status; _extract_ci_search_attributes only ever yields
        # ci_type plus optional location/status. A seed with a class but no
        # location and no operational_status leaves only ci_type, which that
        # tool rejects as VALIDATION. Pre-contract the bare validation string
        # fell through to a soft "no similar CIs"; converting it to a typed
        # error made that a hard failure. A seed with no basis for similarity is
        # an empty list, not an error.
        if not any(k in search_attrs for k in ("name", "ip_address", "location", "status")):
            return list_response([], original_ci=ci_number, similar_criteria=search_attrs)

        similar_cis = await search_cis_by_attributes(**search_attrs, detailed=True)
        # A failed search has no rows to filter. Without this,
        # _filter_and_limit_ci_results returns [] and the caller is told there
        # are no similar CIs for a search that never ran.
        if is_read_failure(similar_cis):
            return similar_cis

        # Filter and limit results
        filtered_results = _filter_and_limit_ci_results(similar_cis, ci_number, limit=20)

        return _build_similar_ci_response(ci_number, search_attrs, filtered_results)

    except ServiceNowRequestError as error:
        # Unreachable on today's call graph, and kept deliberately: both callees
        # above convert a classified failure to a dict rather than raising, so
        # this arm has nothing to catch. It exists so that a later change making
        # either of them propagate cannot silently fall through to the
        # ERROR_FINDING_SIMILAR_CIS string below and drop the code. Decision (e)
        # of the Tier 0.3 contract asks for the arm in every function touched.
        return error.to_error_dict()
    except Exception:
        return error_response("INTERNAL", ERROR_FINDING_SIMILAR_CIS)

async def get_all_ci_types() -> Dict[str, Any]:
    """Get all available CI types/classes in the CMDB.

    TABLES: sys_db_object (live class list).
    SIDE EFFECT: read-only.
    EXAMPLE: which CI classes exist in this CMDB.

    Returns:
        Dictionary of the CI classes this instance actually has.

    This is a live ``sys_db_object`` query, not a static list — it is the only
    discovery path for the classes a given instance defines.

    Note: ``sys_db_object.number_ref`` is a reference to the table's numbering
    configuration, NOT a row count. It was previously surfaced as
    ``record_count``, which invited callers to treat an unrelated reference as
    a population figure. The Table API returns no row count here; use
    ``find_cis_by_type(ci_type)`` and read ``returned_count`` if you need one.
    """
    try:
        # Query sys_db_object to get all tables that extend cmdb_ci
        url = f"{NWS_API_BASE}/api/now/table/sys_db_object?sysparm_query=super_class.name=cmdb_ci^ORname=cmdb_ci&sysparm_fields=name,label,number_ref"
        data = await make_nws_request(url)

        ci_types = []
        for table_info in (data['result'] if data and data.get('result') else []):
            table_name = table_info.get('name')
            if table_name and table_name.startswith('cmdb_ci'):
                ci_types.append({
                    "table_name": table_name,
                    "display_name": table_info.get('label', table_name),
                    "number_prefix_ref": table_info.get('number_ref', 'Unknown')
                })

        return list_response(sorted(ci_types, key=lambda x: x['table_name']))

    except ServiceNowRequestError as error:
        return error.to_error_dict()
    except Exception:
        return error_response("INTERNAL", ERROR_GETTING_CI_TYPES)

# Convenience function for quick CI search
async def quick_ci_search(search_term: str) -> Dict[str, Any]:
    """Quick search for CIs by name, IP, or number (OR across all three).

    TABLES: cmdb_ci (base).
    SIDE EFFECT: read-only.
    EXAMPLE: quickly find a CI by name, IP, or number.

    Args:
        search_term: Term to search for in CI name, IP, or number fields
    
    Returns:
        Dictionary with CI results or error dict
    """
    try:
        # Try multiple search approaches. The term is escaped at this boundary
        # and the escaping survives the transport (v4.4.1); a term containing '^'
        # is refused instead of silently becoming extra conditions.
        safe_term = encode_query_value(search_term)
        query_parts = [
            f"nameLIKE{safe_term}",
            f"ip_address={safe_term}",
            f"number={safe_term}"
        ]

        query_string = "^OR".join(query_parts)
        url = f"{NWS_API_BASE}/api/now/table/cmdb_ci?sysparm_fields={','.join(ESSENTIAL_CI_FIELDS)}&sysparm_query={query_string}&sysparm_display_value=true&sysparm_limit=50"
        data = await make_nws_request(url)

        rows = data['result'] if data and data.get('result') else []
        return list_response(rows, truncated=len(rows) >= 50, search_term=search_term)

    except QueryValueError as refusal:
        # Ahead of the bare except below, for the same reason
        # ServiceNowRequestError is: ERROR_QUICK_CI_SEARCH would replace the
        # explanation of what about the term is unqueryable with a generic string.
        return refusal.to_error_dict()
    except ServiceNowRequestError as error:
        return error.to_error_dict()
    except Exception:
        return error_response("INTERNAL", ERROR_QUICK_CI_SEARCH)