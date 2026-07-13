"""
Tests for param_coercion.py — JSON-string coercion at the MCP tool param
boundary. Uses pydantic.TypeAdapter, the exact mechanism FastMCP uses to
validate tool arguments, so these tests exercise the real coercion path.
"""

import json

import pytest
from pydantic import TypeAdapter

from param_coercion import JsonDict, JsonList, OptJsonDict, OptJsonList


class TestJsonList:
    def test_stringified_json_array_coerces_to_list(self):
        assert TypeAdapter(JsonList).validate_python('["a","b"]') == ["a", "b"]

    def test_native_list_passes_through_unchanged(self):
        assert TypeAdapter(JsonList).validate_python(["a"]) == ["a"]

    def test_stringified_json_object_raises(self):
        with pytest.raises(Exception):
            TypeAdapter(JsonList).validate_python('{"k":"v"}')

    def test_malformed_json_string_raises(self):
        with pytest.raises(Exception):
            TypeAdapter(JsonList).validate_python("not json")


class TestOptJsonList:
    def test_stringified_json_array_coerces_to_list(self):
        assert TypeAdapter(OptJsonList).validate_python('["x","y"]') == ["x", "y"]

    def test_none_passes_through_unchanged(self):
        assert TypeAdapter(OptJsonList).validate_python(None) is None

    def test_native_list_passes_through_unchanged(self):
        assert TypeAdapter(OptJsonList).validate_python(["z"]) == ["z"]

    def test_stringified_json_object_raises(self):
        with pytest.raises(Exception):
            TypeAdapter(OptJsonList).validate_python('{"k":"v"}')

    def test_malformed_json_string_raises(self):
        with pytest.raises(Exception):
            TypeAdapter(OptJsonList).validate_python("not json")


class TestJsonDict:
    def test_stringified_json_object_coerces_to_dict(self):
        assert TypeAdapter(JsonDict).validate_python('{"k":"v"}') == {"k": "v"}

    def test_native_dict_passes_through_unchanged(self):
        assert TypeAdapter(JsonDict).validate_python({"a": 1}) == {"a": 1}

    def test_stringified_json_array_raises(self):
        with pytest.raises(Exception):
            TypeAdapter(JsonDict).validate_python('["a","b"]')

    def test_malformed_json_string_raises(self):
        with pytest.raises(Exception):
            TypeAdapter(JsonDict).validate_python("not json")


class TestOptJsonDict:
    def test_stringified_json_object_coerces_to_dict(self):
        assert TypeAdapter(OptJsonDict).validate_python('{"k":"v"}') == {"k": "v"}

    def test_none_passes_through_unchanged(self):
        assert TypeAdapter(OptJsonDict).validate_python(None) is None

    def test_native_dict_passes_through_unchanged(self):
        assert TypeAdapter(OptJsonDict).validate_python({"a": 1}) == {"a": 1}

    def test_stringified_json_array_raises(self):
        with pytest.raises(Exception):
            TypeAdapter(OptJsonDict).validate_python('["a","b"]')

    def test_malformed_json_string_raises(self):
        with pytest.raises(Exception):
            TypeAdapter(OptJsonDict).validate_python("not json")


class TestDoubleEncoding:
    """Regression tests for the double-encoding bug found in E2E: some MCP
    clients double-encode flat top-level JSON params, so the raw value is a
    JSON string of a JSON string. Both single- and double-encoded input must
    coerce; malformed input must still raise."""

    def test_double_encoded_list_coerces(self):
        double_encoded = json.dumps(json.dumps(["a", "b"]))
        assert TypeAdapter(JsonList).validate_python(double_encoded) == ["a", "b"]

    def test_double_encoded_opt_dict_coerces(self):
        double_encoded = json.dumps(json.dumps({"k": "v"}))
        assert TypeAdapter(OptJsonDict).validate_python(double_encoded) == {"k": "v"}

    def test_single_encoded_list_still_works(self):
        assert TypeAdapter(JsonList).validate_python(json.dumps(["a"])) == ["a"]

    def test_malformed_not_json_at_all_raises(self):
        with pytest.raises(Exception):
            TypeAdapter(JsonList).validate_python("not json at all")

    def test_malformed_dict_where_array_expected_raises(self):
        with pytest.raises(Exception):
            TypeAdapter(JsonList).validate_python('{"k":"v"}')
