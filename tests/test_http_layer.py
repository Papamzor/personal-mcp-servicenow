"""http_layer regression tests for v4.0 Sprint 3 split.

These tests lock the four read-path invariants and the critical
read/write divergence in ``make_nws_request``. Every read MUST inject
the three sysparm performance params and flatten display-value
envelopes; every write MUST NOT touch either of those — applying them
to a write payload would mangle the request and the response.

Failure of any test here means a token-optimization regression. Do not
relax the assertions without recording a baseline diff.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from http_layer.request_dispatcher import make_nws_request
from http_layer.response_parser import (
    extract_display_values,
    extract_field_value,
    process_item_dict,
)
from http_layer.url_builder import add_default_params, ensure_query_encoded


# ---------------------------------------------------------------------------
# Unit-level invariants
# ---------------------------------------------------------------------------

class TestUrlBuilder:
    """Token-optimization invariants the GET path depends on."""

    def test_add_default_params_injects_all_three(self):
        url = add_default_params("https://x/api/now/table/incident?sysparm_query=foo")
        assert "sysparm_display_value=true" in url
        assert "sysparm_exclude_reference_link=true" in url
        assert "sysparm_no_count=true" in url

    def test_add_default_params_is_idempotent(self):
        url = "https://x/api/now/table/incident?sysparm_display_value=true&sysparm_exclude_reference_link=true&sysparm_no_count=true"
        result = add_default_params(url)
        assert result.count("sysparm_display_value=true") == 1
        assert result.count("sysparm_exclude_reference_link=true") == 1
        assert result.count("sysparm_no_count=true") == 1

    def test_add_default_params_can_skip_display_value(self):
        url = add_default_params("https://x/api?foo=bar", display_value=False)
        assert "sysparm_display_value" not in url

    def test_ensure_query_encoded_preserves_servicenow_operators(self):
        url = "https://x/api?sysparm_query=priority=1^ORpriority=2"
        encoded = ensure_query_encoded(url)
        assert "priority=1^ORpriority=2" in encoded  # operators preserved

    def test_ensure_query_encoded_is_idempotent(self):
        url = "https://x/api?sysparm_query=short_description=server%20down"
        once = ensure_query_encoded(url)
        twice = ensure_query_encoded(once)
        assert once == twice


class TestResponseParser:
    """Display-value flattening — the other half of the token-saving story."""

    def test_extract_field_value_flattens_envelope(self):
        assert extract_field_value({"display_value": "Bob", "value": "user_sys_id"}) == "Bob"

    def test_extract_field_value_passes_scalars_through(self):
        assert extract_field_value("plain") == "plain"
        assert extract_field_value(42) == 42

    def test_process_item_dict_flattens_every_field(self):
        row = {
            "number": {"display_value": "INC0001", "value": "INC0001"},
            "priority": {"display_value": "1 - Critical", "value": "1"},
            "active": "true",
        }
        assert process_item_dict(row) == {
            "number": "INC0001",
            "priority": "1 - Critical",
            "active": "true",
        }

    def test_extract_display_values_walks_result_list(self):
        payload = {
            "result": [
                {"number": {"display_value": "INC0001", "value": "INC0001"}},
                {"number": {"display_value": "INC0002", "value": "INC0002"}},
            ]
        }
        assert extract_display_values(payload) == {
            "result": [{"number": "INC0001"}, {"number": "INC0002"}]
        }


# ---------------------------------------------------------------------------
# Dispatcher — read/write divergence
# ---------------------------------------------------------------------------

class TestMakeNwsRequestReadPath:
    """GET path: encoding + perf params + display flattening all apply."""

    @pytest.mark.asyncio
    async def test_get_path_applies_perf_params_and_flattens(self):
        captured_urls = []

        async def fake_oauth(url):
            captured_urls.append(url)
            return {"result": [{"number": {"display_value": "INC0001", "value": "INC0001"}}]}

        with patch("service_now_api_oauth.make_oauth_request", new=fake_oauth):
            result = await make_nws_request(
                "https://x/api/now/table/incident?sysparm_query=active=true"
            )

        # Perf params injected on the outgoing URL
        sent = captured_urls[0]
        assert "sysparm_exclude_reference_link=true" in sent
        assert "sysparm_no_count=true" in sent
        assert "sysparm_display_value=true" in sent

        # Display values flattened on the response
        assert result == {"result": [{"number": "INC0001"}]}


class TestMakeNwsRequestWritePath:
    """Critical negative tests — write path MUST NOT touch read-path mutations.

    Per the token-optimization invariant memory: applying
    ``sysparm_*=true`` params to a POST/PATCH body would mangle the
    write request; running ``extract_display_values`` on a write response
    (single-record shape) would corrupt its structure. Sprint 3 must
    preserve this split.
    """

    @pytest.mark.asyncio
    async def test_post_does_not_inject_perf_params(self):
        captured_urls = []

        mock_client = MagicMock()

        async def fake_authenticated(method, url, raise_for_status=False, **kwargs):
            captured_urls.append(url)
            return {"result": {"number": "VTB0001234"}}

        mock_client.make_authenticated_request = fake_authenticated

        original_url = "https://x/api/now/table/vtb_task"
        with patch("service_now_api_oauth.get_oauth_client", return_value=mock_client):
            await make_nws_request(
                original_url,
                method="POST",
                json_data={"short_description": "Test"},
            )

        sent = captured_urls[0]
        assert "sysparm_exclude_reference_link" not in sent
        assert "sysparm_no_count" not in sent
        assert "sysparm_display_value" not in sent
        # URL passed through unchanged
        assert sent == original_url

    @pytest.mark.asyncio
    async def test_patch_does_not_flatten_response(self):
        """Write responses have a single-record shape; flattening would corrupt them.

        After Sprint 3, the dispatcher routes write returns through the
        oauth client without passing the result through
        ``extract_display_values``. Verify the returned dict is exactly
        what the client returned.
        """
        write_response = {
            "result": {
                # Single record, NOT a list. extract_display_values would
                # silently no-op on this shape today but the dispatcher
                # must still skip the call.
                "number": {"display_value": "VTB0001234", "value": "vtb_sys_id"},
                "state": {"display_value": "1 - Open", "value": "1"},
            }
        }

        mock_client = MagicMock()
        mock_client.make_authenticated_request = AsyncMock(return_value=write_response)

        with patch("service_now_api_oauth.get_oauth_client", return_value=mock_client):
            result = await make_nws_request(
                "https://x/api/now/table/vtb_task/sys123",
                method="PATCH",
                json_data={"state": "2"},
            )

        # If display-value flattening had run, "number" would be a scalar
        # string. The dispatcher MUST return the raw envelope unchanged.
        assert result == write_response
        assert isinstance(result["result"]["number"], dict)

    @pytest.mark.asyncio
    async def test_write_path_propagates_raise_for_status(self):
        """Write must pass ``raise_for_status=True`` so callers map status codes."""
        captured_kwargs = {}

        async def fake_authenticated(method, url, raise_for_status=False, **kwargs):
            captured_kwargs["method"] = method
            captured_kwargs["raise_for_status"] = raise_for_status
            captured_kwargs["json"] = kwargs.get("json")
            return {"result": {}}

        mock_client = MagicMock()
        mock_client.make_authenticated_request = fake_authenticated

        with patch("service_now_api_oauth.get_oauth_client", return_value=mock_client):
            await make_nws_request(
                "https://x/api/now/table/vtb_task",
                method="POST",
                json_data={"short_description": "Test"},
            )

        assert captured_kwargs["method"] == "POST"
        assert captured_kwargs["raise_for_status"] is True
        assert captured_kwargs["json"] == {"short_description": "Test"}
