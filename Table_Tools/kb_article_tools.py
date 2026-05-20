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
)


def _handle_kb_error(error: httpx.HTTPStatusError, operation: str) -> str:
    status_code = error.response.status_code
    error_messages = {
        401: ERROR_KB_ARTICLE_AUTH_FAILED.format(operation=operation),
        403: ERROR_KB_ARTICLE_ACCESS_DENIED.format(operation=operation),
        400: ERROR_KB_ARTICLE_INVALID_REQUEST.format(operation=operation),
        404: ERROR_KB_ARTICLE_NOT_FOUND.format(operation=operation),
    }
    return error_messages.get(status_code, ERROR_KB_ARTICLE_SERVER_ERROR.format(operation=operation))


def _unwrap_kb_write_response(result: Any, operation: str) -> Dict[str, Any] | str:
    if result and isinstance(result, dict) and result.get('result'):
        return result['result']
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
    url = f"{NWS_API_BASE}/api/now/table/kb_knowledge/{sys_id}"
    return await _write_kb_article("PATCH", url, update_data, "update")


async def publish_knowledge_article(article_number: str) -> Dict[str, Any] | str:
    """Publish a knowledge article (workflow_state → published).

    Args:
        article_number: The KB article number (e.g. KB0001234).

    Returns:
        Updated article record dict, or error string on failure.
    """
    sys_id = await _get_kb_article_sys_id(article_number)
    if not sys_id:
        return ERROR_KB_ARTICLE_NOT_FOUND_OP.format(number=article_number)
    url = f"{NWS_API_BASE}/api/now/table/kb_knowledge/{sys_id}"
    return await _write_kb_article("PATCH", url, {"workflow_state": "published"}, "publish")


async def retire_knowledge_article(article_number: str) -> Dict[str, Any] | str:
    """Retire a knowledge article (workflow_state → retired).

    Args:
        article_number: The KB article number (e.g. KB0001234).

    Returns:
        Updated article record dict, or error string on failure.
    """
    sys_id = await _get_kb_article_sys_id(article_number)
    if not sys_id:
        return ERROR_KB_ARTICLE_NOT_FOUND_OP.format(number=article_number)
    url = f"{NWS_API_BASE}/api/now/table/kb_knowledge/{sys_id}"
    return await _write_kb_article("PATCH", url, {"workflow_state": "retired"}, "retire")
