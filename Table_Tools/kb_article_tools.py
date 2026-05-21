from service_now_api_oauth import make_nws_request, NWS_API_BASE
from typing import Any, Dict
import httpx
from constants import (
    ERROR_KB_NO_UPDATE_DATA,
    ERROR_KB_ARTICLE_NOT_FOUND_OP,
    ERROR_KB_ARTICLE_REQUEST_FAILED,
    ERROR_KB_ARTICLE_AUTH_FAILED,
    ERROR_KB_ARTICLE_ACCESS_DENIED,
    ERROR_KB_ARTICLE_INVALID_REQUEST,
    ERROR_KB_ARTICLE_NOT_FOUND,
    ERROR_KB_ARTICLE_SERVER_ERROR,
    KB_WRITE_RESPONSE_FIELDS,
)


def _handle_kb_error(error: httpx.HTTPStatusError, operation: str) -> str:
    status_code = error.response.status_code
    try:
        detail = error.response.json()
    except Exception:
        detail = error.response.text
    error_messages = {
        401: ERROR_KB_ARTICLE_AUTH_FAILED.format(operation=operation),
        403: ERROR_KB_ARTICLE_ACCESS_DENIED.format(operation=operation),
        400: f"{ERROR_KB_ARTICLE_INVALID_REQUEST.format(operation=operation)}: {detail}",
        404: ERROR_KB_ARTICLE_NOT_FOUND.format(operation=operation),
    }
    return error_messages.get(status_code, f"{ERROR_KB_ARTICLE_SERVER_ERROR.format(operation=operation)}: {detail}")


def _unwrap_kb_write_response(result: Any, operation: str) -> Dict[str, Any] | str:
    if result and isinstance(result, dict) and result.get('result'):
        record = result['result']
        if isinstance(record, dict):
            return {k: v for k, v in record.items() if k in KB_WRITE_RESPONSE_FIELDS}
        return record
    return result if result else f"Knowledge article {operation} successful but no data returned."


async def _write_kb_article(
    method: str,
    url: str,
    payload: Dict[str, Any],
    operation: str,
) -> Dict[str, Any] | str:
    try:
        result = await make_nws_request(url, method=method, json_data=payload)
    except httpx.HTTPStatusError as e:
        return _handle_kb_error(e, operation)
    except Exception:
        return ERROR_KB_ARTICLE_REQUEST_FAILED.format(operation=operation)
    return _unwrap_kb_write_response(result, operation)


async def _get_kb_article_sys_id(article_number: str) -> str | None:
    url = f"{NWS_API_BASE}/api/now/table/kb_knowledge?sysparm_fields=sys_id&sysparm_query=number={article_number}"
    data = await make_nws_request(url)
    if not data or not data.get('result') or not data['result']:
        return None
    return data['result'][0]['sys_id']


async def _get_kb_article_meta(article_number: str) -> Dict[str, Any] | None:
    """Fetch sys_id + short_description in one GET — avoids a second round-trip in publish."""
    url = (
        f"{NWS_API_BASE}/api/now/table/kb_knowledge"
        f"?sysparm_fields=sys_id,short_description"
        f"&sysparm_query=number={article_number}"
    )
    data = await make_nws_request(url)
    if not data or not data.get('result') or not data['result']:
        return None
    return data['result'][0]


async def _check_kb_duplicates(short_description: str, exclude_number: str) -> list:
    """Return KB articles matching short_description exactly across ALL workflow states.

    Queries with CONTAINS then exact-matches in Python so the check catches
    drafts, published, and retired articles — not just active ones.
    Excludes the article being published (exclude_number) from results.
    """
    url = (
        f"{NWS_API_BASE}/api/now/table/kb_knowledge"
        f"?sysparm_fields=number,short_description,workflow_state,sys_created_on,kb_category"
        f"&sysparm_query=short_descriptionCONTAINS{short_description}"
    )
    data = await make_nws_request(url)
    if not data or not data.get('result'):
        return []
    needle = short_description.strip().lower()
    return [
        r for r in data['result']
        if r.get('short_description', '').strip().lower() == needle
        and r.get('number') != exclude_number
    ]


async def _call_kb_workflow(sys_id: str, action: str) -> Dict[str, Any] | str:
    # Custom Scripted REST API (qonv/publish) — invokes KnowledgeUIAction server-side.
    # Direct Table API writes to workflow_state are ignored by ServiceNow.
    url = f"{NWS_API_BASE}/api/qonv/mateco_knowledge/articles/{sys_id}/{action}"
    result = await _write_kb_article("POST", url, {}, action)
    if isinstance(result, str):
        return f"{result} [url={url}]"
    return result


async def update_knowledge_article(article_number: str, update_data: Dict[str, Any]) -> Dict[str, Any] | str:
    """Update fields on a knowledge article by article number (e.g. KB0001234).

    Args:
        article_number: The KB article number.
        update_data: Fields to update (e.g. short_description, text, kb_category).

    Returns:
        Updated article record dict, or error string on failure.
    """
    if not update_data:
        return ERROR_KB_NO_UPDATE_DATA
    sys_id = await _get_kb_article_sys_id(article_number)
    if not sys_id:
        return ERROR_KB_ARTICLE_NOT_FOUND_OP.format(number=article_number)
    fields = ",".join(KB_WRITE_RESPONSE_FIELDS)
    url = f"{NWS_API_BASE}/api/now/table/kb_knowledge/{sys_id}?sysparm_fields={fields}"
    return await _write_kb_article("PATCH", url, update_data, "update")


async def publish_knowledge_article(article_number: str) -> Dict[str, Any] | str:
    """Publish a knowledge article via the ServiceNow workflow endpoint.

    Runs a duplicate check across all workflow states before publishing.
    Returns early with a list of duplicates if any are found.

    Args:
        article_number: The KB article number (e.g. KB0001234).

    Returns:
        Updated article record dict, duplicate warning dict, or error string on failure.
    """
    meta = await _get_kb_article_meta(article_number)
    if not meta:
        return ERROR_KB_ARTICLE_NOT_FOUND_OP.format(number=article_number)

    duplicates = await _check_kb_duplicates(meta['short_description'], article_number)
    if duplicates:
        return {
            "success": False,
            "message": "Duplicate KB article(s) found. Resolve before publishing.",
            "duplicates": duplicates,
        }

    return await _call_kb_workflow(meta['sys_id'], "publish")


async def retire_knowledge_article(article_number: str) -> Dict[str, Any] | str:
    """Retire a knowledge article via the ServiceNow workflow endpoint.

    Args:
        article_number: The KB article number (e.g. KB0001234).

    Returns:
        Updated article record dict, or error string on failure.
    """
    sys_id = await _get_kb_article_sys_id(article_number)
    if not sys_id:
        return ERROR_KB_ARTICLE_NOT_FOUND_OP.format(number=article_number)
    return await _call_kb_workflow(sys_id, "retire")
