"""
Comprehensive tests for consolidated_tools.py
Target: 80%+ line coverage, 60%+ branch coverage
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from typing import Dict, Any

from Table_Tools.consolidated_tools import (
    _get_error_message,
    # Incident tools
    similar_incidents_for_text,
    get_short_desc_for_incident,
    similar_incidents_for_incident,
    get_incident_details,
    get_incidents_by_filter,
    get_priority_incidents,
    # Change tools
    similar_changes_for_text,
    get_short_desc_for_change,
    similar_changes_for_change,
    get_change_details,
    # Request item tools
    similar_request_items_for_text,
    get_short_desc_for_request_item,
    similar_request_items_for_request_item,
    get_request_item_details,
    # Universal request tools
    similar_universal_requests_for_text,
    get_short_desc_for_universal_request,
    similar_universal_requests_for_universal_request,
    get_universal_request_details,
    # Knowledge tools
    similar_knowledge_for_text,
    get_knowledge_details,
    get_knowledge_by_category,
    get_active_knowledge_articles,
    # Private task tools
    similar_private_tasks_for_text,
    get_short_desc_for_private_task,
    similar_private_tasks_for_private_task,
    get_private_task_details,
    get_private_tasks_by_filter,
    # SLA tools
    similar_slas_for_text,
    get_slas_for_task,
    get_sla_details,
    get_breaching_slas,
    get_breached_slas,
    get_slas_by_stage,
    get_active_slas,
    get_sla_performance_summary,
    get_recent_breached_slas,
    get_critical_sla_status,
)


class TestHelperFunctions:
    """Test helper functions."""

    def test_get_error_message_with_table_config(self):
        """Test getting error message for configured table."""
        with patch('Table_Tools.consolidated_tools.TABLE_ERROR_MESSAGES', {"incident": "Incident not found"}):
            result = _get_error_message("incident")
            assert result == "Incident not found"

    def test_get_error_message_default(self):
        """Test getting default error message for unconfigured table."""
        with patch('Table_Tools.consolidated_tools.TABLE_ERROR_MESSAGES', {}):
            result = _get_error_message("unknown_table")
            assert result == "Record not found."

    def test_get_error_message_custom_default(self):
        """Test getting custom default error message."""
        with patch('Table_Tools.consolidated_tools.TABLE_ERROR_MESSAGES', {}):
            result = _get_error_message("unknown_table", "Custom error")
            assert result == "Custom error"


class TestIncidentTools:
    """Test incident tool functions."""

    @pytest.mark.asyncio
    async def test_similar_incidents_for_text(self):
        """Test finding similar incidents by text."""
        with patch('Table_Tools.consolidated_tools.query_table_by_text') as mock_query:
            mock_query.return_value = {"result": [{"number": "INC001"}]}

            result = await similar_incidents_for_text("database issue")

            mock_query.assert_called_once_with("incident", "database issue")
            assert result["result"] is not None

    @pytest.mark.asyncio
    async def test_get_short_desc_for_incident(self):
        """Test getting incident description."""
        with patch('Table_Tools.consolidated_tools.get_record_description') as mock_desc:
            mock_desc.return_value = {"result": [{"short_description": "Test"}]}

            result = await get_short_desc_for_incident("INC001")

            mock_desc.assert_called_once_with("incident", "INC001")
            assert result is not None

    @pytest.mark.asyncio
    async def test_similar_incidents_for_incident(self):
        """Test finding similar incidents."""
        with patch('Table_Tools.consolidated_tools.find_similar_records') as mock_similar:
            mock_similar.return_value = {"result": [{"number": "INC002"}]}

            result = await similar_incidents_for_incident("INC001")

            mock_similar.assert_called_once_with("incident", "INC001")
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_incident_details(self):
        """Test getting incident details."""
        with patch('Table_Tools.consolidated_tools.get_record_details') as mock_details:
            mock_details.return_value = {"result": [{"number": "INC001", "priority": "1"}]}

            result = await get_incident_details("INC001")

            mock_details.assert_called_once_with("incident", "INC001")
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_incidents_by_filter(self):
        """Test getting incidents by filter."""
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": [{"number": "INC001"}]}

            result = await get_incidents_by_filter({"priority": "1"})

            mock_query.assert_called_once()
            args = mock_query.call_args
            assert args[0][0] == "incident"
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_priority_incidents(self):
        """Test getting priority incidents."""
        with patch('Table_Tools.consolidated_tools.get_records_by_priority') as mock_priority:
            mock_priority.return_value = {"result": [{"number": "INC001", "priority": "1"}]}

            result = await get_priority_incidents(["1", "2"], state="New")

            mock_priority.assert_called_once_with("incident", ["1", "2"], {"state": "New"}, detailed=True)
            assert result is not None


class TestChangeTools:
    """Test change tool functions."""

    @pytest.mark.asyncio
    async def test_similar_changes_for_text(self):
        """Test finding similar changes by text."""
        with patch('Table_Tools.consolidated_tools.query_table_by_text') as mock_query:
            mock_query.return_value = {"result": [{"number": "CHG001"}]}

            result = await similar_changes_for_text("upgrade")

            mock_query.assert_called_once_with("change_request", "upgrade")
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_short_desc_for_change(self):
        """Test getting change description."""
        with patch('Table_Tools.consolidated_tools.get_record_description') as mock_desc:
            mock_desc.return_value = {"result": [{"short_description": "Test"}]}

            result = await get_short_desc_for_change("CHG001")

            mock_desc.assert_called_once_with("change_request", "CHG001")
            assert result is not None

    @pytest.mark.asyncio
    async def test_similar_changes_for_change(self):
        """Test finding similar changes."""
        with patch('Table_Tools.consolidated_tools.find_similar_records') as mock_similar:
            mock_similar.return_value = {"result": [{"number": "CHG002"}]}

            result = await similar_changes_for_change("CHG001")

            mock_similar.assert_called_once_with("change_request", "CHG001")
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_change_details(self):
        """Test getting change details."""
        with patch('Table_Tools.consolidated_tools.get_record_details') as mock_details:
            mock_details.return_value = {"result": [{"number": "CHG001"}]}

            result = await get_change_details("CHG001")

            mock_details.assert_called_once_with("change_request", "CHG001")
            assert result is not None


class TestRequestItemTools:
    """Test request item tool functions."""

    @pytest.mark.asyncio
    async def test_similar_request_items_for_text(self):
        """Test finding similar request items by text."""
        with patch('Table_Tools.consolidated_tools.query_table_by_text') as mock_query:
            mock_query.return_value = {"result": [{"number": "REQ001"}]}

            result = await similar_request_items_for_text("laptop")

            mock_query.assert_called_once_with("sc_req_item", "laptop")
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_short_desc_for_request_item(self):
        """Test getting request item description."""
        with patch('Table_Tools.consolidated_tools.get_record_description') as mock_desc:
            mock_desc.return_value = {"result": [{"short_description": "Test"}]}

            result = await get_short_desc_for_request_item("REQ001")

            mock_desc.assert_called_once_with("sc_req_item", "REQ001")
            assert result is not None

    @pytest.mark.asyncio
    async def test_similar_request_items_for_request_item(self):
        """Test finding similar request items."""
        with patch('Table_Tools.consolidated_tools.find_similar_records') as mock_similar:
            mock_similar.return_value = {"result": [{"number": "REQ002"}]}

            result = await similar_request_items_for_request_item("REQ001")

            mock_similar.assert_called_once_with("sc_req_item", "REQ001")
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_request_item_details(self):
        """Test getting request item details."""
        with patch('Table_Tools.consolidated_tools.get_record_details') as mock_details:
            mock_details.return_value = {"result": [{"number": "REQ001"}]}

            result = await get_request_item_details("REQ001")

            mock_details.assert_called_once_with("sc_req_item", "REQ001")
            assert result is not None


class TestUniversalRequestTools:
    """Test universal request tool functions."""

    @pytest.mark.asyncio
    async def test_similar_universal_requests_for_text(self):
        """Test finding similar universal requests by text."""
        with patch('Table_Tools.consolidated_tools.query_table_by_text') as mock_query:
            mock_query.return_value = {"result": [{"number": "UR001"}]}

            result = await similar_universal_requests_for_text("access")

            mock_query.assert_called_once_with("universal_request", "access")
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_short_desc_for_universal_request(self):
        """Test getting universal request description."""
        with patch('Table_Tools.consolidated_tools.get_record_description') as mock_desc:
            mock_desc.return_value = {"result": [{"short_description": "Test"}]}

            result = await get_short_desc_for_universal_request("UR001")

            mock_desc.assert_called_once_with("universal_request", "UR001")
            assert result is not None

    @pytest.mark.asyncio
    async def test_similar_universal_requests_for_universal_request(self):
        """Test finding similar universal requests."""
        with patch('Table_Tools.consolidated_tools.find_similar_records') as mock_similar:
            mock_similar.return_value = {"result": [{"number": "UR002"}]}

            result = await similar_universal_requests_for_universal_request("UR001")

            mock_similar.assert_called_once_with("universal_request", "UR001")
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_universal_request_details(self):
        """Test getting universal request details."""
        with patch('Table_Tools.consolidated_tools.get_record_details') as mock_details:
            mock_details.return_value = {"result": [{"number": "UR001"}]}

            result = await get_universal_request_details("UR001")

            mock_details.assert_called_once_with("universal_request", "UR001")
            assert result is not None


class TestKnowledgeTools:
    """Test knowledge tool functions."""

    @pytest.mark.asyncio
    async def test_similar_knowledge_for_text_simple(self):
        """Test finding similar knowledge by text."""
        with patch('Table_Tools.consolidated_tools.query_table_by_text') as mock_query:
            mock_query.return_value = {"result": [{"number": "KB001"}]}

            result = await similar_knowledge_for_text("password reset")

            mock_query.assert_called_once_with("kb_knowledge", "password reset")
            assert result is not None

    @pytest.mark.asyncio
    async def test_similar_knowledge_for_text_with_category(self):
        """Test finding knowledge with category filter."""
        with patch('Table_Tools.consolidated_tools.query_table_with_generic_filters') as mock_query:
            mock_query.return_value = {"result": [{"number": "KB001"}]}

            result = await similar_knowledge_for_text("test", category="IT")

            mock_query.assert_called_once()
            args = mock_query.call_args
            assert args[0][0] == "kb_knowledge"
            assert "kb_category" in args[0][1]

    @pytest.mark.asyncio
    async def test_similar_knowledge_for_text_with_kb_base(self):
        """Test finding knowledge with kb_base filter."""
        with patch('Table_Tools.consolidated_tools.query_table_with_generic_filters') as mock_query:
            mock_query.return_value = {"result": [{"number": "KB001"}]}

            result = await similar_knowledge_for_text("test", kb_base="IT_KB")

            mock_query.assert_called_once()
            args = mock_query.call_args
            assert args[0][0] == "kb_knowledge"
            assert "kb_knowledge_base" in args[0][1]

    @pytest.mark.asyncio
    async def test_get_knowledge_details(self):
        """Test getting knowledge details."""
        with patch('Table_Tools.consolidated_tools.get_record_details') as mock_details:
            mock_details.return_value = {"result": [{"number": "KB001"}]}

            result = await get_knowledge_details("KB001")

            mock_details.assert_called_once_with("kb_knowledge", "KB001")
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_knowledge_by_category(self):
        """Test getting knowledge by category."""
        with patch('Table_Tools.consolidated_tools.query_table_with_generic_filters') as mock_query:
            mock_query.return_value = {"result": [{"number": "KB001"}]}

            result = await get_knowledge_by_category("IT")

            mock_query.assert_called_once_with("kb_knowledge", {"kb_category": "IT"})
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_knowledge_by_category_with_kb_base(self):
        """Test getting knowledge by category with kb_base."""
        with patch('Table_Tools.consolidated_tools.query_table_with_generic_filters') as mock_query:
            mock_query.return_value = {"result": [{"number": "KB001"}]}

            result = await get_knowledge_by_category("IT", kb_base="IT_KB")

            mock_query.assert_called_once()
            args = mock_query.call_args
            filters = args[0][1]
            assert filters["kb_category"] == "IT"
            assert filters["kb_knowledge_base"] == "IT_KB"

    @pytest.mark.asyncio
    async def test_get_active_knowledge_articles(self):
        """Test getting active knowledge articles."""
        with patch('Table_Tools.consolidated_tools.query_table_with_generic_filters') as mock_query:
            mock_query.return_value = {"result": [{"number": "KB001", "state": "published"}]}

            result = await get_active_knowledge_articles("test")

            mock_query.assert_called_once_with("kb_knowledge", {"state": "published"})
            assert result is not None


class TestPrivateTaskTools:
    """Test private task tool functions."""

    @pytest.mark.asyncio
    async def test_similar_private_tasks_for_text(self):
        """Test finding similar private tasks by text."""
        with patch('Table_Tools.consolidated_tools.query_table_by_text') as mock_query:
            mock_query.return_value = {"result": [{"number": "VTB001"}]}

            result = await similar_private_tasks_for_text("review")

            mock_query.assert_called_once_with("vtb_task", "review")
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_short_desc_for_private_task(self):
        """Test getting private task description."""
        with patch('Table_Tools.consolidated_tools.get_record_description') as mock_desc:
            mock_desc.return_value = {"result": [{"short_description": "Test"}]}

            result = await get_short_desc_for_private_task("VTB001")

            mock_desc.assert_called_once_with("vtb_task", "VTB001")
            assert result is not None

    @pytest.mark.asyncio
    async def test_similar_private_tasks_for_private_task(self):
        """Test finding similar private tasks."""
        with patch('Table_Tools.consolidated_tools.find_similar_records') as mock_similar:
            mock_similar.return_value = {"result": [{"number": "VTB002"}]}

            result = await similar_private_tasks_for_private_task("VTB001")

            mock_similar.assert_called_once_with("vtb_task", "VTB001")
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_private_task_details(self):
        """Test getting private task details."""
        with patch('Table_Tools.consolidated_tools.get_record_details') as mock_details:
            mock_details.return_value = {"result": [{"number": "VTB001"}]}

            result = await get_private_task_details("VTB001")

            mock_details.assert_called_once_with("vtb_task", "VTB001")
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_private_tasks_by_filter(self):
        """Test getting private tasks by filter."""
        with patch('Table_Tools.consolidated_tools.query_table_with_generic_filters') as mock_query:
            mock_query.return_value = {"result": [{"number": "VTB001"}]}

            result = await get_private_tasks_by_filter({"state": "1"})

            mock_query.assert_called_once_with("vtb_task", {"state": "1"})
            assert result is not None


class TestSLATools:
    """Test SLA tool functions."""

    @pytest.mark.asyncio
    async def test_similar_slas_for_text(self):
        """Test finding SLAs by text."""
        with patch('Table_Tools.consolidated_tools.query_table_by_text') as mock_query:
            mock_query.return_value = {"result": [{"number": "SLA001"}]}

            result = await similar_slas_for_text("incident")

            mock_query.assert_called_once_with("task_sla", "incident")
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_slas_for_task(self):
        """Test getting SLAs for specific task."""
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query, \
             patch('Table_Tools.consolidated_tools.TASK_NUMBER_FIELD', 'task_number'):
            mock_query.return_value = {"result": [{"number": "SLA001"}]}

            result = await get_slas_for_task("INC001")

            mock_query.assert_called_once()
            args = mock_query.call_args
            assert args[0][0] == "task_sla"

    @pytest.mark.asyncio
    async def test_get_sla_details(self):
        """Test getting SLA details."""
        with patch('Table_Tools.consolidated_tools.get_record_details') as mock_details:
            mock_details.return_value = {"result": [{"sys_id": "abc123"}]}

            result = await get_sla_details("abc123")

            mock_details.assert_called_once_with("task_sla", "abc123")
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_breaching_slas_default_threshold(self):
        """Test getting breaching SLAs with default threshold."""
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": [{"number": "SLA001"}]}

            result = await get_breaching_slas()

            mock_query.assert_called_once()
            args = mock_query.call_args
            params = args[0][1]
            assert params.filters["business_time_left"] == "<3600"  # 60 minutes * 60 seconds

    @pytest.mark.asyncio
    async def test_get_breaching_slas_custom_threshold(self):
        """Test getting breaching SLAs with custom threshold."""
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": [{"number": "SLA001"}]}

            result = await get_breaching_slas(time_threshold_minutes=30)

            mock_query.assert_called_once()
            args = mock_query.call_args
            params = args[0][1]
            assert params.filters["business_time_left"] == "<1800"  # 30 minutes * 60 seconds

    @pytest.mark.asyncio
    async def test_get_breached_slas_default(self):
        """Test getting breached SLAs with defaults."""
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": [{"number": "SLA001"}]}

            result = await get_breached_slas()

            mock_query.assert_called_once()
            args = mock_query.call_args
            params = args[0][1]
            assert params.filters["has_breached"] == "true"
            assert "sys_created_on" in params.filters

    @pytest.mark.asyncio
    async def test_get_breached_slas_with_filters(self):
        """Test getting breached SLAs with additional filters."""
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": [{"number": "SLA001"}]}

            result = await get_breached_slas(filters={"task.priority": "1"})

            mock_query.assert_called_once()
            args = mock_query.call_args
            params = args[0][1]
            assert params.filters["has_breached"] == "true"
            assert params.filters["task.priority"] == "1"

    @pytest.mark.asyncio
    async def test_get_slas_by_stage(self):
        """Test getting SLAs by stage."""
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": [{"number": "SLA001"}]}

            result = await get_slas_by_stage("In progress")

            mock_query.assert_called_once()
            args = mock_query.call_args
            params = args[0][1]
            assert params.filters["stage"] == "In progress"

    @pytest.mark.asyncio
    async def test_get_slas_by_stage_with_additional_filters(self):
        """Test getting SLAs by stage with additional filters."""
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": [{"number": "SLA001"}]}

            result = await get_slas_by_stage("In progress", additional_filters={"active": "true"})

            mock_query.assert_called_once()
            args = mock_query.call_args
            params = args[0][1]
            assert params.filters["stage"] == "In progress"
            assert params.filters["active"] == "true"

    @pytest.mark.asyncio
    async def test_get_active_slas(self):
        """Test getting active SLAs."""
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": [{"number": "SLA001"}]}

            result = await get_active_slas()

            mock_query.assert_called_once()
            args = mock_query.call_args
            params = args[0][1]
            assert params.filters["active"] == "true"

    @pytest.mark.asyncio
    async def test_get_active_slas_with_filters(self):
        """Test getting active SLAs with filters."""
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": [{"number": "SLA001"}]}

            result = await get_active_slas(filters={"stage": "In progress"})

            mock_query.assert_called_once()
            args = mock_query.call_args
            params = args[0][1]
            assert params.filters["active"] == "true"
            assert params.filters["stage"] == "In progress"

    @pytest.mark.asyncio
    async def test_get_sla_performance_summary(self):
        """Test getting SLA performance summary."""
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": [{"number": "SLA001"}]}

            result = await get_sla_performance_summary()

            mock_query.assert_called_once()
            args = mock_query.call_args
            params = args[0][1]
            assert "sys_created_on" in params.filters
            assert params.fields is not None

    @pytest.mark.asyncio
    async def test_get_sla_performance_summary_with_filters(self):
        """Test getting SLA performance summary with filters."""
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": [{"number": "SLA001"}]}

            result = await get_sla_performance_summary(filters={"active": "true"})

            mock_query.assert_called_once()
            args = mock_query.call_args
            params = args[0][1]
            assert params.filters["active"] == "true"

    @pytest.mark.asyncio
    async def test_get_recent_breached_slas_default(self):
        """Test getting recent breached SLAs with default days."""
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": [{"number": "SLA001"}]}

            result = await get_recent_breached_slas()

            mock_query.assert_called_once()
            args = mock_query.call_args
            params = args[0][1]
            assert params.filters["has_breached"] == "true"
            assert "daysAgo(1)" in params.filters["sys_created_on"]

    @pytest.mark.asyncio
    async def test_get_recent_breached_slas_custom_days(self):
        """Test getting recent breached SLAs with custom days."""
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": [{"number": "SLA001"}]}

            result = await get_recent_breached_slas(days=7)

            mock_query.assert_called_once()
            args = mock_query.call_args
            params = args[0][1]
            assert "daysAgo(7)" in params.filters["sys_created_on"]

    @pytest.mark.asyncio
    async def test_get_critical_sla_status(self):
        """Test getting critical SLA status."""
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": [{"number": "SLA001"}]}

            result = await get_critical_sla_status()

            mock_query.assert_called_once()
            args = mock_query.call_args
            params = args[0][1]
            assert params.filters["active"] == "true"
            assert "task.priority" in params.filters
            assert params.filters["business_percentage"] == ">80"
            assert params.fields is not None
