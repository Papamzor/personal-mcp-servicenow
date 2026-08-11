"""
Comprehensive tests for vtb_task_tools.py OAuth-only authentication flow.
Target: 90%+ line coverage, 75%+ branch coverage
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import httpx

# Import functions to test
from constants import ERROR_PRIVATE_TASK_WRITE_UNCONFIRMED
from http_layer.errors import ErrorCode, ServiceNowRequestError
from Table_Tools.vtb_task_tools import (
    _write_private_task,
    _unwrap_write_response,
    create_private_task,
    update_private_task,
    _get_task_sys_id,
    _prepare_task_create_data,
    _handle_http_error
)


def _make_http_status_error(status_code: int) -> httpx.HTTPStatusError:
    response = MagicMock()
    response.status_code = status_code
    return httpx.HTTPStatusError(str(status_code), request=MagicMock(), response=response)


class TestWritePrivateTask:
    """Test the unified write helper that wraps make_nws_request."""

    @pytest.mark.asyncio
    async def test_write_success_returns_inner_result(self):
        with patch('Table_Tools.vtb_task_tools.make_nws_request') as mock_request:
            mock_request.return_value = {
                "result": {"number": "VTB0001234", "short_description": "Test task"}
            }

            result = await _write_private_task(
                "POST",
                "https://test.service-now.com/api/now/table/vtb_task",
                {"short_description": "Test task"},
                "creation",
            )

            assert result["record"] == {"number": "VTB0001234", "short_description": "Test task"}
            mock_request.assert_called_once_with(
                "https://test.service-now.com/api/now/table/vtb_task",
                method="POST",
                json_data={"short_description": "Test task"},
            )

    @pytest.mark.asyncio
    async def test_write_no_result_returns_fallback_string(self):
        with patch('Table_Tools.vtb_task_tools.make_nws_request') as mock_request:
            mock_request.return_value = {}

            result = await _write_private_task(
                "POST",
                "https://test.service-now.com/api/now/table/vtb_task",
                {"short_description": "Test"},
                "creation",
            )

            assert result == {"error": {"code": "INTERNAL", "message": ERROR_PRIVATE_TASK_WRITE_UNCONFIRMED.format(operation="creation")}}
            assert "successful" not in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_write_none_result_returns_fallback_string(self):
        with patch('Table_Tools.vtb_task_tools.make_nws_request') as mock_request:
            mock_request.return_value = None

            result = await _write_private_task(
                "POST",
                "https://test.service-now.com/api/now/table/vtb_task",
                {"short_description": "Test"},
                "creation",
            )

            assert result == {"error": {"code": "INTERNAL", "message": ERROR_PRIVATE_TASK_WRITE_UNCONFIRMED.format(operation="creation")}}
            assert "successful" not in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_write_401_returns_auth_failed(self):
        with patch('Table_Tools.vtb_task_tools.make_nws_request') as mock_request:
            mock_request.side_effect = _make_http_status_error(401)

            result = await _write_private_task(
                "POST",
                "https://test.service-now.com/api/now/table/vtb_task",
                {"short_description": "Test"},
                "creation",
            )

            assert result["error"]["code"] == "AUTH"
            assert "Authentication failed" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_write_403_returns_access_denied(self):
        with patch('Table_Tools.vtb_task_tools.make_nws_request') as mock_request:
            mock_request.side_effect = _make_http_status_error(403)

            result = await _write_private_task(
                "PATCH",
                "https://test.service-now.com/api/now/table/vtb_task/abc",
                {"state": "3"},
                "update",
            )

            assert result["error"]["code"] == "FORBIDDEN"
            assert "Access denied" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_write_400_returns_invalid_request(self):
        with patch('Table_Tools.vtb_task_tools.make_nws_request') as mock_request:
            mock_request.side_effect = _make_http_status_error(400)

            result = await _write_private_task(
                "POST",
                "https://test.service-now.com/api/now/table/vtb_task",
                {"short_description": "Test"},
                "creation",
            )

            assert result["error"]["code"] == "VALIDATION"
            assert "Invalid request" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_write_404_returns_not_found(self):
        with patch('Table_Tools.vtb_task_tools.make_nws_request') as mock_request:
            mock_request.side_effect = _make_http_status_error(404)

            result = await _write_private_task(
                "PATCH",
                "https://test.service-now.com/api/now/table/vtb_task/missing",
                {"state": "3"},
                "update",
            )

            assert result["error"]["code"] == "NOT_FOUND"
            assert "not found" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_write_500_returns_server_error(self):
        with patch('Table_Tools.vtb_task_tools.make_nws_request') as mock_request:
            mock_request.side_effect = _make_http_status_error(500)

            result = await _write_private_task(
                "POST",
                "https://test.service-now.com/api/now/table/vtb_task",
                {"short_description": "Test"},
                "creation",
            )

            assert result["error"]["code"] == "HTTP"
            assert "server error" in result["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_write_generic_exception_returns_request_failed(self):
        with patch('Table_Tools.vtb_task_tools.make_nws_request') as mock_request:
            mock_request.side_effect = Exception("Network error")

            result = await _write_private_task(
                "POST",
                "https://test.service-now.com/api/now/table/vtb_task",
                {"short_description": "Test"},
                "deletion",
            )

            assert result["error"]["code"] == "INTERNAL"
            assert "request failed" in result["error"]["message"].lower()


class TestUnwrapWriteResponse:
    """Test the response unwrapper helper."""

    def test_unwrap_with_inner_result(self):
        result = _unwrap_write_response({"result": {"number": "VTB0001"}}, "creation")
        assert result["record"] == {"number": "VTB0001"}

    def test_unwrap_empty_dict_is_unconfirmed_not_success(self):
        """An empty write response cannot establish that the write landed."""
        result = _unwrap_write_response({}, "creation")
        assert result == {"error": {"code": "INTERNAL", "message": ERROR_PRIVATE_TASK_WRITE_UNCONFIRMED.format(operation="creation")}}
        assert "successful" not in result["error"]["message"]

    def test_unwrap_none_is_unconfirmed_not_success(self):
        result = _unwrap_write_response(None, "update")
        assert result == {"error": {"code": "INTERNAL", "message": ERROR_PRIVATE_TASK_WRITE_UNCONFIRMED.format(operation="update")}}
        assert "successful" not in result["error"]["message"]

    def test_unwrap_dict_without_result_key_is_unconfirmed(self):
        """A 2xx body with no `result` key is not a confirmed record — unconfirmed."""
        result = _unwrap_write_response({"some": "value"}, "creation")
        assert result["error"]["code"] == "INTERNAL"


class TestHttpErrorHandler:
    """Test HTTP error handling function."""

    @pytest.mark.parametrize(
        "status_code, operation, expected, case_insensitive",
        [
            (401, "creation", "Authentication failed", False),
            (403, "update", "Access denied", False),
            (400, "creation", "Invalid request", False),
            (404, "retrieval", "not found", False),
            (503, "update", "server error", True),
        ],
    )
    def test_handle_http_error(self, status_code, operation, expected, case_insensitive):
        result = _handle_http_error(_make_http_status_error(status_code), operation)
        message = result["error"]["message"]
        haystack = message.lower() if case_insensitive else message
        assert expected in haystack


class TestTaskDataPreparation:
    """Test task data preparation function."""

    def test_prepare_task_create_data_minimal(self):
        """Test preparing task data with minimal required fields."""
        task_data = {"short_description": "Test task"}

        result = _prepare_task_create_data(task_data)

        assert result["short_description"] == "Test task"
        assert result["state"] == "1"  # Default state
        assert result["priority"] == "3"  # Default priority

    def test_prepare_task_create_data_with_optional_fields(self):
        """Test preparing task data with optional fields."""
        task_data = {
            "short_description": "Test task",
            "description": "Detailed description",
            "priority": "1",
            "state": "2",
            "assigned_to": "admin",
            "assignment_group": "IT Support",
            "due_date": "2025-12-31",
            "parent": "INC0001234",
            "comments": "Test comment",
            "work_notes": "Work notes here"
        }

        result = _prepare_task_create_data(task_data)

        assert result["short_description"] == "Test task"
        assert result["description"] == "Detailed description"
        assert result["priority"] == "1"
        assert result["state"] == "2"
        assert result["assigned_to"] == "admin"
        assert result["assignment_group"] == "IT Support"
        assert result["due_date"] == "2025-12-31"
        assert result["parent"] == "INC0001234"
        assert result["comments"] == "Test comment"
        assert result["work_notes"] == "Work notes here"

    def test_prepare_task_create_data_ignore_extra_fields(self):
        """Test that extra fields not in optional list are ignored."""
        task_data = {
            "short_description": "Test task",
            "random_field": "Should be ignored",
            "another_field": 123
        }

        result = _prepare_task_create_data(task_data)

        assert "random_field" not in result
        assert "another_field" not in result
        assert result["short_description"] == "Test task"


class TestTaskSysIdRetrieval:
    """Test sys_id retrieval function."""

    @pytest.mark.asyncio
    async def test_get_task_sys_id_success(self):
        """Test successful sys_id retrieval."""
        with patch('Table_Tools.vtb_task_tools.make_nws_request') as mock_request:
            mock_request.return_value = {
                "result": [{"sys_id": "abc123def456"}]
            }

            sys_id = await _get_task_sys_id("VTB0001234")

            assert sys_id == "abc123def456"
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_task_sys_id_not_found(self):
        """Test sys_id retrieval when task not found."""
        with patch('Table_Tools.vtb_task_tools.make_nws_request') as mock_request:
            mock_request.return_value = {"result": []}

            sys_id = await _get_task_sys_id("VTB9999999")

            assert sys_id is None

    @pytest.mark.asyncio
    async def test_get_task_sys_id_read_failure_propagates(self):
        """Decision (d): None means absent, so a failed read must not return None.

        This mocked None and asserted None came back, which the transport can no
        longer produce -- a failed GET raises for this module. None here is what
        made update_private_task report the task as missing on a timeout.
        """
        with patch('Table_Tools.vtb_task_tools.make_nws_request',
                   side_effect=ServiceNowRequestError(
                       ErrorCode.TIMEOUT, "ServiceNow request timed out", retryable=True)):
            with pytest.raises(ServiceNowRequestError):
                await _get_task_sys_id("VTB0001234")

    @pytest.mark.asyncio
    async def test_get_task_sys_id_invalid_response(self):
        """Test sys_id retrieval with invalid response."""
        with patch('Table_Tools.vtb_task_tools.make_nws_request') as mock_request:
            mock_request.return_value = {"result": None}

            sys_id = await _get_task_sys_id("VTB0001234")

            assert sys_id is None


class TestCreatePrivateTask:
    """Test create_private_task function with OAuth authentication."""

    @pytest.mark.asyncio
    async def test_create_private_task_success(self):
        """Test successful private task creation."""
        with patch('Table_Tools.vtb_task_tools.make_nws_request') as mock_request:
            mock_request.return_value = {
                "result": {
                    "number": "VTB0001234",
                    "short_description": "Test task",
                    "state": "1",
                }
            }

            task_data = {"short_description": "Test task"}
            result = await create_private_task(task_data)

            assert result["record"]["number"] == "VTB0001234"
            mock_request.assert_called_once()
            kwargs = mock_request.call_args.kwargs
            assert kwargs["method"] == "POST"

    @pytest.mark.asyncio
    async def test_create_private_task_missing_short_description(self):
        """Test task creation fails without short_description."""
        task_data = {"description": "Missing short description"}

        result = await create_private_task(task_data)

        assert result["error"]["code"] == "VALIDATION"
        assert "short_description is required" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_create_private_task_with_all_fields(self):
        """Test task creation with all optional fields."""
        with patch('Table_Tools.vtb_task_tools.make_nws_request') as mock_request:
            mock_request.return_value = {"result": {"number": "VTB0001234"}}

            task_data = {
                "short_description": "Complete task",
                "description": "Full description",
                "priority": "1",
                "state": "2",
                "assigned_to": "admin",
                "assignment_group": "IT",
                "due_date": "2025-12-31"
            }

            result = await create_private_task(task_data)

            assert result["record"]["number"] == "VTB0001234"
            mock_request.assert_called_once()


class TestUpdatePrivateTask:
    """Test update_private_task function with OAuth authentication."""

    @pytest.mark.asyncio
    async def test_update_private_task_success(self):
        """Test successful private task update."""
        with patch('Table_Tools.vtb_task_tools._get_task_sys_id') as mock_sys_id, \
             patch('Table_Tools.vtb_task_tools.make_nws_request') as mock_request:

            mock_sys_id.return_value = "abc123def456"
            mock_request.return_value = {
                "result": {"number": "VTB0001234", "state": "3"}
            }

            update_data = {"state": "3"}
            result = await update_private_task("VTB0001234", update_data)

            assert result["record"]["number"] == "VTB0001234"
            assert result["record"]["state"] == "3"
            mock_sys_id.assert_called_once_with("VTB0001234")
            mock_request.assert_called_once()
            kwargs = mock_request.call_args.kwargs
            assert kwargs["method"] == "PATCH"

    @pytest.mark.asyncio
    async def test_update_private_task_no_update_data(self):
        """Test update fails without update data."""
        result = await update_private_task("VTB0001234", {})

        assert result["error"]["code"] == "VALIDATION"
        assert "No update data provided" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_update_private_task_not_found(self):
        """Test update fails when task not found."""
        with patch('Table_Tools.vtb_task_tools._get_task_sys_id') as mock_sys_id:
            mock_sys_id.return_value = None

            update_data = {"state": "3"}
            result = await update_private_task("VTB9999999", update_data)

            assert result["error"]["code"] == "NOT_FOUND"
            assert "not found" in result["error"]["message"]
