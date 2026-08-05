#!/usr/bin/env python3

"""
ServiceNow CMDB (Configuration Management Database) Tools
Provides CI discovery, search, and analysis functionality.
"""

import asyncio
import re
from urllib.parse import quote
from http_layer import ServiceNowRequestError, make_nws_request, NWS_API_BASE
from utils import extract_keywords
from typing import Any, Dict, Optional, List
from .read_helpers import is_read_failure
from constants import (
    NO_CIS_FOUND_FOR_TYPE,
    NO_CIS_FOUND_MATCHING_CRITERIA,
    CI_NOT_FOUND,
    CI_NUMBER_REQUIRED,
    CI_TYPE_REQUIRED,
    INVALID_CI_TYPE,
    NO_SIMILAR_CIS_FOUND,
    NO_CI_TYPES_FOUND,
    NO_CIS_FOUND_FOR_SEARCH,
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
# Read-failure contract (v4.4 Tier 0.3). This module is in
# `http_layer.request_dispatcher._TYPED_CALLERS`, so a failed GET raises
# `ServiceNowRequestError` instead of returning None. Rules, as settled in the
# generic_table_tools migration:
#
#   * A raise returns `error.to_error_dict()` -> {"error": {code, message}}.
#     Every other return here is a bare string; the union is deliberate and
#     temporary (Tier 3.1 removes all 16 strings). Inventing an error *string*
#     to keep the return type uniform would ship a lie to preserve tidiness.
#   * An empty result set keeps its existing not-found string. Empty is success.
#   * `except ServiceNowRequestError` precedes every bare `except Exception`,
#     or the ERROR_* string swallows the code.
#   * These reads are single-request (sysparm_limit, no pagination), so there is
#     no `partial` shape in this module.
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

async def find_cis_by_type(ci_type: str, detailed: bool = False) -> dict[str, Any] | str:
    """
    Find all Configuration Items of a specific type.

    Args:
        ci_type: CI class/table name (e.g., 'cmdb_ci_server', 'cmdb_ci_computer')
        detailed: If True, returns detailed CI information

    Returns:
        Dictionary with CI results or error string

    ci_type is validated by shape (see _ci_type_error), not against a static
    class list — that list drifted from real instances and rejected valid,
    common types (e.g. cmdb_ci_server). A well-formed but unknown table
    simply yields no results rather than a misleading "invalid type".
    """
    if not ci_type:
        return CI_TYPE_REQUIRED
    type_error = _ci_type_error(ci_type)
    if type_error:
        return type_error

    fields = DETAILED_CI_FIELDS if detailed else ESSENTIAL_CI_FIELDS
    
    try:
        url = f"{NWS_API_BASE}/api/now/table/{ci_type}?sysparm_fields={','.join(fields)}&sysparm_display_value=true&sysparm_limit=100"
        data = await make_nws_request(url)
        
        if data and data.get('result'):
            return {
                "ci_type": ci_type,
                "count": len(data['result']),
                "result": data['result']
            }
        return NO_CIS_FOUND_FOR_TYPE.format(ci_type=ci_type)

    except ServiceNowRequestError as error:
        # Ahead of the bare except below: a failed read is not "this type has
        # no CIs", and ERROR_SEARCHING_CIS_BY_TYPE would drop the code.
        return error.to_error_dict()
    except Exception:
        return ERROR_SEARCHING_CIS_BY_TYPE

async def search_cis_by_attributes(
    name: Optional[str] = None,
    ip_address: Optional[str] = None, 
    location: Optional[str] = None,
    status: Optional[str] = None,
    ci_type: Optional[str] = None,
    detailed: bool = False
) -> dict[str, Any] | str:
    """
    Search Configuration Items by multiple attributes.
    
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
        Dictionary with CI results or error string
    """
    if not any([name, ip_address, location, status]):
        return "At least one search attribute must be provided"

    table = "cmdb_ci"
    if ci_type:
        type_error = _ci_type_error(ci_type)
        if type_error:
            return type_error
        table = ci_type

    fields = DETAILED_CI_FIELDS if detailed else ESSENTIAL_CI_FIELDS
    
    # Build query conditions. User values are percent-encoded (safe='') so
    # structural characters (#, +, %, ?, ...) in a name/location don't corrupt
    # the sysparm_query. (Operator chars in the locked encode safe-set —
    # & ^ = etc. — still pass through and remain unsupported inside values.)
    query_parts = []
    if name:
        query_parts.append(f"nameLIKE{quote(name, safe='')}")
    if ip_address:
        query_parts.append(f"ip_address={quote(ip_address, safe='')}")
    if location:
        query_parts.append(f"locationLIKE{quote(location, safe='')}")
    if status:
        query_parts.append(f"operational_status={quote(status, safe='')}")
    
    query_string = "^".join(query_parts)
    
    try:
        url = f"{NWS_API_BASE}/api/now/table/{table}?sysparm_fields={','.join(fields)}&sysparm_query={query_string}&sysparm_display_value=true&sysparm_limit=100"
        data = await make_nws_request(url)
        
        if data and data.get('result'):
            return {
                "table": table,
                "search_criteria": {
                    "name": name,
                    "ip_address": ip_address,
                    "location": location,
                    "status": status
                },
                "count": len(data['result']),
                "result": data['result']
            }
        return NO_CIS_FOUND_MATCHING_CRITERIA

    except ServiceNowRequestError as error:
        return error.to_error_dict()
    except Exception:
        return ERROR_SEARCHING_CIS

async def _probe_ci_table(table: str, ci_number: str) -> Optional[Dict[str, Any]]:
    """Fetch a CI by number from one table; return the first row, or None if absent.

    None means "probed this table, the CI is not in it" and nothing else. The
    previous `except Exception: return None` made a failed probe identical to an
    absent CI: under the concurrent gather in `get_ci_details`, a timeout on
    cmdb_ci_server made a server CI look like it lives in the base cmdb_ci table
    — the wrong table, reported confidently. Failures propagate now and
    `get_ci_details` decides what a missing probe means.
    """
    url = f"{NWS_API_BASE}/api/now/table/{table}?sysparm_fields={','.join(DETAILED_CI_FIELDS)}&sysparm_query=number={ci_number}&sysparm_display_value=true"
    data = await make_nws_request(url)
    if data and data.get('result'):
        return data['result'][0]
    return None


async def get_ci_details(ci_number: str, ci_type: Optional[str] = None) -> dict[str, Any] | str:
    """
    Get comprehensive details for a specific Configuration Item.

    Args:
        ci_number: CI number (e.g., CI0001000)
        ci_type: Specific CI table to search in (optional). When given it is
            the only table searched; an unusable value is an error, never a
            silent fall back to probing every table.

    Returns:
        Dictionary with detailed CI information or error string

    When ci_type is not given, the candidate tables are probed concurrently
    (bounded) instead of one-at-a-time; the most-specific-first priority is
    preserved by returning the first table (in order) that yields a row. If a
    probe fails before any table yields a row, the failure is returned.
    """
    if not ci_number:
        return CI_NUMBER_REQUIRED

    if ci_type:
        type_error = _ci_type_error(ci_type)
        if type_error:
            return type_error
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
        if isinstance(outcome, BaseException):
            # Not a classified read failure — a real bug. Propagate as before
            # rather than silently degrading it to a not-found string.
            raise outcome
        if outcome:
            return {
                "ci_table": table,
                "ci_number": ci_number,
                "result": outcome,
            }

    return CI_NOT_FOUND.format(ci_number=ci_number)

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
    """Build response for similar CIs. Complexity: 2"""
    return {
        "original_ci": ci_number,
        "similar_criteria": search_attrs,
        "count": len(filtered_results),
        "result": filtered_results
    }

async def similar_cis_for_ci(ci_number: str) -> dict[str, Any] | str:
    """
    Find Configuration Items similar to the specified CI based on attributes.

    Args:
        ci_number: CI number to find similar CIs for

    Returns:
        Dictionary with similar CIs or error string

    Complexity: 8 (reduced from ~15-17)
    """
    try:
        # The lookup is inside this try, not before it: get_ci_details converts
        # a classified read failure to a dict but re-raises anything else, and a
        # bug in the lookup half should read the same as a bug in the search
        # half rather than escaping to the client from one arm of one function.
        ci_details = await get_ci_details(ci_number)

        if isinstance(ci_details, str):
            return ci_details
        # get_ci_details can now answer with a failure dict, which has no
        # 'result' key — pass it through instead of indexing into it.
        if is_read_failure(ci_details):
            return ci_details

        # Extract key attributes for similarity search
        search_attrs = _extract_ci_search_attributes(
            ci_details['result'], ci_details['ci_table']
        )

        similar_cis = await search_cis_by_attributes(**search_attrs, detailed=True)
        # A failed search has no rows to filter. Without this,
        # _filter_and_limit_ci_results returns [] and the caller is told there
        # are no similar CIs for a search that never ran.
        if is_read_failure(similar_cis):
            return similar_cis

        # Filter and limit results
        filtered_results = _filter_and_limit_ci_results(similar_cis, ci_number, limit=20)

        if filtered_results:
            return _build_similar_ci_response(ci_number, search_attrs, filtered_results)

        return NO_SIMILAR_CIS_FOUND.format(ci_number=ci_number)

    except ServiceNowRequestError as error:
        return error.to_error_dict()
    except Exception:
        return ERROR_FINDING_SIMILAR_CIS

async def get_all_ci_types() -> dict[str, Any] | str:
    """
    Get all available CI types/classes in the CMDB.
    
    Returns:
        Dictionary of the CI classes this instance actually has.

    This is a live ``sys_db_object`` query, not a static list — it is the only
    discovery path for the classes a given instance defines.

    Note: ``sys_db_object.number_ref`` is a reference to the table's numbering
    configuration, NOT a row count. It was previously surfaced as
    ``record_count``, which invited callers to treat an unrelated reference as
    a population figure. The Table API returns no row count here; use
    ``find_cis_by_type(ci_type)`` and read ``count`` if you need one.
    """
    try:
        # Query sys_db_object to get all tables that extend cmdb_ci
        url = f"{NWS_API_BASE}/api/now/table/sys_db_object?sysparm_query=super_class.name=cmdb_ci^ORname=cmdb_ci&sysparm_fields=name,label,number_ref"
        data = await make_nws_request(url)

        if data and data.get('result'):
            ci_types = []
            for table_info in data['result']:
                table_name = table_info.get('name')
                if table_name and table_name.startswith('cmdb_ci'):
                    ci_types.append({
                        "table_name": table_name,
                        "display_name": table_info.get('label', table_name),
                        "number_prefix_ref": table_info.get('number_ref', 'Unknown')
                    })
            
            return {
                "total_ci_types": len(ci_types),
                "ci_types": sorted(ci_types, key=lambda x: x['table_name'])
            }
        
        return NO_CI_TYPES_FOUND

    except ServiceNowRequestError as error:
        return error.to_error_dict()
    except Exception:
        return ERROR_GETTING_CI_TYPES

# Convenience function for quick CI search
async def quick_ci_search(search_term: str) -> dict[str, Any] | str:
    """
    Quick search for CIs by name, IP, or number.
    
    Args:
        search_term: Term to search for in CI name, IP, or number fields
    
    Returns:
        Dictionary with CI results or error string
    """
    try:
        # Try multiple search approaches. Percent-encode the term so special
        # characters in it don't corrupt the sysparm_query structure.
        safe_term = quote(search_term, safe='')
        query_parts = [
            f"nameLIKE{safe_term}",
            f"ip_address={safe_term}",
            f"number={safe_term}"
        ]

        query_string = "^OR".join(query_parts)
        url = f"{NWS_API_BASE}/api/now/table/cmdb_ci?sysparm_fields={','.join(ESSENTIAL_CI_FIELDS)}&sysparm_query={query_string}&sysparm_display_value=true&sysparm_limit=50"
        data = await make_nws_request(url)
        
        if data and data.get('result'):
            return {
                "search_term": search_term,
                "count": len(data['result']),
                "result": data['result']
            }
        
        return NO_CIS_FOUND_FOR_SEARCH.format(search_term=search_term)

    except ServiceNowRequestError as error:
        return error.to_error_dict()
    except Exception:
        return ERROR_QUICK_CI_SEARCH