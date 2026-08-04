"""ci_type validation across the CMDB tools (v4.4 Tier 0.6).

The bug: `search_cis_by_attributes` silently downgraded an unrecognised
`ci_type` to the base `cmdb_ci` table, and `get_ci_details` silently ignored it
and probed every table. Both returned HTTP 200 with rows from a table the
caller never asked for and nothing in the response saying so — a wrong answer
that looks exactly like a right one.

Unlike tests/test_cmdb_tools.py, these patch the real request layer
(`Table_Tools.cmdb_tools.make_nws_request`) and assert on the URL that would
actually be sent, so they fail if the downgrade returns.
"""
from unittest.mock import patch

import pytest

from Table_Tools.cmdb_tools import (
    _ci_type_error,
    find_cis_by_type,
    get_all_ci_types,
    get_ci_details,
    search_cis_by_attributes,
)


def _table_of(url):
    """Table segment of a ServiceNow Table API URL."""
    return url.split("/api/now/table/")[1].split("?")[0]


class _Capture:
    """Records every URL passed to make_nws_request and returns a canned payload.

    `per_table` lets a test answer differently per table, which is what makes
    the concurrent multi-table probe in get_ci_details testable — a single
    canned payload cannot express "empty, empty, hit".
    """

    def __init__(self, payload=None, per_table=None):
        self.urls = []
        self.payload = payload if payload is not None else {"result": []}
        self.per_table = per_table or {}

    async def __call__(self, url, *args, **kwargs):
        self.urls.append(url)
        if self.per_table:
            return self.per_table.get(_table_of(url), {"result": []})
        return self.payload

    @property
    def tables(self):
        """Table segment of each captured URL."""
        return [_table_of(url) for url in self.urls]


class TestCiTypePolicy:
    @pytest.mark.parametrize("ci_type", [
        "cmdb_ci",
        "cmdb_ci_server",
        "cmdb_ci_network_gear",
        "cmdb_ci_vcenter_vm_group",
        "cmdb_ci_appl",
        "cmdb_ci_db2_catalog",
    ])
    def test_well_formed_types_accepted(self, ci_type):
        assert _ci_type_error(ci_type) is None

    @pytest.mark.parametrize("ci_type", [
        "incident",
        "sys_user",
        "CMDB_CI_SERVER",          # wrong case — real table names are lowercase
        "cmdb",
        "cmdb_c",
        "cmdb_ci-server",          # hyphen is not a table-name character
        "cmdb_ci_server ",         # trailing space
        " cmdb_ci_server",
        "cmdb_ci_server?sysparm_limit=9999",   # query-param smuggling
        "cmdb_ci_server/../sys_user",          # path traversal
        "cmdb_ci_server&sysparm_fields=x",
        "cmdb_ci_server\n",                    # `$` matches before a trailing \n
        "cmdb_ci_server\nX",
        "",
    ])
    def test_unusable_types_rejected(self, ci_type):
        error = _ci_type_error(ci_type)
        assert error is not None
        assert "Invalid CI type" in error

    def test_startswith_alone_would_not_have_caught_the_injection(self):
        """The old bare prefix check accepted this; the shape check does not."""
        smuggled = "cmdb_ci_server?sysparm_limit=9999"
        assert smuggled.startswith("cmdb_ci")
        assert _ci_type_error(smuggled) is not None

    def test_trailing_newline_rejected_where_dollar_anchor_would_allow_it(self):
        """re.match with `$` accepts one trailing newline; fullmatch does not."""
        import re

        from Table_Tools.cmdb_tools import _CI_TYPE_PATTERN

        assert re.match(r'^cmdb_ci[a-z0-9_]*$', "cmdb_ci_server\n") is not None
        assert _CI_TYPE_PATTERN.fullmatch("cmdb_ci_server\n") is None
        assert _ci_type_error("cmdb_ci_server\n") is not None


class TestSearchCisByAttributes:
    @pytest.mark.asyncio
    async def test_unknown_ci_type_errors_instead_of_downgrading(self):
        """The headline bug: never query cmdb_ci when the caller named another table."""
        capture = _Capture()
        with patch("Table_Tools.cmdb_tools.make_nws_request", new=capture):
            result = await search_cis_by_attributes(name="prod", ci_type="not_a_cmdb_table")

        assert isinstance(result, str)
        assert "Invalid CI type" in result
        assert capture.urls == [], "a rejected ci_type must not reach ServiceNow at all"

    @pytest.mark.asyncio
    async def test_valid_ci_type_is_the_table_queried(self):
        capture = _Capture()
        with patch("Table_Tools.cmdb_tools.make_nws_request", new=capture):
            await search_cis_by_attributes(name="prod", ci_type="cmdb_ci_esx_server")

        assert capture.tables == ["cmdb_ci_esx_server"]

    @pytest.mark.asyncio
    async def test_omitted_ci_type_still_defaults_to_base_table(self):
        """Absent is not invalid — no ci_type means "search all CIs"."""
        capture = _Capture()
        with patch("Table_Tools.cmdb_tools.make_nws_request", new=capture):
            await search_cis_by_attributes(name="prod")

        assert capture.tables == ["cmdb_ci"]

    @pytest.mark.asyncio
    async def test_no_attributes_still_rejected_before_validation(self):
        capture = _Capture()
        with patch("Table_Tools.cmdb_tools.make_nws_request", new=capture):
            result = await search_cis_by_attributes(ci_type="cmdb_ci_server")

        assert "At least one search attribute" in result
        assert capture.urls == []


class TestFindCisByType:
    @pytest.mark.asyncio
    async def test_missing_ci_type_reports_required(self):
        capture = _Capture()
        with patch("Table_Tools.cmdb_tools.make_nws_request", new=capture):
            result = await find_cis_by_type("")

        assert result == "CI type is required"
        assert capture.urls == []

    @pytest.mark.asyncio
    async def test_injection_attempt_rejected(self):
        capture = _Capture()
        with patch("Table_Tools.cmdb_tools.make_nws_request", new=capture):
            result = await find_cis_by_type("cmdb_ci_server?sysparm_limit=9999")

        assert "Invalid CI type" in result
        assert capture.urls == []

    @pytest.mark.asyncio
    async def test_valid_type_queries_that_table(self):
        capture = _Capture(payload={"result": [{"number": "SRV0001", "name": "prod-1"}]})
        with patch("Table_Tools.cmdb_tools.make_nws_request", new=capture):
            result = await find_cis_by_type("cmdb_ci_server")

        assert capture.tables == ["cmdb_ci_server"]
        assert result["ci_type"] == "cmdb_ci_server"
        assert result["count"] == 1


class TestGetCiDetails:
    @pytest.mark.asyncio
    async def test_unknown_ci_type_errors_instead_of_probing_everything(self):
        capture = _Capture()
        with patch("Table_Tools.cmdb_tools.make_nws_request", new=capture):
            result = await get_ci_details("SRV0001", ci_type="not_a_cmdb_table")

        assert "Invalid CI type" in result
        assert capture.urls == [], "a rejected ci_type must not fan out across tables"

    @pytest.mark.asyncio
    async def test_valid_ci_type_probes_only_that_table(self):
        """Previously any type outside the static list was ignored and all 7 probed."""
        capture = _Capture()
        with patch("Table_Tools.cmdb_tools.make_nws_request", new=capture):
            await get_ci_details("SRV0001", ci_type="cmdb_ci_esx_server")

        assert capture.tables == ["cmdb_ci_esx_server"]

    @pytest.mark.asyncio
    async def test_omitted_ci_type_probes_the_default_set(self):
        capture = _Capture()
        with patch("Table_Tools.cmdb_tools.make_nws_request", new=capture):
            await get_ci_details("SRV0001")

        assert capture.tables == [
            "cmdb_ci_server", "cmdb_ci_computer", "cmdb_ci_database",
            "cmdb_ci_hardware", "cmdb_ci_network_gear", "cmdb_ci_service", "cmdb_ci",
        ]

    @pytest.mark.asyncio
    async def test_missing_ci_number_reports_required(self):
        capture = _Capture()
        with patch("Table_Tools.cmdb_tools.make_nws_request", new=capture):
            result = await get_ci_details("")

        assert result == "CI number is required"
        assert capture.urls == []

    @pytest.mark.asyncio
    async def test_hit_on_a_later_table_reports_that_table(self):
        """The concurrent probe must pair each row with the table it came from.

        The probes run under asyncio.gather with a semaphore, so completion
        order is not dispatch order. `zip(tables_to_search, rows)` is what keeps
        the reported ci_table correct; without a per-table payload this path had
        no coverage at all and an order-insensitive refactor would misreport it.
        """
        capture = _Capture(per_table={
            "cmdb_ci_database": {"result": [{"number": "DB0001", "name": "prod-db"}]},
        })
        with patch("Table_Tools.cmdb_tools.make_nws_request", new=capture):
            result = await get_ci_details("DB0001")

        assert result["ci_table"] == "cmdb_ci_database"
        assert result["ci_number"] == "DB0001"
        assert result["result"]["name"] == "prod-db"

    @pytest.mark.asyncio
    async def test_most_specific_table_wins_when_several_match(self):
        """Probe order is a priority order: the earliest matching table wins."""
        capture = _Capture(per_table={
            "cmdb_ci_server": {"result": [{"number": "SRV0001", "name": "from-server"}]},
            "cmdb_ci_database": {"result": [{"number": "SRV0001", "name": "from-database"}]},
            "cmdb_ci": {"result": [{"number": "SRV0001", "name": "from-base"}]},
        })
        with patch("Table_Tools.cmdb_tools.make_nws_request", new=capture):
            result = await get_ci_details("SRV0001")

        assert result["ci_table"] == "cmdb_ci_server"
        assert result["result"]["name"] == "from-server"

    @pytest.mark.asyncio
    async def test_no_table_matching_reports_not_found(self):
        capture = _Capture()
        with patch("Table_Tools.cmdb_tools.make_nws_request", new=capture):
            result = await get_ci_details("NOPE0001")

        assert "NOPE0001" in result
        assert "not found" in result.lower()


class TestGetAllCiTypesLabelling:
    @pytest.mark.asyncio
    async def test_number_ref_is_not_reported_as_a_record_count(self):
        """number_ref is a numbering-config reference; calling it record_count lied."""
        payload = {"result": [
            {"name": "cmdb_ci_server", "label": "Server", "number_ref": "abc123"},
        ]}
        with patch("Table_Tools.cmdb_tools.make_nws_request", new=_Capture(payload=payload)):
            result = await get_all_ci_types()

        entry = result["ci_types"][0]
        assert "record_count" not in entry
        assert entry["number_prefix_ref"] == "abc123"
        assert entry["table_name"] == "cmdb_ci_server"
