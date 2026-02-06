"""
Tests for consolidated_tools.py — priority incidents, knowledge-specific, and SLA tools.
Wrapper tests removed in v3.0 (now covered by test_generic_tool_wrappers.py).
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from typing import Dict, Any

from Table_Tools.consolidated_tools import (
    _get_error_message,
    _build_priority_result_message,
    # Priority incidents
    get_priority_incidents,
    get_priority_incidents_current_month,
    get_priority_incidents_last_n_days,
    get_priority_incidents_this_week,
    get_priority_incidents_yesterday,
    get_priority_incidents_today,
    # Knowledge tools
    similar_knowledge_for_text,
    get_knowledge_by_category,
    get_active_knowledge_articles,
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
        with patch('Table_Tools.consolidated_tools.TABLE_ERROR_MESSAGES', {"incident": "Incident not found"}):
            result = _get_error_message("incident")
            assert result == "Incident not found"

    def test_get_error_message_default(self):
        with patch('Table_Tools.consolidated_tools.TABLE_ERROR_MESSAGES', {}):
            result = _get_error_message("unknown_table")
            assert result == "Record not found."

    def test_get_error_message_custom_default(self):
        with patch('Table_Tools.consolidated_tools.TABLE_ERROR_MESSAGES', {}):
            result = _get_error_message("unknown_table", "Custom error")
            assert result == "Custom error"


class TestGetPriorityIncidents:
    """Test get_priority_incidents function."""

    @pytest.mark.asyncio
    async def test_basic(self):
        with patch('Table_Tools.consolidated_tools.get_records_by_priority') as mock_priority:
            mock_priority.return_value = {"result": [{"number": "INC001", "priority": "1"}]}
            result = await get_priority_incidents(["1", "2"])
            mock_priority.assert_called_once_with("incident", ["1", "2"], None, detailed=True)
            assert "result" in result

    @pytest.mark.asyncio
    async def test_deprecated_kwargs(self):
        with patch('Table_Tools.consolidated_tools.get_records_by_priority') as mock_priority, \
             patch('Table_Tools.consolidated_tools.logger') as mock_logger:
            mock_priority.return_value = {"result": [{"number": "INC001"}]}
            result = await get_priority_incidents(["1", "2"], state="New")
            mock_logger.warning.assert_called()
            filters = mock_priority.call_args[0][2]
            assert filters.get("state") == "New"


class TestGetPriorityIncidentsEnhanced:
    """Test enhanced get_priority_incidents with date filtering."""

    @pytest.mark.asyncio
    async def test_with_date_range(self):
        with patch('Table_Tools.consolidated_tools.get_records_by_priority') as mock_priority:
            mock_priority.return_value = {"result": [{"number": "INC001"}]}
            await get_priority_incidents(["1", "2"], start_date="2026-01-01", end_date="2026-01-28")
            filters = mock_priority.call_args[0][2]
            assert "_date_range" in filters

    @pytest.mark.asyncio
    async def test_with_start_date_only(self):
        with patch('Table_Tools.consolidated_tools.get_records_by_priority') as mock_priority:
            mock_priority.return_value = {"result": [{"number": "INC001"}]}
            await get_priority_incidents(["1"], start_date="2026-01-01")
            filters = mock_priority.call_args[0][2]
            assert "sys_created_on>=2026-01-01 00:00:00" in filters["_date_range"]

    @pytest.mark.asyncio
    async def test_with_end_date_only(self):
        with patch('Table_Tools.consolidated_tools.get_records_by_priority') as mock_priority:
            mock_priority.return_value = {"result": [{"number": "INC001"}]}
            await get_priority_incidents(["1"], end_date="2026-01-28")
            filters = mock_priority.call_args[0][2]
            assert "sys_created_on<=2026-01-28 23:59:59" in filters["_date_range"]

    @pytest.mark.asyncio
    async def test_invalid_start_date(self):
        result = await get_priority_incidents(["1"], start_date="01-28-2026")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_invalid_end_date(self):
        result = await get_priority_incidents(["1"], end_date="2026/01/28")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_with_metadata(self):
        with patch('Table_Tools.consolidated_tools.get_records_by_priority') as mock_priority:
            mock_priority.return_value = {"result": [{"number": "INC001"}, {"number": "INC002"}]}
            result = await get_priority_incidents(
                ["1", "2"], start_date="2026-01-01", end_date="2026-01-28", include_metadata=True
            )
            assert "metadata" in result
            assert result["metadata"]["count"] == 2

    @pytest.mark.asyncio
    async def test_with_additional_filters(self):
        with patch('Table_Tools.consolidated_tools.get_records_by_priority') as mock_priority:
            mock_priority.return_value = {"result": []}
            await get_priority_incidents(["1"], additional_filters={"state": "New"})
            filters = mock_priority.call_args[0][2]
            assert filters.get("state") == "New"

    @pytest.mark.asyncio
    async def test_metadata_without_date_range(self):
        with patch('Table_Tools.consolidated_tools.get_records_by_priority') as mock_priority:
            mock_priority.return_value = {"result": [{"number": "INC001"}]}
            result = await get_priority_incidents(["1"], include_metadata=True)
            assert result["metadata"]["date_range"] is None


class TestBuildPriorityResultMessage:
    """Test the result message builder."""

    def test_with_both_dates(self):
        msg = _build_priority_result_message(5, ["1", "2"], "2026-01-01", "2026-01-28")
        assert "from 2026-01-01 to 2026-01-28" in msg

    def test_with_start_date_only(self):
        msg = _build_priority_result_message(3, ["1"], "2026-01-01", None)
        assert "from 2026-01-01 onwards" in msg

    def test_with_end_date_only(self):
        msg = _build_priority_result_message(10, ["1", "2", "3"], None, "2026-01-28")
        assert "up to 2026-01-28" in msg

    def test_without_dates(self):
        msg = _build_priority_result_message(0, ["1"], None, None)
        assert "from" not in msg


class TestPriorityIncidentsHelpers:
    """Test convenience helper functions."""

    @pytest.mark.asyncio
    async def test_current_month(self):
        with patch('Table_Tools.consolidated_tools.get_priority_incidents') as mock_func, \
             patch('Table_Tools.consolidated_tools.get_current_month_range') as mock_range:
            mock_range.return_value = ("2026-01-01", "2026-01-31")
            mock_func.return_value = {"result": []}
            await get_priority_incidents_current_month(["1", "2"])
            assert mock_func.call_args[1]["start_date"] == "2026-01-01"

    @pytest.mark.asyncio
    async def test_last_n_days(self):
        with patch('Table_Tools.consolidated_tools.get_priority_incidents') as mock_func, \
             patch('Table_Tools.consolidated_tools.get_last_n_days_range') as mock_range:
            mock_range.return_value = ("2026-01-21", "2026-01-28")
            mock_func.return_value = {"result": []}
            await get_priority_incidents_last_n_days(["1"], days=14)
            mock_range.assert_called_once_with(14)

    @pytest.mark.asyncio
    async def test_this_week(self):
        with patch('Table_Tools.consolidated_tools.get_priority_incidents') as mock_func, \
             patch('Table_Tools.consolidated_tools.get_this_week_range') as mock_range:
            mock_range.return_value = ("2026-01-26", "2026-02-01")
            mock_func.return_value = {"result": []}
            await get_priority_incidents_this_week(["1", "2"])
            assert mock_func.call_args[1]["start_date"] == "2026-01-26"

    @pytest.mark.asyncio
    async def test_today(self):
        with patch('Table_Tools.consolidated_tools.get_priority_incidents') as mock_func, \
             patch('Table_Tools.consolidated_tools.get_today_range') as mock_range:
            mock_range.return_value = ("2026-01-28", "2026-01-28")
            mock_func.return_value = {"result": []}
            await get_priority_incidents_today(["1"])
            assert mock_func.call_args[1]["start_date"] == "2026-01-28"

    @pytest.mark.asyncio
    async def test_yesterday(self):
        with patch('Table_Tools.consolidated_tools.get_priority_incidents') as mock_func, \
             patch('Table_Tools.consolidated_tools.get_yesterday_range') as mock_range:
            mock_range.return_value = ("2026-01-27", "2026-01-27")
            mock_func.return_value = {"result": []}
            await get_priority_incidents_yesterday(["1", "2"])
            assert mock_func.call_args[1]["start_date"] == "2026-01-27"


class TestKnowledgeTools:
    """Test knowledge tool functions."""

    @pytest.mark.asyncio
    async def test_similar_knowledge_for_text_simple(self):
        with patch('Table_Tools.consolidated_tools.query_table_by_text') as mock_query:
            mock_query.return_value = {"result": [{"number": "KB001"}]}
            result = await similar_knowledge_for_text("password reset")
            mock_query.assert_called_once_with("kb_knowledge", "password reset")

    @pytest.mark.asyncio
    async def test_similar_knowledge_with_category(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_generic_filters') as mock_query:
            mock_query.return_value = {"result": []}
            await similar_knowledge_for_text("test", category="IT")
            assert "kb_category" in mock_query.call_args[0][1]

    @pytest.mark.asyncio
    async def test_similar_knowledge_with_kb_base(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_generic_filters') as mock_query:
            mock_query.return_value = {"result": []}
            await similar_knowledge_for_text("test", kb_base="IT_KB")
            assert "kb_knowledge_base" in mock_query.call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_knowledge_by_category(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_generic_filters') as mock_query:
            mock_query.return_value = {"result": []}
            await get_knowledge_by_category("IT")
            mock_query.assert_called_once_with("kb_knowledge", {"kb_category": "IT"})

    @pytest.mark.asyncio
    async def test_get_knowledge_by_category_with_kb_base(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_generic_filters') as mock_query:
            mock_query.return_value = {"result": []}
            await get_knowledge_by_category("IT", kb_base="IT_KB")
            filters = mock_query.call_args[0][1]
            assert filters["kb_category"] == "IT"
            assert filters["kb_knowledge_base"] == "IT_KB"

    @pytest.mark.asyncio
    async def test_get_active_knowledge_articles(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_generic_filters') as mock_query:
            mock_query.return_value = {"result": [{"number": "KB001"}]}
            result = await get_active_knowledge_articles("test")
            mock_query.assert_called_once_with("kb_knowledge", {"state": "published"})


class TestSLATools:
    """Test SLA tool functions."""

    @pytest.mark.asyncio
    async def test_similar_slas_for_text(self):
        with patch('Table_Tools.consolidated_tools.query_table_by_text') as mock_query:
            mock_query.return_value = {"result": []}
            await similar_slas_for_text("incident")
            mock_query.assert_called_once_with("task_sla", "incident")

    @pytest.mark.asyncio
    async def test_get_slas_for_task(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query, \
             patch('Table_Tools.consolidated_tools.TASK_NUMBER_FIELD', 'task_number'):
            mock_query.return_value = {"result": []}
            await get_slas_for_task("INC001")
            assert mock_query.call_args[0][0] == "task_sla"

    @pytest.mark.asyncio
    async def test_get_sla_details(self):
        with patch('Table_Tools.consolidated_tools.get_record_details') as mock:
            mock.return_value = {"result": []}
            await get_sla_details("abc123")
            mock.assert_called_once_with("task_sla", "abc123")

    @pytest.mark.asyncio
    async def test_get_breaching_slas_default(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": []}
            await get_breaching_slas()
            params = mock_query.call_args[0][1]
            assert params.filters["business_time_left"] == "<3600"

    @pytest.mark.asyncio
    async def test_get_breaching_slas_custom(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": []}
            await get_breaching_slas(time_threshold_minutes=30)
            params = mock_query.call_args[0][1]
            assert params.filters["business_time_left"] == "<1800"

    @pytest.mark.asyncio
    async def test_get_breached_slas(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": []}
            await get_breached_slas()
            params = mock_query.call_args[0][1]
            assert params.filters["has_breached"] == "true"

    @pytest.mark.asyncio
    async def test_get_breached_slas_with_filters(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": []}
            await get_breached_slas(filters={"task.priority": "1"})
            params = mock_query.call_args[0][1]
            assert params.filters["task.priority"] == "1"

    @pytest.mark.asyncio
    async def test_get_slas_by_stage(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": []}
            await get_slas_by_stage("In progress")
            params = mock_query.call_args[0][1]
            assert params.filters["stage"] == "In progress"

    @pytest.mark.asyncio
    async def test_get_slas_by_stage_with_filters(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": []}
            await get_slas_by_stage("In progress", additional_filters={"active": "true"})
            params = mock_query.call_args[0][1]
            assert params.filters["active"] == "true"

    @pytest.mark.asyncio
    async def test_get_active_slas(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": []}
            await get_active_slas()
            params = mock_query.call_args[0][1]
            assert params.filters["active"] == "true"

    @pytest.mark.asyncio
    async def test_get_active_slas_with_filters(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": []}
            await get_active_slas(filters={"stage": "In progress"})
            params = mock_query.call_args[0][1]
            assert params.filters["stage"] == "In progress"

    @pytest.mark.asyncio
    async def test_get_sla_performance_summary(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": []}
            await get_sla_performance_summary()
            params = mock_query.call_args[0][1]
            assert "sys_created_on" in params.filters
            assert params.fields is not None

    @pytest.mark.asyncio
    async def test_get_sla_performance_with_filters(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": []}
            await get_sla_performance_summary(filters={"active": "true"})
            params = mock_query.call_args[0][1]
            assert params.filters["active"] == "true"

    @pytest.mark.asyncio
    async def test_get_recent_breached_slas(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": []}
            await get_recent_breached_slas()
            params = mock_query.call_args[0][1]
            assert params.filters["has_breached"] == "true"
            assert "sys_created_on>=" in params.filters["sys_created_on"]

    @pytest.mark.asyncio
    async def test_get_recent_breached_slas_custom_days(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": []}
            await get_recent_breached_slas(days=7)
            params = mock_query.call_args[0][1]
            assert "sys_created_on>=" in params.filters["sys_created_on"]

    @pytest.mark.asyncio
    async def test_get_critical_sla_status(self):
        with patch('Table_Tools.consolidated_tools.query_table_with_filters') as mock_query:
            mock_query.return_value = {"result": []}
            await get_critical_sla_status()
            params = mock_query.call_args[0][1]
            assert params.filters["active"] == "true"
            assert params.filters["task.priority"] == "IN1,2"
            assert params.filters["business_percentage"] == ">80"
            assert params.fields is not None
