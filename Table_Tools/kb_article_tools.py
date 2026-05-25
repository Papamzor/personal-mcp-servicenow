import asyncio
from service_now_api_oauth import make_nws_request, NWS_API_BASE
from typing import Any, Dict, List
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
    KB_DUPLICATE_IGNORED_STATES,
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


async def _get_kb_article_sys_id(article_number: str, workflow_state: str | None = None) -> str | None:
    query = f"number={article_number}"
    if workflow_state:
        query += f"^workflow_state={workflow_state}"
    url = f"{NWS_API_BASE}/api/now/table/kb_knowledge?sysparm_fields=sys_id&sysparm_query={query}"
    data = await make_nws_request(url)
    if not data or not data.get('result') or not data['result']:
        return None
    return data['result'][0]['sys_id']


async def _get_kb_article_meta(article_number: str, workflow_state: str | None = None) -> Dict[str, Any] | None:
    """Fetch sys_id + short_description in one GET — avoids a second round-trip in publish."""
    query = f"number={article_number}"
    if workflow_state:
        query += f"^workflow_state={workflow_state}"
    url = (
        f"{NWS_API_BASE}/api/now/table/kb_knowledge"
        f"?sysparm_fields=sys_id,short_description"
        f"&sysparm_query={query}"
    )
    data = await make_nws_request(url)
    if not data or not data.get('result') or not data['result']:
        return None
    return data['result'][0]


async def _check_kb_duplicates(short_description: str, exclude_number: str) -> list:
    """Return KB articles matching short_description exactly across live workflow states.

    Queries with CONTAINS then exact-matches in Python so the check catches
    drafts, review, and published articles. Retired + outdated articles are
    skipped — retired = explicitly killed, outdated = prior version after a newer
    publish (ServiceNow versioning artefact). Excludes the article being published
    (exclude_number) from results.
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
        and r.get('workflow_state', '').strip().lower() not in KB_DUPLICATE_IGNORED_STATES
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
    sys_id = await _get_kb_article_sys_id(article_number, workflow_state="draft")
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
    meta = await _get_kb_article_meta(article_number, workflow_state="draft")
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


async def _check_single_kb_duplicate(article_number: str) -> Dict[str, Any]:
    """Lookup meta then check duplicates for one article. Used by check_kb_duplicates fan-out."""
    meta = await _get_kb_article_meta(article_number)
    if not meta:
        return {
            "number": article_number,
            "has_duplicate": False,
            "duplicates": [],
            "error": ERROR_KB_ARTICLE_NOT_FOUND_OP.format(number=article_number),
        }
    duplicates = await _check_kb_duplicates(meta["short_description"], article_number)
    return {
        "number": article_number,
        "has_duplicate": bool(duplicates),
        "duplicates": [
            {"number": d.get("number"), "workflow_state": d.get("workflow_state")}
            for d in duplicates
        ],
    }


async def check_kb_duplicates(
    article_numbers: List[str],
    concurrency: int = 5,
) -> Dict[str, Any]:
    """Check for duplicate KB articles without publishing.

    For each number: looks up short_description, then finds matching live KB
    articles (draft / review / published). Retired + outdated states are
    skipped. Lets the caller resolve all conflicts upfront before running a
    publish loop.

    Args:
        article_numbers: List of KB article numbers (e.g. ["KB0001234", ...]).
            Capped at 50 per call to keep response size bounded.
        concurrency: Max concurrent ServiceNow round-trips. Default 5.

    Returns:
        {"result": [{"number", "has_duplicate", "duplicates": [{"number", "workflow_state"}], "error"?}, ...]}
    """
    if not article_numbers:
        return {"result": []}
    if len(article_numbers) > 50:
        return {"error": "check_kb_duplicates accepts at most 50 article numbers per call."}

    semaphore = asyncio.Semaphore(max(1, concurrency))

    async def _bounded(num: str) -> Dict[str, Any]:
        async with semaphore:
            return await _check_single_kb_duplicate(num)

    results = await asyncio.gather(*(_bounded(n) for n in article_numbers))
    return {"result": results}


def _normalize_publish_result(article_number: str, result: Dict[str, Any] | str) -> Dict[str, Any]:
    """Normalize publish_knowledge_article output into a flat batch-result row."""
    if isinstance(result, str):
        return {"number": article_number, "status": "error", "message": result}
    if isinstance(result, dict) and result.get("success") is False:
        return {
            "number": article_number,
            "status": "blocked",
            "message": result.get("message"),
            "blockers": result.get("duplicates", []),
        }
    workflow_state = result.get("workflow_state") if isinstance(result, dict) else None
    return {"number": article_number, "status": "published", "workflow_state": workflow_state}


async def publish_knowledge_articles(
    article_numbers: List[str],
    concurrency: int = 5,
) -> Dict[str, Any]:
    """Publish multiple KB articles in one tool call.

    Runs full publish flow per article (meta lookup → duplicate check →
    ServiceNow workflow POST). Returns a flat status row per article so
    failures and duplicate blocks do not abort the rest of the batch.

    Args:
        article_numbers: KB numbers to publish. Capped at 20 per call.
        concurrency: Max concurrent ServiceNow round-trips. Default 5.

    Returns:
        {"result": [{"number", "status": "published"|"blocked"|"error", ...}, ...]}
    """
    if not article_numbers:
        return {"result": []}
    if len(article_numbers) > 20:
        return {"error": "publish_knowledge_articles accepts at most 20 article numbers per call."}

    semaphore = asyncio.Semaphore(max(1, concurrency))

    async def _bounded(num: str) -> Dict[str, Any]:
        async with semaphore:
            outcome = await publish_knowledge_article(num)
            return _normalize_publish_result(num, outcome)

    results = await asyncio.gather(*(_bounded(n) for n in article_numbers))
    return {"result": results}


async def retire_knowledge_article(article_number: str) -> Dict[str, Any] | str:
    """Retire a knowledge article via the ServiceNow workflow endpoint.

    Args:
        article_number: The KB article number (e.g. KB0001234).

    Returns:
        Updated article record dict, or error string on failure.
    """
    sys_id = await _get_kb_article_sys_id(article_number, workflow_state="published")
    if not sys_id:
        return ERROR_KB_ARTICLE_NOT_FOUND_OP.format(number=article_number)
    return await _call_kb_workflow(sys_id, "retire")
