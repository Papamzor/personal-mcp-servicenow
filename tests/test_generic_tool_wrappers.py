"""
Tests for generic_tool_wrappers.py — the 5 generic MCP tools.
"""

import pytest
from unittest.mock import patch, AsyncMock

from Table_Tools.generic_tool_wrappers import (
    _validate_table,
    search_records,
    get_record_summary,
    get_record,
    find_similar,
    filter_records,
    SUPPORTED_TABLES,
)


class TestValidateTable:
    """Test table validation helper."""

    def test_valid_table(self):
        assert _validate_table("incident") is None
        assert _validate_table("change_request") is None
        assert _validate_table("vtb_task") is None

    def test_invalid_table(self):
        result = _validate_table("nonexistent_table")
        assert result is not None
        assert "error" in result
        assert "nonexistent_table" in result["error"]
        assert "incident" in result["error"]  # lists supported tables

    def test_supported_tables_list(self):
        assert "incident" in SUPPORTED_TABLES
        assert "kb_knowledge" in SUPPORTED_TABLES
        assert "vtb_task" in SUPPORTED_TABLES


class TestSearchRecords:
    """Test search_records generic tool."""

    @pytest.mark.asyncio
    async def test_valid_table(self):
        with patch("Table_Tools.generic_tool_wrappers.query_table_by_text") as mock:
            mock.return_value = {"result": [{"number": "INC001"}]}
            result = await search_records("incident", "server down")
            mock.assert_called_once_with("incident", "server down")
            assert result["result"][0]["number"] == "INC001"

    @pytest.mark.asyncio
    async def test_invalid_table(self):
        result = await search_records("bad_table", "test")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_different_tables(self):
        with patch("Table_Tools.generic_tool_wrappers.query_table_by_text") as mock:
            mock.return_value = {"result": []}
            await search_records("change_request", "upgrade")
            mock.assert_called_once_with("change_request", "upgrade")


class TestGetRecordSummary:
    """Test get_record_summary generic tool."""

    @pytest.mark.asyncio
    async def test_valid_table(self):
        with patch("Table_Tools.generic_tool_wrappers.get_record_description") as mock:
            mock.return_value = {"result": [{"short_description": "Test"}]}
            result = await get_record_summary("incident", "INC001")
            mock.assert_called_once_with("incident", "INC001")
            assert result["result"][0]["short_description"] == "Test"

    @pytest.mark.asyncio
    async def test_invalid_table(self):
        result = await get_record_summary("bad_table", "INC001")
        assert "error" in result


class TestGetRecord:
    """Test get_record generic tool."""

    @pytest.mark.asyncio
    async def test_valid_table(self):
        with patch("Table_Tools.generic_tool_wrappers.get_record_details") as mock:
            mock.return_value = {"result": [{"number": "CHG001", "priority": "2"}]}
            result = await get_record("change_request", "CHG001")
            mock.assert_called_once_with("change_request", "CHG001")
            assert result["result"][0]["number"] == "CHG001"

    @pytest.mark.asyncio
    async def test_invalid_table(self):
        result = await get_record("bad_table", "CHG001")
        assert "error" in result


class TestFindSimilar:
    """Test find_similar generic tool."""

    @pytest.mark.asyncio
    async def test_valid_table(self):
        with patch("Table_Tools.generic_tool_wrappers.find_similar_records") as mock:
            mock.return_value = {"result": [{"number": "INC002"}], "message": "Found 1"}
            result = await find_similar("incident", "INC001")
            mock.assert_called_once_with("incident", "INC001")
            assert len(result["result"]) == 1

    @pytest.mark.asyncio
    async def test_invalid_table(self):
        result = await find_similar("bad_table", "INC001")
        assert "error" in result


class TestFilterRecords:
    """Test filter_records generic tool."""

    @pytest.mark.asyncio
    async def test_valid_table(self):
        with patch("Table_Tools.generic_tool_wrappers.query_table_with_filters") as mock:
            mock.return_value = {"result": [{"number": "INC001"}]}
            result = await filter_records("incident", {"priority": "1", "state": "New"})
            mock.assert_called_once()
            args = mock.call_args
            assert args[0][0] == "incident"
            assert args[0][1].filters == {"priority": "1", "state": "New"}

    @pytest.mark.asyncio
    async def test_invalid_table(self):
        result = await filter_records("bad_table", {"priority": "1"})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_with_custom_fields(self):
        with patch("Table_Tools.generic_tool_wrappers.query_table_with_filters") as mock:
            mock.return_value = {"result": []}
            result = await filter_records(
                "incident",
                {"priority": "1"},
                fields=["number", "short_description"]
            )
            args = mock.call_args
            assert args[0][1].fields == ["number", "short_description"]

    @pytest.mark.asyncio
    async def test_vtb_task_table(self):
        """Verify vtb_task works through generic filter (ServiceNow API path)."""
        with patch("Table_Tools.generic_tool_wrappers.query_table_with_filters") as mock:
            mock.return_value = {"result": [{"number": "VTB001"}]}
            result = await filter_records("vtb_task", {"state": "1"})
            assert args[0][0] == "vtb_task" if (args := mock.call_args) else False
