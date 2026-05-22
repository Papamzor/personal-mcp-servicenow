"""
Tests for kb_article_tools.py — KB article write path (update / publish / retire).
Target: 90%+ line coverage, 75%+ branch coverage.
"""

import asyncio
import pytest
from unittest.mock import patch, MagicMock
import httpx

from Table_Tools.kb_article_tools import (
    _handle_kb_error,
    _unwrap_kb_write_response,
    _write_kb_article,
    _get_kb_article_sys_id,
    _get_kb_article_meta,
    _check_kb_duplicates,
    _normalize_publish_result,
    update_knowledge_article,
    publish_knowledge_article,
    publish_knowledge_articles,
    retire_knowledge_article,
    check_kb_duplicates,
)


def _make_http_status_error(status_code: int) -> httpx.HTTPStatusError:
    response = MagicMock()
    response.status_code = status_code
    return httpx.HTTPStatusError(str(status_code), request=MagicMock(), response=response)


class TestHandleKbError:

    def test_401_returns_auth_failed(self):
        result = _handle_kb_error(_make_http_status_error(401), "publish")
        assert "Authentication failed" in result

    def test_403_returns_access_denied(self):
        result = _handle_kb_error(_make_http_status_error(403), "retire")
        assert "Access denied" in result

    def test_400_returns_invalid_request(self):
        result = _handle_kb_error(_make_http_status_error(400), "update")
        assert "Invalid request" in result

    def test_404_returns_not_found(self):
        result = _handle_kb_error(_make_http_status_error(404), "update")
        assert "not found" in result.lower()

    def test_500_returns_server_error(self):
        result = _handle_kb_error(_make_http_status_error(500), "publish")
        assert "server error" in result.lower()


class TestUnwrapKbWriteResponse:

    def test_unwrap_with_inner_result(self):
        result = _unwrap_kb_write_response({"result": {"number": "KB0001234"}}, "update")
        assert result == {"number": "KB0001234"}

    def test_unwrap_empty_dict_returns_fallback(self):
        result = _unwrap_kb_write_response({}, "publish")
        assert "successful but no data returned" in result

    def test_unwrap_none_returns_fallback(self):
        result = _unwrap_kb_write_response(None, "retire")
        assert "successful but no data returned" in result

    def test_unwrap_dict_without_result_key_returns_as_is(self):
        result = _unwrap_kb_write_response({"some": "value"}, "update")
        assert result == {"some": "value"}


class TestWriteKbArticle:

    @pytest.mark.asyncio
    async def test_success_returns_inner_result(self):
        with patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_request.return_value = {"result": {"number": "KB0001234", "workflow_state": "published"}}

            result = await _write_kb_article(
                "PATCH",
                "https://test.service-now.com/api/now/table/kb_knowledge/abc123",
                {"workflow_state": "published"},
                "publish",
            )

            assert result == {"number": "KB0001234", "workflow_state": "published"}
            mock_request.assert_called_once_with(
                "https://test.service-now.com/api/now/table/kb_knowledge/abc123",
                method="PATCH",
                json_data={"workflow_state": "published"},
            )

    @pytest.mark.asyncio
    async def test_none_result_returns_fallback(self):
        with patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_request.return_value = None

            result = await _write_kb_article("PATCH", "http://x", {}, "update")
            assert "successful but no data returned" in result

    @pytest.mark.asyncio
    async def test_http_status_error_mapped(self):
        with patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_request.side_effect = _make_http_status_error(401)

            result = await _write_kb_article("PATCH", "http://x", {}, "publish")
            assert "Authentication failed" in result

    @pytest.mark.asyncio
    async def test_generic_exception_returns_request_failed(self):
        with patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_request.side_effect = Exception("Network error")

            result = await _write_kb_article("PATCH", "http://x", {}, "retire")
            assert "Request failed" in result


class TestGetKbArticleSysId:

    @pytest.mark.asyncio
    async def test_success_returns_sys_id(self):
        with patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_request.return_value = {"result": [{"sys_id": "abc123def456"}]}

            sys_id = await _get_kb_article_sys_id("KB0001234")

            assert sys_id == "abc123def456"
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_result_returns_none(self):
        with patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_request.return_value = {"result": []}

            assert await _get_kb_article_sys_id("KB9999999") is None

    @pytest.mark.asyncio
    async def test_none_response_returns_none(self):
        with patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_request.return_value = None

            assert await _get_kb_article_sys_id("KB0001234") is None

    @pytest.mark.asyncio
    async def test_none_result_key_returns_none(self):
        with patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_request.return_value = {"result": None}

            assert await _get_kb_article_sys_id("KB0001234") is None


class TestUpdateKnowledgeArticle:

    @pytest.mark.asyncio
    async def test_empty_update_data_returns_error(self):
        result = await update_knowledge_article("KB0001234", {})
        assert "No update data provided" in result

    @pytest.mark.asyncio
    async def test_article_not_found_returns_error(self):
        with patch('Table_Tools.kb_article_tools._get_kb_article_sys_id') as mock_sys_id:
            mock_sys_id.return_value = None

            result = await update_knowledge_article("KB9999999", {"short_description": "x"})
            assert "KB9999999" in result
            assert "not found" in result.lower()

    @pytest.mark.asyncio
    async def test_success_returns_updated_record(self):
        with patch('Table_Tools.kb_article_tools._get_kb_article_sys_id') as mock_sys_id, \
             patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_sys_id.return_value = "abc123"
            mock_request.return_value = {"result": {"number": "KB0001234", "short_description": "Updated"}}

            result = await update_knowledge_article("KB0001234", {"short_description": "Updated"})

            assert result["number"] == "KB0001234"
            kwargs = mock_request.call_args.kwargs
            assert kwargs["method"] == "PATCH"
            assert kwargs["json_data"] == {"short_description": "Updated"}


class TestGetKbArticleMeta:

    @pytest.mark.asyncio
    async def test_success_returns_sys_id_and_short_description(self):
        with patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_request.return_value = {"result": [{"sys_id": "abc123", "short_description": "Test article"}]}

            meta = await _get_kb_article_meta("KB0001234")

            assert meta["sys_id"] == "abc123"
            assert meta["short_description"] == "Test article"

    @pytest.mark.asyncio
    async def test_not_found_returns_none(self):
        with patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_request.return_value = {"result": []}

            assert await _get_kb_article_meta("KB9999999") is None

    @pytest.mark.asyncio
    async def test_none_response_returns_none(self):
        with patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_request.return_value = None

            assert await _get_kb_article_meta("KB0001234") is None


class TestCheckKbDuplicates:

    @pytest.mark.asyncio
    async def test_no_duplicates_returns_empty_list(self):
        with patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_request.return_value = {"result": [
                {"number": "KB0001234", "short_description": "Account self-registration", "workflow_state": "draft"}
            ]}

            result = await _check_kb_duplicates("Account self-registration", "KB0001234")
            assert result == []

    @pytest.mark.asyncio
    async def test_duplicate_in_draft_state_detected(self):
        with patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_request.return_value = {"result": [
                {"number": "KB0009999", "short_description": "Account self-registration", "workflow_state": "draft"}
            ]}

            result = await _check_kb_duplicates("Account self-registration", "KB0001234")
            assert len(result) == 1
            assert result[0]["number"] == "KB0009999"

    @pytest.mark.asyncio
    async def test_case_insensitive_exact_match(self):
        with patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_request.return_value = {"result": [
                {"number": "KB0009999", "short_description": "ACCOUNT SELF-REGISTRATION", "workflow_state": "published"}
            ]}

            result = await _check_kb_duplicates("Account self-registration", "KB0001234")
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_partial_match_not_returned(self):
        with patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_request.return_value = {"result": [
                {"number": "KB0009999", "short_description": "Account self-registration guide", "workflow_state": "published"}
            ]}

            result = await _check_kb_duplicates("Account self-registration", "KB0001234")
            assert result == []

    @pytest.mark.asyncio
    async def test_empty_result_returns_empty_list(self):
        with patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_request.return_value = {"result": []}

            assert await _check_kb_duplicates("Test", "KB0001234") == []

    @pytest.mark.asyncio
    async def test_none_response_returns_empty_list(self):
        with patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_request.return_value = None

            assert await _check_kb_duplicates("Test", "KB0001234") == []

    @pytest.mark.asyncio
    async def test_retired_duplicate_skipped(self):
        with patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_request.return_value = {"result": [
                {"number": "KB0009999", "short_description": "Account self-registration", "workflow_state": "retired"}
            ]}

            result = await _check_kb_duplicates("Account self-registration", "KB0001234")
            assert result == []

    @pytest.mark.asyncio
    async def test_outdated_duplicate_skipped(self):
        with patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_request.return_value = {"result": [
                {"number": "KB0009998", "short_description": "Account self-registration", "workflow_state": "outdated"}
            ]}

            result = await _check_kb_duplicates("Account self-registration", "KB0001234")
            assert result == []

    @pytest.mark.asyncio
    async def test_mixed_states_only_live_returned(self):
        with patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_request.return_value = {"result": [
                {"number": "KB1000001", "short_description": "Account self-registration", "workflow_state": "draft"},
                {"number": "KB1000002", "short_description": "Account self-registration", "workflow_state": "review"},
                {"number": "KB1000003", "short_description": "Account self-registration", "workflow_state": "published"},
                {"number": "KB1000004", "short_description": "Account self-registration", "workflow_state": "retired"},
                {"number": "KB1000005", "short_description": "Account self-registration", "workflow_state": "outdated"},
            ]}

            result = await _check_kb_duplicates("Account self-registration", "KB0001234")
            numbers = {r["number"] for r in result}
            assert numbers == {"KB1000001", "KB1000002", "KB1000003"}

    @pytest.mark.asyncio
    async def test_workflow_state_case_insensitive(self):
        with patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_request.return_value = {"result": [
                {"number": "KB0009999", "short_description": "Account self-registration", "workflow_state": "RETIRED"}
            ]}

            result = await _check_kb_duplicates("Account self-registration", "KB0001234")
            assert result == []


class TestPublishKnowledgeArticle:

    @pytest.mark.asyncio
    async def test_article_not_found_returns_error(self):
        with patch('Table_Tools.kb_article_tools._get_kb_article_meta') as mock_meta:
            mock_meta.return_value = None

            result = await publish_knowledge_article("KB9999999")
            assert "KB9999999" in result

    @pytest.mark.asyncio
    async def test_duplicate_found_blocks_publish(self):
        with patch('Table_Tools.kb_article_tools._get_kb_article_meta') as mock_meta, \
             patch('Table_Tools.kb_article_tools._check_kb_duplicates') as mock_dupes:
            mock_meta.return_value = {"sys_id": "abc123", "short_description": "Test article"}
            mock_dupes.return_value = [{"number": "KB0009999", "short_description": "Test article", "workflow_state": "draft"}]

            result = await publish_knowledge_article("KB0001234")

            assert result["success"] is False
            assert "Duplicate" in result["message"]
            assert len(result["duplicates"]) == 1

    @pytest.mark.asyncio
    async def test_success_posts_to_scripted_rest_publish(self):
        with patch('Table_Tools.kb_article_tools._get_kb_article_meta') as mock_meta, \
             patch('Table_Tools.kb_article_tools._check_kb_duplicates') as mock_dupes, \
             patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_meta.return_value = {"sys_id": "abc123", "short_description": "Test article"}
            mock_dupes.return_value = []
            mock_request.return_value = {"result": {"number": "KB0001234", "workflow_state": "published"}}

            result = await publish_knowledge_article("KB0001234")

            assert result["workflow_state"] == "published"
            call_url = mock_request.call_args.args[0]
            call_kwargs = mock_request.call_args.kwargs
            assert "/api/qonv/mateco_knowledge/articles/abc123/publish" in call_url
            assert call_kwargs["method"] == "POST"


class TestRetireKnowledgeArticle:

    @pytest.mark.asyncio
    async def test_article_not_found_returns_error(self):
        with patch('Table_Tools.kb_article_tools._get_kb_article_sys_id') as mock_sys_id:
            mock_sys_id.return_value = None

            result = await retire_knowledge_article("KB9999999")
            assert "KB9999999" in result

    @pytest.mark.asyncio
    async def test_success_posts_to_scripted_rest_retire(self):
        with patch('Table_Tools.kb_article_tools._get_kb_article_sys_id') as mock_sys_id, \
             patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_sys_id.return_value = "abc123"
            mock_request.return_value = {"result": {"number": "KB0001234", "workflow_state": "retired"}}

            result = await retire_knowledge_article("KB0001234")

            assert result["workflow_state"] == "retired"
            call_url = mock_request.call_args.args[0]
            call_kwargs = mock_request.call_args.kwargs
            assert "/api/qonv/mateco_knowledge/articles/abc123/retire" in call_url
            assert call_kwargs["method"] == "POST"


class TestCheckKbDuplicatesTool:

    @pytest.mark.asyncio
    async def test_empty_list_returns_empty_result(self):
        result = await check_kb_duplicates([])
        assert result == {"result": []}

    @pytest.mark.asyncio
    async def test_over_50_returns_error(self):
        result = await check_kb_duplicates([f"KB{i:07d}" for i in range(51)])
        assert "error" in result
        assert "50" in result["error"]

    @pytest.mark.asyncio
    async def test_single_article_no_duplicates(self):
        with patch('Table_Tools.kb_article_tools._get_kb_article_meta') as mock_meta, \
             patch('Table_Tools.kb_article_tools._check_kb_duplicates') as mock_dupes:
            mock_meta.return_value = {"sys_id": "abc", "short_description": "Onboarding"}
            mock_dupes.return_value = []

            result = await check_kb_duplicates(["KB0001234"])

            assert len(result["result"]) == 1
            assert result["result"][0] == {
                "number": "KB0001234",
                "has_duplicate": False,
                "duplicates": [],
            }

    @pytest.mark.asyncio
    async def test_single_article_with_duplicates(self):
        with patch('Table_Tools.kb_article_tools._get_kb_article_meta') as mock_meta, \
             patch('Table_Tools.kb_article_tools._check_kb_duplicates') as mock_dupes:
            mock_meta.return_value = {"sys_id": "abc", "short_description": "Onboarding"}
            mock_dupes.return_value = [
                {"number": "KB0009999", "workflow_state": "published", "short_description": "Onboarding", "kb_category": "x"},
            ]

            result = await check_kb_duplicates(["KB0001234"])

            entry = result["result"][0]
            assert entry["has_duplicate"] is True
            # Response is slimmed to number + workflow_state only
            assert entry["duplicates"] == [{"number": "KB0009999", "workflow_state": "published"}]

    @pytest.mark.asyncio
    async def test_missing_article_reports_error_entry(self):
        with patch('Table_Tools.kb_article_tools._get_kb_article_meta') as mock_meta:
            mock_meta.return_value = None

            result = await check_kb_duplicates(["KB9999999"])

            entry = result["result"][0]
            assert entry["number"] == "KB9999999"
            assert entry["has_duplicate"] is False
            assert "error" in entry

    @pytest.mark.asyncio
    async def test_mixed_batch_returns_per_article_status(self):
        async def fake_meta(num):
            if num == "KB_MISSING":
                return None
            return {"sys_id": f"sysid_{num}", "short_description": f"desc_{num}"}

        async def fake_dupes(short_desc, exclude_number):
            if exclude_number == "KB_DUP":
                return [{"number": "KB_OTHER", "workflow_state": "draft"}]
            return []

        with patch('Table_Tools.kb_article_tools._get_kb_article_meta', side_effect=fake_meta), \
             patch('Table_Tools.kb_article_tools._check_kb_duplicates', side_effect=fake_dupes):

            result = await check_kb_duplicates(["KB_CLEAN", "KB_DUP", "KB_MISSING"])

            by_num = {r["number"]: r for r in result["result"]}
            assert by_num["KB_CLEAN"]["has_duplicate"] is False
            assert by_num["KB_DUP"]["has_duplicate"] is True
            assert "error" in by_num["KB_MISSING"]


class TestNormalizePublishResult:

    def test_error_string_becomes_error_row(self):
        row = _normalize_publish_result("KB001", "Authentication failed during publish")
        assert row == {
            "number": "KB001",
            "status": "error",
            "message": "Authentication failed during publish",
        }

    def test_duplicate_block_becomes_blocked_row(self):
        row = _normalize_publish_result(
            "KB001",
            {"success": False, "message": "Duplicate KB article(s) found.", "duplicates": [{"number": "KB999"}]},
        )
        assert row["status"] == "blocked"
        assert row["blockers"] == [{"number": "KB999"}]

    def test_success_record_becomes_published_row(self):
        row = _normalize_publish_result(
            "KB001",
            {"number": "KB001", "sys_id": "abc", "workflow_state": "published", "short_description": "x"},
        )
        assert row == {"number": "KB001", "status": "published", "workflow_state": "published"}


class TestPublishKnowledgeArticles:

    @pytest.mark.asyncio
    async def test_empty_list_returns_empty_result(self):
        result = await publish_knowledge_articles([])
        assert result == {"result": []}

    @pytest.mark.asyncio
    async def test_over_20_returns_error(self):
        result = await publish_knowledge_articles([f"KB{i:07d}" for i in range(21)])
        assert "error" in result
        assert "20" in result["error"]

    @pytest.mark.asyncio
    async def test_mixed_batch_yields_per_article_status(self):
        async def fake_publish(num):
            if num == "KB_OK":
                return {"number": num, "workflow_state": "published", "sys_id": "s", "short_description": "x"}
            if num == "KB_DUP":
                return {"success": False, "message": "Duplicate KB article(s) found.", "duplicates": [{"number": "KB_OTHER", "workflow_state": "draft"}]}
            return "Authentication failed during publish"

        with patch('Table_Tools.kb_article_tools.publish_knowledge_article', side_effect=fake_publish):
            result = await publish_knowledge_articles(["KB_OK", "KB_DUP", "KB_ERR"])

        by_num = {r["number"]: r for r in result["result"]}
        assert by_num["KB_OK"]["status"] == "published"
        assert by_num["KB_DUP"]["status"] == "blocked"
        assert by_num["KB_DUP"]["blockers"] == [{"number": "KB_OTHER", "workflow_state": "draft"}]
        assert by_num["KB_ERR"]["status"] == "error"

    @pytest.mark.asyncio
    async def test_concurrency_cap_respected(self):
        """Verify Semaphore prevents more than `concurrency` in-flight publishes."""
        in_flight = 0
        max_seen = 0

        async def fake_publish(num):
            nonlocal in_flight, max_seen
            in_flight += 1
            max_seen = max(max_seen, in_flight)
            await asyncio.sleep(0.01)
            in_flight -= 1
            return {"number": num, "workflow_state": "published"}

        with patch('Table_Tools.kb_article_tools.publish_knowledge_article', side_effect=fake_publish):
            await publish_knowledge_articles([f"KB{i:03d}" for i in range(10)], concurrency=3)

        assert max_seen <= 3


class TestRoutesThroughUnifiedPipeline:
    """Verify write ops use make_nws_request write path (not GET path)."""

    @pytest.mark.asyncio
    async def test_publish_routes_through_make_nws_request(self):
        with patch('Table_Tools.kb_article_tools._get_kb_article_meta') as mock_meta, \
             patch('Table_Tools.kb_article_tools._check_kb_duplicates') as mock_dupes, \
             patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_meta.return_value = {"sys_id": "abc123", "short_description": "Test"}
            mock_dupes.return_value = []
            mock_request.return_value = {"result": {"number": "KB0001234"}}

            await publish_knowledge_article("KB0001234")

            mock_request.assert_called_once()
            call_kwargs = mock_request.call_args.kwargs
            assert call_kwargs["method"] == "POST"
            assert "/api/qonv/mateco_knowledge/articles/" in mock_request.call_args.args[0]

    @pytest.mark.asyncio
    async def test_retire_routes_through_make_nws_request(self):
        with patch('Table_Tools.kb_article_tools._get_kb_article_sys_id') as mock_sys_id, \
             patch('Table_Tools.kb_article_tools.make_nws_request') as mock_request:
            mock_sys_id.return_value = "abc123"
            mock_request.return_value = {"result": {"number": "KB0001234"}}

            await retire_knowledge_article("KB0001234")

            mock_request.assert_called_once()
            call_kwargs = mock_request.call_args.kwargs
            assert call_kwargs["method"] == "POST"
            assert "/api/qonv/mateco_knowledge/articles/" in mock_request.call_args.args[0]
