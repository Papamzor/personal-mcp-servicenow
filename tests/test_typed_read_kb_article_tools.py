"""Typed read failures in the KB article tools (v4.4 Tier 0.3, PR C).

`Table_Tools.kb_article_tools` joins `_TYPED_CALLERS`, so a failed GET raises
instead of returning None. Four things are locked here:

1. **The publish guard is fail-closed.** `_check_kb_duplicates` has three
   outcomes — clear, duplicates-found, inconclusive — and only *clear* permits a
   publish. Before this, a failed duplicate-check read returned `[]`, the one
   value `publish_knowledge_article` reads as "clear to publish", so a timeout
   published the article with the guard silently skipped and reported success.

2. **An unreadable verify does not re-fire the publish.** The write has already
   gone out; retrying on the strength of a failed *read* published a second
   version. Exactly one fire, status `unconfirmed`.

3. **Pre-write reads distinguish absent from failed** (decision (d)), so a write
   no longer reports "article not found" for a timeout.

4. **A failure shape is never re-wrapped as success.** `_normalize_publish_result`
   reports `published` by fall-through, so every non-success shape has to be
   recognised ahead of it.

The assertions to keep honest are the ones about what did NOT happen: no publish
POST fired, exactly one fired, the batch did not lose its other rows. Those are
the properties that would silently regress.
"""
import asyncio

import pytest
from unittest.mock import AsyncMock, patch

from constants import (
    ERROR_KB_ARTICLE_NOT_FOUND_OP,
    KB_DEDUP_QUERY_LIMIT,
)
from http_layer.errors import ErrorCode, ServiceNowRequestError
from Table_Tools.kb_article_tools import (
    KbDuplicateCheckInconclusive,
    _check_kb_duplicates,
    _normalize_publish_result,
    _publish_with_verify,
    check_kb_duplicates,
    publish_knowledge_article,
    publish_knowledge_articles,
    retire_knowledge_article,
    update_knowledge_article,
)

TIMEOUT = ServiceNowRequestError(
    ErrorCode.TIMEOUT, "ServiceNow request timed out", retryable=True
)
FORBIDDEN = ServiceNowRequestError(
    ErrorCode.FORBIDDEN, "ServiceNow returned HTTP 403", status_code=403
)

META = {"sys_id": "a" * 32, "short_description": "How to reset a password"}
PUBLISHED_ROW = {"number": "KB0001234", "workflow_state": "Published"}


def _no_sleep():
    return patch("Table_Tools.kb_article_tools.asyncio.sleep", new_callable=AsyncMock)


def _assert_plain_failure(response, code):
    assert isinstance(response, dict), response
    assert set(response) == {"error"}, response
    assert response["error"]["code"] == code


class TestPublishGuardIsFailClosed:
    """A publish requires a duplicate check that positively came back clear."""

    @pytest.mark.asyncio
    async def test_failed_duplicate_read_does_not_publish(self):
        """The headline bug. A timeout in the guard must not become permission."""
        with patch(
            "Table_Tools.kb_article_tools._get_kb_article_meta",
            new=AsyncMock(return_value=META),
        ), patch(
            "Table_Tools.kb_article_tools._check_kb_duplicates",
            new=AsyncMock(side_effect=TIMEOUT),
        ), patch(
            "Table_Tools.kb_article_tools._publish_with_verify", new=AsyncMock()
        ) as publish:
            result = await publish_knowledge_article("KB0001234")

        publish.assert_not_called()
        assert result["success"] is False
        assert result["duplicate_check"] == "inconclusive"
        assert "not published" in result["message"]
        assert "Nothing was written" in result["message"]

    @pytest.mark.asyncio
    async def test_inconclusive_check_does_not_publish(self):
        with patch(
            "Table_Tools.kb_article_tools._get_kb_article_meta",
            new=AsyncMock(return_value=META),
        ), patch(
            "Table_Tools.kb_article_tools._check_kb_duplicates",
            new=AsyncMock(side_effect=KbDuplicateCheckInconclusive("the reason")),
        ), patch(
            "Table_Tools.kb_article_tools._publish_with_verify", new=AsyncMock()
        ) as publish:
            result = await publish_knowledge_article("KB0001234")

        publish.assert_not_called()
        assert result["duplicate_check"] == "inconclusive"
        assert "the reason" in result["message"]

    @pytest.mark.asyncio
    async def test_clear_check_still_publishes(self):
        """The guard must not have become so strict that nothing can publish."""
        with patch(
            "Table_Tools.kb_article_tools._get_kb_article_meta",
            new=AsyncMock(return_value=META),
        ), patch(
            "Table_Tools.kb_article_tools._check_kb_duplicates",
            new=AsyncMock(return_value=[]),
        ), patch(
            "Table_Tools.kb_article_tools._publish_with_verify",
            new=AsyncMock(return_value=PUBLISHED_ROW),
        ) as publish:
            result = await publish_knowledge_article("KB0001234")

        publish.assert_called_once()
        assert result == PUBLISHED_ROW

    @pytest.mark.asyncio
    async def test_found_duplicates_still_block_with_their_blockers(self):
        dupes = [{"number": "KB0009999", "workflow_state": "published"}]
        with patch(
            "Table_Tools.kb_article_tools._get_kb_article_meta",
            new=AsyncMock(return_value=META),
        ), patch(
            "Table_Tools.kb_article_tools._check_kb_duplicates",
            new=AsyncMock(return_value=dupes),
        ), patch(
            "Table_Tools.kb_article_tools._publish_with_verify", new=AsyncMock()
        ) as publish:
            result = await publish_knowledge_article("KB0001234")

        publish.assert_not_called()
        assert result["duplicates"] == dupes
        assert "duplicate_check" not in result

    @pytest.mark.asyncio
    async def test_failed_meta_read_is_not_article_not_found(self):
        with patch(
            "Table_Tools.kb_article_tools._get_kb_article_meta",
            new=AsyncMock(side_effect=TIMEOUT),
        ), patch(
            "Table_Tools.kb_article_tools._publish_with_verify", new=AsyncMock()
        ) as publish:
            result = await publish_knowledge_article("KB0001234")

        publish.assert_not_called()
        _assert_plain_failure(result, ErrorCode.TIMEOUT)
        assert result != ERROR_KB_ARTICLE_NOT_FOUND_OP.format(number="KB0001234")

    @pytest.mark.asyncio
    async def test_absent_article_keeps_its_not_found_message(self):
        with patch(
            "Table_Tools.kb_article_tools._get_kb_article_meta",
            new=AsyncMock(return_value=None),
        ):
            result = await publish_knowledge_article("KB9999999")
        assert result == ERROR_KB_ARTICLE_NOT_FOUND_OP.format(number="KB9999999")


class TestDuplicateCheckOutcomes:
    """`[]` must mean "checked, clear" and nothing else."""

    @pytest.mark.asyncio
    async def test_unsafe_character_is_inconclusive_before_any_request(self):
        """A '^' in the title splits the encoded query, silently widening it.

        Percent-encoding at the call site does not help: ensure_query_encoded
        unquotes before re-quoting and keeps '^' in its safe-set, so the operator
        survives either way. The check therefore refuses to answer.
        """
        with patch("Table_Tools.kb_article_tools.make_nws_request") as request:
            with pytest.raises(KbDuplicateCheckInconclusive) as excinfo:
                await _check_kb_duplicates("Cost^Center report", "KB0001234")
        request.assert_not_called()
        assert "widen" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_ampersand_is_also_inconclusive(self):
        with pytest.raises(KbDuplicateCheckInconclusive):
            await _check_kb_duplicates("Sales & Marketing", "KB0001234")

    @pytest.mark.parametrize("title, becomes", [
        ("Deal 20%2C off", "Deal 20, off"),
        ("Reset %41dmin password", "Reset Admin password"),
        ("Up 20%DB backups", None),  # invalid byte -> U+FFFD
    ])
    @pytest.mark.asyncio
    async def test_percent_escape_in_the_title_is_inconclusive(self, title, becomes):
        """The quiet one: ensure_query_encoded unquotes, so '%XY' is decoded.

        ServiceNow would be searched for a different string than the title, and
        `unquote` never raises, so nothing announces it. That silently returned
        `[]` and published the article.
        """
        if becomes is not None:
            from urllib.parse import unquote
            assert unquote(title) == becomes, "premise of the test"
        with patch("Table_Tools.kb_article_tools.make_nws_request") as request:
            with pytest.raises(KbDuplicateCheckInconclusive) as excinfo:
                await _check_kb_duplicates(title, "KB0001234")
        request.assert_not_called()
        assert "percent-escape" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_a_bare_percent_is_not_refused(self):
        """No false positives: a '%' not followed by hex digits survives intact.

        Blacklisting '%' outright would refuse an ordinary title, which is why the
        check is a round trip on the value rather than a character list.
        """
        with patch("Table_Tools.kb_article_tools.make_nws_request") as request:
            request.return_value = {"result": []}
            assert await _check_kb_duplicates("Cut costs by 50% off", "KB0001234") == []
        request.assert_called_once()

    @pytest.mark.parametrize("char", list("=<>():@!"))
    @pytest.mark.asyncio
    async def test_the_rest_of_the_operator_safe_set_is_not_refused(self, char):
        """Only ^ and & break structure; the others survive the round trip.

        Pinned so a future widening of KB_QUERY_UNSAFE_CHARS has to be deliberate
        rather than a precaution that quietly blocks publishes.
        """
        with patch("Table_Tools.kb_article_tools.make_nws_request") as request:
            request.return_value = {"result": []}
            assert await _check_kb_duplicates(f"Cost{char}Center guide", "KB0001234") == []

    @pytest.mark.asyncio
    async def test_truncated_page_is_inconclusive_not_clear(self):
        """A full page may have left the real duplicate off the end of it."""
        rows = [
            {"number": f"KB{i:07d}", "short_description": "other", "workflow_state": "published"}
            for i in range(KB_DEDUP_QUERY_LIMIT)
        ]
        with patch("Table_Tools.kb_article_tools.make_nws_request") as request:
            request.return_value = {"result": rows}
            with pytest.raises(KbDuplicateCheckInconclusive) as excinfo:
                await _check_kb_duplicates("How to reset a password", "KB0001234")
        assert str(KB_DEDUP_QUERY_LIMIT) in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_a_definite_duplicate_beats_truncation(self):
        """Both outcomes block, so report the specific one."""
        rows = [
            {"number": f"KB{i:07d}", "short_description": "other", "workflow_state": "published"}
            for i in range(KB_DEDUP_QUERY_LIMIT - 1)
        ] + [
            {"number": "KB0009999", "short_description": "How to reset a password",
             "workflow_state": "published"}
        ]
        with patch("Table_Tools.kb_article_tools.make_nws_request") as request:
            request.return_value = {"result": rows}
            matches = await _check_kb_duplicates("How to reset a password", "KB0001234")
        assert [m["number"] for m in matches] == ["KB0009999"]

    @pytest.mark.asyncio
    async def test_short_page_with_no_match_is_clear(self):
        with patch("Table_Tools.kb_article_tools.make_nws_request") as request:
            request.return_value = {"result": [
                {"number": "KB0002222", "short_description": "something else",
                 "workflow_state": "published"},
            ]}
            assert await _check_kb_duplicates("How to reset a password", "KB0001234") == []

    @pytest.mark.asyncio
    async def test_query_carries_an_explicit_row_cap(self):
        """Without a limit the instance default applies and truncation is invisible."""
        with patch("Table_Tools.kb_article_tools.make_nws_request") as request:
            request.return_value = {"result": []}
            await _check_kb_duplicates("How to reset a password", "KB0001234")
        url = request.call_args.args[0]
        assert f"sysparm_limit={KB_DEDUP_QUERY_LIMIT}" in url


class TestUnreadableVerifyDoesNotRefire:
    @pytest.mark.asyncio
    async def test_failed_verify_fires_the_publish_exactly_once(self):
        with _no_sleep(), patch(
            "Table_Tools.kb_article_tools._fire_publish",
            new=AsyncMock(return_value=None),
        ) as fire, patch(
            "Table_Tools.kb_article_tools._verify_kb_published",
            new=AsyncMock(side_effect=TIMEOUT),
        ):
            result = await _publish_with_verify("a" * 32, "KB0001234")

        assert fire.call_count == 1, "an unreadable verify must not re-fire the write"
        assert result["publish_confirmed"] is False
        assert result["success"] is False
        assert result["error"]["code"] == ErrorCode.TIMEOUT
        assert "may or may not be published" in result["message"]

    @pytest.mark.asyncio
    async def test_still_draft_after_verify_does_retry(self):
        """The retry path is for a verify that positively says "not published yet"."""
        with _no_sleep(), patch(
            "Table_Tools.kb_article_tools._fire_publish",
            new=AsyncMock(return_value=None),
        ) as fire, patch(
            "Table_Tools.kb_article_tools._verify_kb_published",
            new=AsyncMock(return_value=None),
        ), patch(
            "Table_Tools.kb_article_tools._get_kb_article_sys_id",
            new=AsyncMock(return_value="b" * 32),
        ):
            await _publish_with_verify("a" * 32, "KB0001234")

        assert fire.call_count == 2

    @pytest.mark.asyncio
    async def test_a_failed_sys_id_refresh_keeps_the_sys_id_in_hand(self):
        """The refresh between attempts is best effort, not a reason to abort."""
        seen = []

        async def fire(sys_id):
            seen.append(sys_id)
            return None

        with _no_sleep(), patch(
            "Table_Tools.kb_article_tools._fire_publish", new=fire
        ), patch(
            "Table_Tools.kb_article_tools._verify_kb_published",
            new=AsyncMock(return_value=None),
        ), patch(
            "Table_Tools.kb_article_tools._get_kb_article_sys_id",
            new=AsyncMock(side_effect=TIMEOUT),
        ):
            await _publish_with_verify("a" * 32, "KB0001234")

        assert seen == ["a" * 32, "a" * 32]


class TestNormalizePublishResultNeverInventsSuccess:
    """`published` is the fall-through, so every other shape must be caught first."""

    def test_a_bare_failure_dict_is_not_reported_as_published(self):
        row = _normalize_publish_result("KB0001234", TIMEOUT.to_error_dict())
        assert row["status"] == "error"
        assert row["code"] == ErrorCode.TIMEOUT
        assert row["message"] == "ServiceNow request timed out"

    def test_unconfirmed_is_its_own_status(self):
        result = {
            "success": False,
            "publish_confirmed": False,
            "message": "submitted but unconfirmed",
            "error": {"code": ErrorCode.TIMEOUT, "message": "timed out"},
        }
        row = _normalize_publish_result("KB0001234", result)
        assert row["status"] == "unconfirmed"
        assert row["error"]["code"] == ErrorCode.TIMEOUT

    def test_inconclusive_block_keeps_its_marker(self):
        result = {
            "success": False,
            "duplicate_check": "inconclusive",
            "message": "could not be completed",
            "duplicates": [],
        }
        row = _normalize_publish_result("KB0001234", result)
        assert row["status"] == "blocked"
        assert row["duplicate_check"] == "inconclusive"

    def test_duplicates_block_reports_its_blockers(self):
        result = {
            "success": False,
            "message": "Duplicate KB article(s) found.",
            "duplicates": [{"number": "KB0009999"}],
        }
        row = _normalize_publish_result("KB0001234", result)
        assert row["status"] == "blocked"
        assert row["blockers"] == [{"number": "KB0009999"}]

    def test_a_published_row_is_still_published(self):
        row = _normalize_publish_result("KB0001234", PUBLISHED_ROW)
        assert row["status"] == "published"
        assert row["workflow_state"] == "Published"

    def test_a_non_dict_non_str_is_an_error_not_a_publish(self):
        row = _normalize_publish_result("KB0001234", 42)
        assert row["status"] == "error"


class TestBatchesKeepTheirOtherRows:
    @pytest.mark.asyncio
    async def test_one_articles_raise_does_not_discard_the_batch(self):
        """Some of these are already published by the time a later one fails."""
        async def publish(number):
            if number == "KB0002222":
                raise TIMEOUT
            return PUBLISHED_ROW

        with patch("Table_Tools.kb_article_tools.publish_knowledge_article", new=publish):
            result = await publish_knowledge_articles(
                ["KB0001111", "KB0002222", "KB0003333"]
            )

        rows = {r["number"]: r for r in result["result"]}
        assert len(rows) == 3
        assert rows["KB0001111"]["status"] == "published"
        assert rows["KB0003333"]["status"] == "published"
        assert rows["KB0002222"]["status"] == "error"
        assert rows["KB0002222"]["message"] == "ServiceNow request timed out"

    @pytest.mark.asyncio
    async def test_an_unexpected_bug_in_one_article_is_still_one_row(self):
        async def publish(number):
            if number == "KB0002222":
                raise RuntimeError("boom")
            return PUBLISHED_ROW

        with patch("Table_Tools.kb_article_tools.publish_knowledge_article", new=publish):
            result = await publish_knowledge_articles(["KB0001111", "KB0002222"])

        rows = {r["number"]: r for r in result["result"]}
        assert rows["KB0001111"]["status"] == "published"
        assert rows["KB0002222"]["status"] == "error"
        assert "RuntimeError" in rows["KB0002222"]["message"]

    @pytest.mark.asyncio
    async def test_dup_check_row_for_a_failed_read_is_not_a_clean_bill_of_health(self):
        with patch(
            "Table_Tools.kb_article_tools._get_kb_article_meta",
            new=AsyncMock(return_value=META),
        ), patch(
            "Table_Tools.kb_article_tools._check_kb_duplicates",
            new=AsyncMock(side_effect=FORBIDDEN),
        ):
            result = await check_kb_duplicates(["KB0001234"])

        row = result["result"][0]
        assert row["duplicate_check"] == "inconclusive"
        assert row["error"] == "ServiceNow returned HTTP 403"
        assert "has_duplicate" not in row, (
            "a missing answer must not be readable as 'no duplicates'"
        )

    @pytest.mark.asyncio
    async def test_dup_check_row_for_a_failed_meta_read_is_also_inconclusive(self):
        """The lookup half of the row can fail too, and reads the same way."""
        with patch(
            "Table_Tools.kb_article_tools._get_kb_article_meta",
            new=AsyncMock(side_effect=TIMEOUT),
        ):
            result = await check_kb_duplicates(["KB0001234"])

        row = result["result"][0]
        assert row["duplicate_check"] == "inconclusive"
        assert "has_duplicate" not in row

    @pytest.mark.asyncio
    async def test_dup_check_row_for_an_untrustworthy_query_is_inconclusive(self):
        """An unsafe title reaches the row as inconclusive, not as 'no duplicates'."""
        with patch(
            "Table_Tools.kb_article_tools._get_kb_article_meta",
            new=AsyncMock(return_value={"sys_id": "a" * 32,
                                        "short_description": "Cost^Center report"}),
        ):
            result = await check_kb_duplicates(["KB0001234"])

        row = result["result"][0]
        assert row["duplicate_check"] == "inconclusive"
        assert "widen" in row["error"]
        assert "has_duplicate" not in row

    @pytest.mark.asyncio
    async def test_dup_check_row_for_a_real_answer_still_carries_has_duplicate(self):
        with patch(
            "Table_Tools.kb_article_tools._get_kb_article_meta",
            new=AsyncMock(return_value=META),
        ), patch(
            "Table_Tools.kb_article_tools._check_kb_duplicates",
            new=AsyncMock(return_value=[]),
        ):
            result = await check_kb_duplicates(["KB0001234"])

        assert result["result"][0]["has_duplicate"] is False


class TestOutcomeErrorMessage:
    """Per-exception-type messages for anything that escapes a batch coroutine.

    Both public batch entry points catch their own errors, so this is the net
    under an unexpected escape. Tested directly rather than left uncovered: the
    point of the net is that it produces a usable row, and that is cheap to
    verify but invisible in the batch tests.
    """

    def test_typed_read_failure_uses_its_message(self):
        from Table_Tools.kb_article_tools import _outcome_error_message
        assert _outcome_error_message(TIMEOUT) == "ServiceNow request timed out"

    def test_inconclusive_uses_its_reason(self):
        from Table_Tools.kb_article_tools import _outcome_error_message
        assert _outcome_error_message(
            KbDuplicateCheckInconclusive("the page was capped")
        ) == "the page was capped"

    def test_anything_else_is_named_by_its_type(self):
        from Table_Tools.kb_article_tools import _outcome_error_message
        assert _outcome_error_message(RuntimeError("boom")) == "RuntimeError: boom"


class TestPreWriteReadsDistinguishAbsentFromFailed:
    """Decision (d): a write never reports "not found" because a lookup failed."""

    @pytest.mark.asyncio
    async def test_update_failed_lookup_is_not_not_found(self):
        with patch(
            "Table_Tools.kb_article_tools._get_kb_article_sys_id",
            new=AsyncMock(side_effect=TIMEOUT),
        ), patch(
            "Table_Tools.kb_article_tools._write_kb_article", new=AsyncMock()
        ) as write:
            result = await update_knowledge_article("KB0001234", {"short_description": "x"})

        write.assert_not_called()
        _assert_plain_failure(result, ErrorCode.TIMEOUT)

    @pytest.mark.asyncio
    async def test_update_absent_article_keeps_not_found(self):
        with patch(
            "Table_Tools.kb_article_tools._get_kb_article_sys_id",
            new=AsyncMock(return_value=None),
        ):
            result = await update_knowledge_article("KB9999999", {"short_description": "x"})
        assert result == ERROR_KB_ARTICLE_NOT_FOUND_OP.format(number="KB9999999")

    @pytest.mark.asyncio
    async def test_retire_failed_lookup_is_not_not_found(self):
        with patch(
            "Table_Tools.kb_article_tools._get_kb_article_sys_id",
            new=AsyncMock(side_effect=FORBIDDEN),
        ), patch(
            "Table_Tools.kb_article_tools._call_kb_workflow", new=AsyncMock()
        ) as workflow:
            result = await retire_knowledge_article("KB0001234")

        workflow.assert_not_called()
        _assert_plain_failure(result, ErrorCode.FORBIDDEN)

    @pytest.mark.asyncio
    async def test_retire_absent_article_keeps_not_found(self):
        with patch(
            "Table_Tools.kb_article_tools._get_kb_article_sys_id",
            new=AsyncMock(return_value=None),
        ):
            result = await retire_knowledge_article("KB9999999")
        assert result == ERROR_KB_ARTICLE_NOT_FOUND_OP.format(number="KB9999999")


class TestEndToEndThroughTheRealDispatcher:
    """Proves the `_TYPED_CALLERS` entry resolves for this module.

    Without the entry the shim returns None, `_check_kb_duplicates` answers `[]`,
    and the article publishes — so these fail if the entry is reverted, which the
    mock-at-the-module-seam tests above cannot detect on their own.
    """

    @pytest.fixture
    def transport(self, monkeypatch):
        """Fake the transport under the real dispatcher; record every write."""
        import http_layer.request_dispatcher as dispatcher

        writes = []

        class FakeClient:
            async def make_authenticated_request(self, method, url, raise_for_status=True, json=None):
                writes.append((method, url))
                return {"result": PUBLISHED_ROW}

        def install(get_handler):
            async def fake_get(url):
                return get_handler(url)
            monkeypatch.setattr(dispatcher, "make_oauth_request", fake_get)
            monkeypatch.setattr(dispatcher, "get_oauth_client", lambda: FakeClient())
            return writes

        return install

    @staticmethod
    def _meta_ok_dedup(dedup):
        """GET handler: meta resolves, the dedup query does whatever `dedup` says."""
        def handler(url):
            if "short_descriptionLIKE" in url:
                return dedup() if callable(dedup) else dedup
            if "sys_id" in url and "short_description" in url:
                return {"result": [META]}
            return {"result": []}
        return handler

    @pytest.mark.asyncio
    async def test_dedup_timeout_blocks_the_publish(self, transport):
        def boom():
            raise TimeoutError()

        writes = transport(self._meta_ok_dedup(boom))
        with _no_sleep():
            result = await publish_knowledge_article("KB0001234")

        assert writes == [], "the publish workflow must not have been called"
        assert result["duplicate_check"] == "inconclusive"

    @pytest.mark.asyncio
    async def test_clear_dedup_publishes(self, transport):
        def handler(url):
            if "short_descriptionLIKE" in url:
                return {"result": []}
            if "workflow_state=published" in url or "workflow_state%3Dpublished" in url:
                return {"result": [PUBLISHED_ROW]}
            if "sys_id" in url and "short_description" in url:
                return {"result": [META]}
            return {"result": []}

        writes = transport(handler)
        with _no_sleep():
            result = await publish_knowledge_article("KB0001234")

        assert len(writes) == 1
        assert writes[0][0] == "POST"
        assert result == PUBLISHED_ROW

    @pytest.mark.asyncio
    async def test_verify_timeout_leaves_exactly_one_write(self, transport):
        def handler(url):
            if "short_descriptionLIKE" in url:
                return {"result": []}
            if "workflow_state=published" in url or "workflow_state%3Dpublished" in url:
                raise TimeoutError()
            if "sys_id" in url and "short_description" in url:
                return {"result": [META]}
            return {"result": []}

        writes = transport(handler)
        with _no_sleep():
            result = await publish_knowledge_article("KB0001234")

        assert len(writes) == 1, "an unreadable verify must not re-fire the publish"
        assert result["publish_confirmed"] is False
