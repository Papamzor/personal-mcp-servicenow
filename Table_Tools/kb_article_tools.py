"""Knowledge-article reads and writes.

Read-failure contract (v4.4 Tier 0.3). A failed GET raises
`ServiceNowRequestError` rather than returning None:

  * A raise surfaces as `error.to_error_dict()` -> {"error": {code, message}}.
  * An empty result set keeps its existing not-found message. Empty is success.
  * The pre-write `sys_id` / meta reads return None ONLY for a genuinely absent
    article. A failed read propagates, so a write never again reports "article
    not found" because the lookup timed out (decision (d)).

The publish guard is FAIL-CLOSED. `_check_kb_duplicates` has three outcomes, not
two — clear, duplicates-found, and inconclusive — and only *clear* permits a
publish. Before v4.4 a failed duplicate-check read returned `[]`, which read as
a clean bill of health, and the article published with the guard silently
skipped. "Could not check" is not "nothing found".
"""
import asyncio
import sys
import time
from http_layer import ServiceNowRequestError, make_nws_request, NWS_API_BASE
from filter import QueryValueError, encode_query_value
from typing import Any, Dict, List, Optional
import anyio
import httpx
import structlog
from .read_helpers import is_read_failure
from .write_helpers import map_http_error, unwrap_write_response
from param_coercion import JsonList
from constants import (
    ERROR_KB_NO_UPDATE_DATA,
    ERROR_KB_ARTICLE_NOT_FOUND_OP,
    ERROR_KB_ARTICLE_REQUEST_FAILED,
    ERROR_KB_ARTICLE_AUTH_FAILED,
    ERROR_KB_ARTICLE_ACCESS_DENIED,
    ERROR_KB_ARTICLE_INVALID_REQUEST,
    ERROR_KB_ARTICLE_NOT_FOUND,
    ERROR_KB_ARTICLE_SERVER_ERROR,
    ERROR_KB_PUBLISH_NOT_CONFIRMED,
    ERROR_KB_WRITE_UNCONFIRMED,
    ERROR_KB_DUPLICATE_CHECK_INCONCLUSIVE,
    ERROR_KB_PUBLISH_VERIFY_UNREADABLE,
    KB_DEDUP_QUERY_LIMIT,
    KB_DEDUP_REASON_TRUNCATED,
    KB_DEDUP_REASON_UNSAFE_CHARS,
    KB_QUERY_UNSAFE_CHARS,
    KB_WRITE_RESPONSE_FIELDS,
    KB_META_FIELDS,
    KB_DEDUP_FIELDS,
    KB_VERIFY_FIELDS,
    KB_DUPLICATE_IGNORED_STATES,
    KB_PUBLISH_TIMEOUT_SECONDS,
    KB_WRITE_TIMEOUT_SECONDS,
    KB_VERIFY_DELAY_SECONDS,
    KB_PUBLISH_MAX_RETRIES,
    KB_PUBLISH_BATCH_CONCURRENCY,
    KB_PUBLISHED_STATE,
    KB_MAX_BATCH_CONCURRENCY,
    KB_UPDATABLE_FIELDS,
)

_log = structlog.get_logger("kb_write")


class KbDuplicateCheckInconclusive(Exception):
    """The duplicate check could not produce a trustworthy answer.

    Distinct from "no duplicates found", and deliberately not a
    `ServiceNowRequestError` — nothing went wrong at the transport layer. The
    query either could not be expressed faithfully or came back possibly
    truncated, so returning `[]` would report a clean bill of health for a check
    that did not really run. Callers fail closed and do not publish.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _handle_kb_error(error: httpx.HTTPStatusError, operation: str) -> str:
    error_map = {
        401: ERROR_KB_ARTICLE_AUTH_FAILED.format(operation=operation),
        403: ERROR_KB_ARTICLE_ACCESS_DENIED.format(operation=operation),
        400: ERROR_KB_ARTICLE_INVALID_REQUEST.format(operation=operation),
        404: ERROR_KB_ARTICLE_NOT_FOUND.format(operation=operation),
    }
    # KB writes append the response body to 400 and server-error messages.
    return map_http_error(
        error,
        error_map,
        ERROR_KB_ARTICLE_SERVER_ERROR.format(operation=operation),
        detail_codes={400},
        detail_on_default=True,
    )


def _unwrap_kb_write_response(result: Any, operation: str) -> Dict[str, Any] | str:
    return unwrap_write_response(
        result,
        ERROR_KB_WRITE_UNCONFIRMED.format(operation=operation),
        fields=KB_WRITE_RESPONSE_FIELDS,
    )


async def _write_kb_article(
    method: str,
    url: str,
    payload: Dict[str, Any],
    operation: str,
) -> Dict[str, Any] | str:
    # Bound the write with an anyio cancel scope — the pooled client runs with
    # timeout=None, so without this a held/half-open connection hangs forever.
    # anyio.fail_after raises builtin TimeoutError on breach, caught below.
    try:
        with anyio.fail_after(KB_WRITE_TIMEOUT_SECONDS):
            result = await make_nws_request(url, method=method, json_data=payload)
    except httpx.HTTPStatusError as e:
        return _handle_kb_error(e, operation)
    except Exception:
        return ERROR_KB_ARTICLE_REQUEST_FAILED.format(operation=operation)
    return _unwrap_kb_write_response(result, operation)


async def _get_kb_article_sys_id(article_number: str, workflow_state: str | None = None) -> str | None:
    """Return the article's sys_id, or None if no such article exists.

    None means "looked, absent" and nothing else (decision (d)). A failed read
    raises `ServiceNowRequestError` and the caller maps it, so a write can no
    longer report "article not found" because the lookup timed out.

    The number is escaped because this lookup picks the sys_id a write then
    PATCHes: a `^` in it could append or OR-in a condition and resolve to a
    *different* article. Refused (`QueryValueError`) rather than escaped, since no
    encoding can carry a `^`. `workflow_state` is an internal literal, so its `^`
    is ours and stays structural.
    """
    query = f"number={encode_query_value(article_number)}"
    if workflow_state:
        query += f"^workflow_state={workflow_state}"
    url = f"{NWS_API_BASE}/api/now/table/kb_knowledge?sysparm_fields=sys_id&sysparm_query={query}"
    data = await make_nws_request(url)
    if not data or not data.get('result') or not data['result']:
        return None
    return data['result'][0]['sys_id']


async def _get_kb_article_meta(article_number: str, workflow_state: str | None = None) -> Dict[str, Any] | None:
    """Fetch sys_id + short_description in one GET — avoids a second round-trip in publish.

    Same boundary as `_get_kb_article_sys_id`: None means absent, a failed read
    raises (decision (d)), and the number is escaped because it selects a write
    target.
    """
    query = f"number={encode_query_value(article_number)}"
    if workflow_state:
        query += f"^workflow_state={workflow_state}"
    url = (
        f"{NWS_API_BASE}/api/now/table/kb_knowledge"
        f"?sysparm_fields={','.join(KB_META_FIELDS)}"
        f"&sysparm_query={query}"
    )
    data = await make_nws_request(url)
    if not data or not data.get('result') or not data['result']:
        return None
    return data['result'][0]


def _dedup_query_defect(short_description: str) -> Optional[str]:
    """Why the dedup query would not faithfully carry *short_description*, if so.

    v4.4.1 narrowed this from three refusals to one. `&` and a literal `%XY` were
    only ever mis-transported — the encoder unquoted before re-quoting, undoing
    any escaping — and are carried faithfully now that the escaping survives and
    `_check_kb_duplicates` escapes the title itself. Titles like
    "Sales & Marketing" and "Deal 20%2C" no longer block a publish.

    `^` still refuses, because it is unrepresentable rather than merely
    mis-transported: ServiceNow's condition parser splits on the *decoded* value.
    A duplicate check that ran broader than asked cannot clear a publish.
    """
    unsafe = [c for c in KB_QUERY_UNSAFE_CHARS if c in short_description]
    if unsafe:
        return KB_DEDUP_REASON_UNSAFE_CHARS.format(chars=" ".join(unsafe))
    return None


async def _check_kb_duplicates(short_description: str, exclude_number: str) -> list:
    """Return KB articles matching short_description exactly across live workflow states.

    Queries with LIKE (ServiceNow's encoded-query "contains") then exact-matches
    in Python so the check catches drafts, review, and published articles.
    Retired + outdated articles are skipped — retired = explicitly killed,
    outdated = prior version after a newer publish (ServiceNow versioning
    artefact). Excludes the article being published (exclude_number) from results.

    An empty list means the check ran and found nothing. It never means the check
    could not run — that is the whole point of the two raises below, because the
    caller's only safe reading of `[]` is "clear to publish".

    Raises:
        ServiceNowRequestError: the read failed. Previously this arrived as None
            and became `[]`, so a timeout published the article unchecked.
        KbDuplicateCheckInconclusive: the query could not be trusted — either the
            title carries a character the encoded query mangles, or the result
            page hit its row cap and the duplicate may be off the end of it.
    """
    defect = _dedup_query_defect(short_description)
    if defect:
        # Refused before the request: the query that would run is not the one
        # asked for, so a "no duplicates" answer from it would be meaningless.
        raise KbDuplicateCheckInconclusive(defect)

    url = (
        f"{NWS_API_BASE}/api/now/table/kb_knowledge"
        f"?sysparm_fields={','.join(KB_DEDUP_FIELDS)}"
        f"&sysparm_query=short_descriptionLIKE{encode_query_value(short_description)}"
        f"&sysparm_limit={KB_DEDUP_QUERY_LIMIT}"
    )
    data = await make_nws_request(url)
    if not data or not data.get('result'):
        return []
    rows = data['result']
    needle = short_description.strip().lower()
    matches = [
        r for r in rows
        if r.get('short_description', '').strip().lower() == needle
        and r.get('number') != exclude_number
        and r.get('workflow_state', '').strip().lower() not in KB_DUPLICATE_IGNORED_STATES
    ]
    if matches:
        # A definite answer beats an inconclusive one, and both block the
        # publish — so report the duplicates even off a truncated page.
        return matches
    if len(rows) >= KB_DEDUP_QUERY_LIMIT:
        raise KbDuplicateCheckInconclusive(
            KB_DEDUP_REASON_TRUNCATED.format(limit=KB_DEDUP_QUERY_LIMIT)
        )
    return []


async def _call_kb_workflow(sys_id: str, action: str) -> Dict[str, Any] | str:
    # Custom Scripted REST API (qonv/publish) — invokes KnowledgeUIAction server-side.
    # Direct Table API writes to workflow_state are ignored by ServiceNow.
    url = f"{NWS_API_BASE}/api/qonv/mateco_knowledge/articles/{sys_id}/{action}"
    result = await _write_kb_article("POST", url, {}, action)
    if isinstance(result, str):
        _log.error("kb_workflow_error", action=action, sys_id=sys_id, url=url, result=result)
    return result


async def _call_kb_publish_workflow(sys_id: str) -> Dict[str, Any] | None:
    # Variant of _call_kb_workflow that propagates httpx exceptions instead
    # of mapping them to strings. _publish_with_verify needs the raw
    # TimeoutException / HTTPStatusError types to decide retry behaviour.
    url = f"{NWS_API_BASE}/api/qonv/mateco_knowledge/articles/{sys_id}/publish"
    with anyio.fail_after(KB_PUBLISH_TIMEOUT_SECONDS):
        return await make_nws_request(url, method="POST", json_data={})


async def _verify_kb_published(article_number: str) -> Dict[str, Any] | None:
    """Return the published row for *article_number*, or None if not yet published.

    ServiceNow KB versioning produces (draft, published) row pairs after a
    successful publish. Any row in the Published state confirms the workflow
    committed — that is the only authoritative success signal.

    None means "read succeeded, no Published row yet". A failed read raises: it
    is not evidence the publish did not commit, and treating it as such is what
    made an unreadable verify re-fire the publish write.
    """
    query = f"number={encode_query_value(article_number)}^workflow_state={KB_PUBLISHED_STATE}"
    url = (
        f"{NWS_API_BASE}/api/now/table/kb_knowledge"
        f"?sysparm_fields={','.join(KB_VERIFY_FIELDS)}"
        f"&sysparm_query={query}"
    )
    data = await make_nws_request(url)
    if not data or not data.get("result"):
        return None
    return data["result"][0]


async def _fire_publish(sys_id: str) -> str | None:
    """Fire the publish workflow. Returns None on success, error string on fire-time failure.

    A fire-time timeout is recoverable: the publish may still commit server-side,
    so we return a marker and let _publish_with_verify poll for the Published row.
    The deadline now comes from anyio.fail_after (builtin TimeoutError); the
    httpx.TimeoutException arm is kept for any transport-level timeout.
    """
    try:
        await _call_kb_publish_workflow(sys_id)
        return None
    except (httpx.TimeoutException, TimeoutError):
        return "fire timeout"
    except httpx.HTTPStatusError as e:
        return _handle_kb_error(e, "publish")


async def _publish_with_verify(sys_id: str, article_number: str) -> Dict[str, Any] | str:
    """Fire the publish workflow then verify by polling for a Published row.

    Treats verify as the source of truth — a fire-time TimeoutException or
    HTTPStatusError is recoverable if the article ends up Published. Only
    retries when verify confirms still-draft. Caps at KB_PUBLISH_MAX_RETRIES.
    """
    current_sys_id = sys_id
    last_fire_error: str | None = None

    for attempt in range(KB_PUBLISH_MAX_RETRIES + 1):
        last_fire_error = await _fire_publish(current_sys_id)

        await asyncio.sleep(KB_VERIFY_DELAY_SECONDS)
        try:
            published = await _verify_kb_published(article_number)
        except ServiceNowRequestError as error:
            # Do NOT retry. The publish write has already gone out; re-firing it
            # on the strength of a failed *read* is how one unreadable verify
            # became two publish workflows and a second published version.
            return _publish_unconfirmed(article_number, error)
        if published:
            return published

        if attempt < KB_PUBLISH_MAX_RETRIES:
            current_sys_id = await _refresh_draft_sys_id(article_number, current_sys_id)

    return last_fire_error or ERROR_KB_PUBLISH_NOT_CONFIRMED.format(number=article_number)


def _publish_unconfirmed(article_number: str, error: ServiceNowRequestError) -> Dict[str, Any]:
    """The publish fired but the confirming read failed — neither success nor failure.

    Carries `publish_confirmed: False` so a batch row can be labelled
    `unconfirmed` rather than `blocked` (nothing blocked it) or `error` (the write
    may well have landed).
    """
    return {
        "success": False,
        "publish_confirmed": False,
        "message": ERROR_KB_PUBLISH_VERIFY_UNREADABLE.format(
            number=article_number, message=error.message
        ),
        "error": error.to_error_dict()["error"],
    }


async def _refresh_draft_sys_id(article_number: str, current_sys_id: str) -> str:
    """Re-read the draft sys_id between publish attempts, best effort.

    ServiceNow versioning can hand the draft a new sys_id, so the retry re-reads
    it. A failed re-read is not worth abandoning the retry over — keep the sys_id
    already in hand rather than propagating.
    """
    try:
        refreshed = await _get_kb_article_sys_id(article_number, workflow_state="draft")
    except ServiceNowRequestError:
        return current_sys_id
    return refreshed or current_sys_id


async def update_knowledge_article(article_number: str, update_data: Dict[str, Any]) -> Dict[str, Any] | str:
    """Update fields on a knowledge article by article number (e.g. KB0001234).

    Args:
        article_number: The KB article number.
        update_data: Fields to update (e.g. short_description, text,
            kb_category, meta, meta_description).

    Returns:
        Updated article record dict, or error string on failure.
    """
    if not update_data:
        return ERROR_KB_NO_UPDATE_DATA

    bad = [k for k in update_data if k not in KB_UPDATABLE_FIELDS]
    if bad:
        return f"Rejected non-updatable field(s): {', '.join(bad)}"

    # Per-step stderr timing — localises a stall to the sys_id GET vs the PATCH
    # when an update hangs. stdout is reserved for the MCP JSON-RPC frame stream.
    t0 = time.monotonic()
    try:
        sys_id = await _get_kb_article_sys_id(article_number, workflow_state="draft")
    except (ServiceNowRequestError, QueryValueError) as error:
        # A failed lookup is not a missing article, and reporting it as one sent
        # people looking for an article that was there all along (decision (d)).
        # An unqueryable article number is the same kind of answer — the lookup
        # did not happen — and both types expose the same `to_error_dict()`.
        return error.to_error_dict()
    t1 = time.monotonic()
    print(f"[kb] {article_number} sys_id GET took {t1 - t0:.1f}s", file=sys.stderr)
    if not sys_id:
        return ERROR_KB_ARTICLE_NOT_FOUND_OP.format(number=article_number)
    fields = ",".join(KB_WRITE_RESPONSE_FIELDS)
    url = f"{NWS_API_BASE}/api/now/table/kb_knowledge/{sys_id}?sysparm_fields={fields}"
    result = await _write_kb_article("PATCH", url, update_data, "update")
    print(f"[kb] {article_number} PATCH took {time.monotonic() - t1:.1f}s", file=sys.stderr)
    return result


async def publish_knowledge_article(article_number: str) -> Dict[str, Any] | str:
    """Publish a knowledge article via the ServiceNow workflow endpoint.

    Runs a duplicate check across all workflow states before publishing.
    Returns early with a list of duplicates if any are found.

    Args:
        article_number: The KB article number (e.g. KB0001234).

    Returns:
        Updated article record dict, duplicate warning dict, or error string on failure.

    Fail-closed: the publish only proceeds on a duplicate check that positively
    came back clear. A check that could not run blocks the publish and writes
    nothing.
    """
    try:
        meta = await _get_kb_article_meta(article_number, workflow_state="draft")
    except (ServiceNowRequestError, QueryValueError) as error:
        return error.to_error_dict()
    if not meta:
        return ERROR_KB_ARTICLE_NOT_FOUND_OP.format(number=article_number)

    try:
        duplicates = await _check_kb_duplicates(meta['short_description'], article_number)
    except ServiceNowRequestError as error:
        return _duplicate_check_inconclusive(article_number, error.message)
    except KbDuplicateCheckInconclusive as inconclusive:
        return _duplicate_check_inconclusive(article_number, inconclusive.reason)

    if duplicates:
        return {
            "success": False,
            "message": "Duplicate KB article(s) found. Resolve before publishing.",
            "duplicates": duplicates,
        }

    return await _publish_with_verify(meta['sys_id'], article_number)


def _duplicate_check_inconclusive(article_number: str, reason: str) -> Dict[str, Any]:
    """Refuse the publish because the duplicate check could not answer.

    Same `success: False` shape as a found-duplicate block — in both cases nothing
    was written and the caller must resolve something first. `duplicate_check`
    distinguishes "the guard said no" from "the guard could not say".
    """
    return {
        "success": False,
        "duplicate_check": "inconclusive",
        "message": ERROR_KB_DUPLICATE_CHECK_INCONCLUSIVE.format(
            number=article_number, reason=reason
        ),
        "duplicates": [],
    }


def _duplicate_row_inconclusive(article_number: str, reason: str) -> Dict[str, Any]:
    """A row for an article whose duplicate status could not be determined.

    Deliberately carries NO `has_duplicate` key. The old shape reported
    `has_duplicate: False` with no error when the read had failed — a clean bill
    of health from a check that never ran, and the exact reading that let a
    publish through. A consumer that reaches for `has_duplicate` here should fail
    loudly rather than read the absence of a duplicate into a missing answer.
    """
    return {
        "number": article_number,
        "duplicate_check": "inconclusive",
        "duplicates": [],
        "error": reason,
    }


async def _check_single_kb_duplicate(article_number: str) -> Dict[str, Any]:
    """Lookup meta then check duplicates for one article. Used by check_kb_duplicates fan-out."""
    try:
        meta = await _get_kb_article_meta(article_number)
    except (ServiceNowRequestError, QueryValueError) as error:
        return _duplicate_row_inconclusive(article_number, error.message)
    if not meta:
        # A genuinely absent article: the check did run, so has_duplicate stands.
        return {
            "number": article_number,
            "has_duplicate": False,
            "duplicates": [],
            "error": ERROR_KB_ARTICLE_NOT_FOUND_OP.format(number=article_number),
        }
    try:
        duplicates = await _check_kb_duplicates(meta["short_description"], article_number)
    except ServiceNowRequestError as error:
        return _duplicate_row_inconclusive(article_number, error.message)
    except KbDuplicateCheckInconclusive as inconclusive:
        return _duplicate_row_inconclusive(article_number, inconclusive.reason)
    return {
        "number": article_number,
        "has_duplicate": bool(duplicates),
        "duplicates": [
            {"number": d.get("number"), "workflow_state": d.get("workflow_state")}
            for d in duplicates
        ],
    }


def _outcome_error_message(outcome: BaseException) -> str:
    """Message for an exception that escaped a per-article coroutine."""
    if isinstance(outcome, (ServiceNowRequestError, QueryValueError)):
        return outcome.message
    if isinstance(outcome, KbDuplicateCheckInconclusive):
        return outcome.reason
    return f"{type(outcome).__name__}: {outcome}"


def _rows_from_outcomes(numbers, outcomes, error_row) -> List[Dict[str, Any]]:
    """Zip gathered outcomes back onto their article numbers, exceptions included.

    `asyncio.gather(..., return_exceptions=True)` keeps results positional, so a
    failure stays attached to the article it belongs to instead of aborting the
    batch and discarding every sibling row — including rows for articles that
    were already written.
    """
    rows: List[Dict[str, Any]] = []
    for number, outcome in zip(numbers, outcomes):
        if isinstance(outcome, BaseException):
            rows.append(error_row(number, _outcome_error_message(outcome)))
        else:
            rows.append(outcome)
    return rows


async def check_kb_duplicates(
    article_numbers: JsonList,
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

        A row whose check could not be completed instead carries
        `{"number", "duplicate_check": "inconclusive", "duplicates": [], "error"}`
        and NO `has_duplicate` key — a missing answer must not be readable as
        "no duplicates". Treat such a row the way `publish_knowledge_article`
        does: as a reason not to publish, not as a clean result.
    """
    if not article_numbers:
        return {"result": []}
    if len(article_numbers) > 50:
        return {"error": "check_kb_duplicates accepts at most 50 article numbers per call."}

    semaphore = asyncio.Semaphore(min(max(1, concurrency), KB_MAX_BATCH_CONCURRENCY))

    async def _bounded(num: str) -> Dict[str, Any]:
        async with semaphore:
            return await _check_single_kb_duplicate(num)

    outcomes = await asyncio.gather(
        *(_bounded(n) for n in article_numbers), return_exceptions=True
    )
    return {"result": _rows_from_outcomes(article_numbers, outcomes, _duplicate_row_inconclusive)}


def _normalize_publish_result(article_number: str, result: Dict[str, Any] | str) -> Dict[str, Any]:
    """Normalize publish_knowledge_article output into a flat batch-result row.

    Four statuses: `published`, `blocked` (a guard said no — nothing written),
    `unconfirmed` (the write went out, the confirming read did not come back), and
    `error`.

    Note the ordering. `published` is the FALL-THROUGH, so every non-success shape
    has to be recognised before it: a bare `{"error": ...}` failure dict would
    otherwise be reported as a successful publish with `workflow_state: None`,
    turning the typed failure this tier introduced into a false success — the
    precise mislabelling the tier exists to remove.
    """
    if isinstance(result, str):
        return {"number": article_number, "status": "error", "message": result}
    if not isinstance(result, dict):
        return {"number": article_number, "status": "error", "message": str(result)}
    if result.get("publish_confirmed") is False:
        return {
            "number": article_number,
            "status": "unconfirmed",
            "message": result.get("message"),
            "error": result.get("error"),
        }
    if is_read_failure(result):
        error = result.get("error") or {}
        return {
            "number": article_number,
            "status": "error",
            "message": error.get("message"),
            "code": error.get("code"),
        }
    if result.get("success") is False:
        row = {
            "number": article_number,
            "status": "blocked",
            "message": result.get("message"),
            "blockers": result.get("duplicates", []),
        }
        if result.get("duplicate_check"):
            row["duplicate_check"] = result["duplicate_check"]
        return row
    return {
        "number": article_number,
        "status": "published",
        "workflow_state": result.get("workflow_state"),
    }


async def publish_knowledge_articles(
    article_numbers: JsonList,
    concurrency: int = KB_PUBLISH_BATCH_CONCURRENCY,
) -> Dict[str, Any]:
    """Publish multiple KB articles in one tool call.

    Runs full publish flow per article (meta lookup → duplicate check →
    ServiceNow workflow POST). Returns a flat status row per article so
    failures and duplicate blocks do not abort the rest of the batch.

    Args:
        article_numbers: KB numbers to publish. Capped at 20 per call.
        concurrency: Max concurrent ServiceNow round-trips
            (default KB_PUBLISH_BATCH_CONCURRENCY = 2).

    Returns:
        {"result": [{"number", "status": "published"|"blocked"|"unconfirmed"|"error", ...}, ...]}

        `blocked` — a guard refused (duplicates found, or the duplicate check
        could not answer). Nothing was written.
        `unconfirmed` — the publish was submitted but the confirming read failed.
        It may have committed; do not blind-retry.
    """
    if not article_numbers:
        return {"result": []}
    if len(article_numbers) > 20:
        return {"error": "publish_knowledge_articles accepts at most 20 article numbers per call."}

    semaphore = asyncio.Semaphore(min(max(1, concurrency), KB_MAX_BATCH_CONCURRENCY))

    async def _bounded(num: str) -> Dict[str, Any]:
        async with semaphore:
            outcome = await publish_knowledge_article(num)
            return _normalize_publish_result(num, outcome)

    def _error_row(number: str, message: str) -> Dict[str, Any]:
        return {"number": number, "status": "error", "message": message}

    # return_exceptions: one article's failure must not discard the batch. Some
    # of these articles have already been PUBLISHED by the time a later one
    # fails, and aborting the gather threw away the only record of which.
    outcomes = await asyncio.gather(
        *(_bounded(n) for n in article_numbers), return_exceptions=True
    )
    return {"result": _rows_from_outcomes(article_numbers, outcomes, _error_row)}


async def retire_knowledge_article(article_number: str) -> Dict[str, Any] | str:
    """Retire a knowledge article via the ServiceNow workflow endpoint.

    Args:
        article_number: The KB article number (e.g. KB0001234).

    Returns:
        Updated article record dict, or error string on failure.
    """
    try:
        sys_id = await _get_kb_article_sys_id(article_number, workflow_state="published")
    except (ServiceNowRequestError, QueryValueError) as error:
        return error.to_error_dict()
    if not sys_id:
        return ERROR_KB_ARTICLE_NOT_FOUND_OP.format(number=article_number)
    return await _call_kb_workflow(sys_id, "retire")
