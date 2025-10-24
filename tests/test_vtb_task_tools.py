"""
Comprehensive tests for vtb_task_tools.py OAuth-only authentication flow.
Target: 90%+ line coverage, 75%+ branch coverage
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import httpx

# Import functions to test
from Table_Tools.vtb_task_tools import (
    _get_authenticated_headers,
    _make_authenticated_request,
    similar_private_tasks_for_text,
    get_short_desc_for_private_task,
    similar_private_tasks_for_private_task,
    get_private_task_details,
    create_private_task,
    update_private_task,
    get_private_tasks_by_filter,
    _get_task_sys_id,
    _prepare_task_create_data,
    _handle_http_error
)


class TestAuthenticationHelpers:
    """Test OAuth-only authentication helper functions."""

    @pytest.mark.asyncio
    async def test_get_authenticated_headers_success(self):
        """Test getting OAuth authentication headers successfully."""
        with patch('oauth_client.get_oauth_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_auth_headers = AsyncMock(return_value={
                "Authorization": "Bearer test_token_123",
                "Content-Type": "application/json",
                "Accept": "application/json"
            })
            mock_get_client.return_value = mock_client

            headers = await _get_authenticated_headers()

            assert headers["Authorization"] == "Bearer test_token_123"
            assert headers["Content-Type"] == "application/json"
            mock_get_client.assert_called_once()
            mock_client.get_auth_headers.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_authenticated_request_success(self):
        """Test successful OAuth authenticated request."""
        with patch('Table_Tools.vtb_task_tools._get_authenticated_headers') as mock_headers, \
             patch('Table_Tools.vtb_task_tools.httpx.AsyncClient') as mock_client_class:

            mock_headers.return_value = {"Authorization": "Bearer test_token"}

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "result": {"number": "VTB0001234", "short_description": "Test task"}
            }

            mock_client = MagicMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await _make_authenticated_request(
                "POST",
                "https://test.service-now.com/api/now/table/vtb_task",
                {"short_description": "Test task"},
                "creation"
            )

            assert result == {"number": "VTB0001234", "short_description": "Test task"}
            mock_headers.assert_called_once()
            mock_client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_authenticated_request_no_result(self):
        """Test authenticated request with no result data."""
        with patch('Table_Tools.vtb_task_tools._get_authenticated_headers') as mock_headers, \
             patch('Table_Tools.vtb_task_tools.httpx.AsyncClient') as mock_client_class:

            mock_headers.return_value = {"Authorization": "Bearer test_token"}

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}

            mock_client = MagicMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await _make_authenticated_request(
                "POST",
                "https://test.service-now.com/api/now/table/vtb_task",
                {"short_description": "Test"},
                "creation"
            )

            assert "successful but no data returned" in result

    @pytest.mark.asyncio
    async def test_make_authenticated_request_401_error(self):
        """Test authenticated request with 401 authentication error."""
        with patch('Table_Tools.vtb_task_tools._get_authenticated_headers') as mock_headers, \
             patch('Table_Tools.vtb_task_tools.httpx.AsyncClient') as mock_client_class:

            mock_headers.return_value = {"Authorization": "Bearer test_token"}

            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_error = httpx.HTTPStatusError("401", request=MagicMock(), response=mock_response)

            mock_client = MagicMock()
            mock_client.request = AsyncMock(side_effect=mock_error)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await _make_authenticated_request(
                "POST",
                "https://test.service-now.com/api/now/table/vtb_task",
                {"short_description": "Test"},
                "creation"
            )

            assert "Authentication failed" in result

    @pytest.mark.asyncio
    async def test_make_authenticated_request_403_error(self):
        """Test authenticated request with 403 access denied error."""
        with patch('Table_Tools.vtb_task_tools._get_authenticated_headers') as mock_headers, \
             patch('Table_Tools.vtb_task_tools.httpx.AsyncClient') as mock_client_class:

            mock_headers.return_value = {"Authorization": "Bearer test_token"}

            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_error = httpx.HTTPStatusError("403", request=MagicMock(), response=mock_response)

            mock_client = MagicMock()
            mock_client.request = AsyncMock(side_effect=mock_error)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await _make_authenticated_request(
                "POST",
                "https://test.service-now.com/api/now/table/vtb_task",
                {"short_description": "Test"},
                "update"
            )

            assert "Access denied" in result

    @pytest.mark.asyncio
    async def test_make_authenticated_request_404_error(self):
        """Test authenticated request with 404 not found error."""
        with patch('Table_Tools.vtb_task_tools._get_authenticated_headers') as mock_headers, \
             patch('Table_Tools.vtb_task_tools.httpx.AsyncClient') as mock_client_class:

            mock_headers.return_value = {"Authorization": "Bearer test_token"}

            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_error = httpx.HTTPStatusError("404", request=MagicMock(), response=mock_response)

            mock_client = MagicMock()
            mock_client.request = AsyncMock(side_effect=mock_error)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await _make_authenticated_request(
                "GET",
                "https://test.service-now.com/api/now/table/vtb_task/invalid",
                operation="retrieval"
            )

            assert "not found" in result

    @pytest.mark.asyncio
    async def test_make_authenticated_request_500_error(self):
        """Test authenticated request with 500 server error."""
        with patch('Table_Tools.vtb_task_tools._get_authenticated_headers') as mock_headers, \
             patch('Table_Tools.vtb_task_tools.httpx.AsyncClient') as mock_client_class:

            mock_headers.return_value = {"Authorization": "Bearer test_token"}

            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_error = httpx.HTTPStatusError("500", request=MagicMock(), response=mock_response)

            mock_client = MagicMock()
            mock_client.request = AsyncMock(side_effect=mock_error)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await _make_authenticated_request(
                "POST",
                "https://test.service-now.com/api/now/table/vtb_task",
                {"short_description": "Test"},
                "creation"
            )

            assert "server error" in result.lower()

    @pytest.mark.asyncio
    async def test_make_authenticated_request_generic_exception(self):
        """Test authenticated request with generic exception."""
        with patch('Table_Tools.vtb_task_tools._get_authenticated_headers') as mock_headers, \
             patch('Table_Tools.vtb_task_tools.httpx.AsyncClient') as mock_client_class:

            mock_headers.return_value = {"Authorization": "Bearer test_token"}

            mock_client = MagicMock()
            mock_client.request = AsyncMock(side_effect=Exception("Network error"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await _make_authenticated_request(
                "POST",
                "https://test.service-now.com/api/now/table/vtb_task",
                {"short_description": "Test"},
                "deletion"
            )

            assert "request failed" in result.lower()


class TestHttpErrorHandler:
    """Test HTTP error handling function."""

    def test_handle_http_error_401(self):
        """Test handling 401 authentication error."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        error = httpx.HTTPStatusError("401", request=MagicMock(), response=mock_response)

        result = _handle_http_error(error, "creation")

        assert "Authentication failed" in result

    def test_handle_http_error_403(self):
        """Test handling 403 access denied error."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        error = httpx.HTTPStatusError("403", request=MagicMock(), response=mock_response)

        result = _handle_http_error(error, "update")

        assert "Access denied" in result

    def test_handle_http_error_400(self):
        """Test handling 400 bad request error."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        error = httpx.HTTPStatusError("400", request=MagicMock(), response=mock_response)

        result = _handle_http_error(error, "creation")

        assert "Invalid request" in result

    def test_handle_http_error_404(self):
        """Test handling 404 not found error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        error = httpx.HTTPStatusError("404", request=MagicMock(), response=mock_response)

        result = _handle_http_error(error, "retrieval")

        assert "not found" in result

    def test_handle_http_error_unknown(self):
        """Test handling unknown HTTP error code."""
        mock_response = MagicMock()
        mock_response.status_code = 503
        error = httpx.HTTPStatusError("503", request=MagicMock(), response=mock_response)

        result = _handle_http_error(error, "update")

        assert "server error" in result.lower()


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
    async def test_get_task_sys_id_no_data(self):
        """Test sys_id retrieval with no data."""
        with patch('Table_Tools.vtb_task_tools.make_nws_request') as mock_request:
            mock_request.return_value = None

            sys_id = await _get_task_sys_id("VTB0001234")

            assert sys_id is None

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
        with patch('Table_Tools.vtb_task_tools._make_authenticated_request') as mock_request:
            mock_request.return_value = {
                "number": "VTB0001234",
                "short_description": "Test task",
                "state": "1"
            }

            task_data = {"short_description": "Test task"}
            result = await create_private_task(task_data)

            assert result["number"] == "VTB0001234"
            mock_request.assert_called_once()
            args = mock_request.call_args
            assert args[0][0] == "POST"

    @pytest.mark.asyncio
    async def test_create_private_task_missing_short_description(self):
        """Test task creation fails without short_description."""
        task_data = {"description": "Missing short description"}

        result = await create_private_task(task_data)

        assert "short_description is required" in result

    @pytest.mark.asyncio
    async def test_create_private_task_with_all_fields(self):
        """Test task creation with all optional fields."""
        with patch('Table_Tools.vtb_task_tools._make_authenticated_request') as mock_request:
            mock_request.return_value = {"number": "VTB0001234"}

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

            assert result["number"] == "VTB0001234"
            mock_request.assert_called_once()


class TestUpdatePrivateTask:
    """Test update_private_task function with OAuth authentication."""

    @pytest.mark.asyncio
    async def test_update_private_task_success(self):
        """Test successful private task update."""
        with patch('Table_Tools.vtb_task_tools._get_task_sys_id') as mock_sys_id, \
             patch('Table_Tools.vtb_task_tools._make_authenticated_request') as mock_request:

            mock_sys_id.return_value = "abc123def456"
            mock_request.return_value = {
                "number": "VTB0001234",
                "state": "3"
            }

            update_data = {"state": "3"}
            result = await update_private_task("VTB0001234", update_data)

            assert result["number"] == "VTB0001234"
            assert result["state"] == "3"
            mock_sys_id.assert_called_once_with("VTB0001234")
            mock_request.assert_called_once()
            args = mock_request.call_args
            assert args[0][0] == "PUT"

    @pytest.mark.asyncio
    async def test_update_private_task_no_update_data(self):
        """Test update fails without update data."""
        result = await update_private_task("VTB0001234", {})

        assert "No update data provided" in result

    @pytest.mark.asyncio
    async def test_update_private_task_not_found(self):
        """Test update fails when task not found."""
        with patch('Table_Tools.vtb_task_tools._get_task_sys_id') as mock_sys_id:
            mock_sys_id.return_value = None

            update_data = {"state": "3"}
            result = await update_private_task("VTB9999999", update_data)

            assert "not found" in result


class TestQueryFunctions:
    """Test private task query functions."""

    @pytest.mark.asyncio
    async def test_similar_private_tasks_for_text(self):
        """Test finding similar private tasks by text."""
        with patch('Table_Tools.vtb_task_tools.extract_keywords') as mock_keywords, \
             patch('Table_Tools.vtb_task_tools.make_nws_request') as mock_request:

            mock_keywords.return_value = ["audit", "postmortem"]
            mock_request.return_value = {
                "result": [{"number": "VTB0001234", "short_description": "Audit task"}]
            }

            result = await similar_private_tasks_for_text("audit postmortem")

            assert result["result"][0]["number"] == "VTB0001234"
            mock_keywords.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_short_desc_for_private_task(self):
        """Test getting private task short description."""
        with patch('Table_Tools.vtb_task_tools.make_nws_request') as mock_request:
            mock_request.return_value = {
                "result": [{"short_description": "Test task"}]
            }

            result = await get_short_desc_for_private_task("VTB0001234")

            assert result["result"][0]["short_description"] == "Test task"

    @pytest.mark.asyncio
    async def test_get_private_task_details(self):
        """Test getting detailed private task information."""
        with patch('Table_Tools.vtb_task_tools.make_nws_request') as mock_request:
            mock_request.return_value = {
                "result": [{
                    "number": "VTB0001234",
                    "short_description": "Test task",
                    "priority": "2",
                    "state": "1"
                }]
            }

            result = await get_private_task_details("VTB0001234")

            assert result["number"] == "VTB0001234"
            assert result["priority"] == "2"

    @pytest.mark.asyncio
    async def test_get_private_tasks_by_filter(self):
        """Test getting private tasks with filters."""
        with patch('Table_Tools.vtb_task_tools.make_nws_request') as mock_request:
            mock_request.return_value = {
                "result": [{"number": "VTB0001234", "state": "1"}]
            }

            filters = {"state": "1", "priority": "2"}
            result = await get_private_tasks_by_filter(filters)

            assert result["result"][0]["number"] == "VTB0001234"
            mock_request.assert_called_once()
