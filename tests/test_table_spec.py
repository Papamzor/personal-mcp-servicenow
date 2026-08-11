"""TableSpec consistency (v5.0 "Boron" Tier 3.2).

The scattered per-table dicts never had this: nothing forced TABLE_CONFIGS,
ESSENTIAL_FIELDS, DETAIL_FIELDS and TABLE_ERROR_MESSAGES to describe the SAME set
of tables, so a table could be added to one and forgotten in another (the class
of coordination bug cf2d7e2 hit). Now they are all derived from TABLE_SPECS;
these tests pin that the derivation stays faithful and every spec is well-formed.
"""
from __future__ import annotations

import pytest

import constants as c
from table_spec import TABLE_SPECS, TableSpec

_SPEC_KEYS = set(TABLE_SPECS)


class TestKeySetConsistency:
    """Every derived view covers exactly the TABLE_SPECS table set."""

    def test_derived_dicts_share_the_spec_key_set(self):
        for name, view in [
            ("TABLE_CONFIGS", c.TABLE_CONFIGS),
            ("ESSENTIAL_FIELDS", c.ESSENTIAL_FIELDS),
            ("DETAIL_FIELDS", c.DETAIL_FIELDS),
            ("TABLE_ERROR_MESSAGES", c.TABLE_ERROR_MESSAGES),
        ]:
            assert set(view) == _SPEC_KEYS, f"{name} key set drifted from TABLE_SPECS"

    def test_registry_key_matches_spec_key_field(self):
        for name, spec in TABLE_SPECS.items():
            assert spec.key == name, f"{name}: spec.key={spec.key!r} disagrees with its registry key"

    def test_table_configs_api_name_equals_key(self):
        for name, cfg in c.TABLE_CONFIGS.items():
            assert cfg["api_name"] == name


class TestStructuralIdentityGuard:
    """The task_sla foot-gun is derived from number_field, not a hand list."""

    def test_identity_guard_is_the_set_of_number_field_less_specs(self):
        expected = frozenset(n for n, s in TABLE_SPECS.items() if s.number_field is None)
        assert c.TABLES_WITHOUT_RECORD_IDENTITY == expected

    def test_task_sla_has_no_record_identity(self):
        assert TABLE_SPECS["task_sla"].number_field is None
        assert not TABLE_SPECS["task_sla"].has_record_identity
        assert "task_sla" in c.TABLES_WITHOUT_RECORD_IDENTITY

    def test_every_other_table_has_record_identity(self):
        for name, spec in TABLE_SPECS.items():
            if name == "task_sla":
                continue
            assert spec.number_field == "number", name
            assert spec.has_record_identity
            assert name not in c.TABLES_WITHOUT_RECORD_IDENTITY


class TestSpecWellFormed:
    """Each spec carries the fields consumers rely on, with sane types."""

    def test_every_spec_is_a_tablespec(self):
        assert all(isinstance(s, TableSpec) for s in TABLE_SPECS.values())

    def test_required_string_fields_present(self):
        for name, spec in TABLE_SPECS.items():
            assert isinstance(spec.display_name, str), name
            assert spec.display_name, name
            assert isinstance(spec.state_field, str), name
            assert spec.state_field, name
            assert isinstance(spec.text_search_field, str), name
            assert spec.text_search_field, name
            assert spec.error_message.endswith("."), name

    def test_field_lists_are_non_empty_and_start_with_essentials_subset(self):
        for name, spec in TABLE_SPECS.items():
            assert spec.essential_fields, name
            assert spec.detail_fields, name
            # Essentials should be a subset of detail (detail is the superset view).
            missing = set(spec.essential_fields) - set(spec.detail_fields)
            assert not missing, f"{name}: essential fields missing from detail: {missing}"

    def test_optional_fields_typed_none_or_str(self):
        for name, spec in TABLE_SPECS.items():
            for attr in ("number_prefix", "number_field", "priority_field"):
                val = getattr(spec, attr)
                assert val is None or isinstance(val, str), f"{name}.{attr}"

    def test_text_search_field_default_or_dotwalk(self):
        # A table searches its own short_description unless it dot-walks (task_sla).
        for name, spec in TABLE_SPECS.items():
            if name == "task_sla":
                assert spec.text_search_field == c.TASK_SLA_TEXT_SEARCH_FIELD == "task.short_description"
            else:
                assert spec.text_search_field == c.TEXT_SEARCH_FIELD == "short_description"


class TestDerivationFidelity:
    """Each derived collection maps the CORRECT spec attribute — not just the right
    key set. A wrong wiring in constants.py (error_message→display_name, swapped
    essential/detail, wrong supports_* field) would pass the key-set tests but
    break consumers; this locks the byte-identical-vs-HEAD claim structurally."""

    def test_field_lists_derived_correctly(self):
        for name, spec in TABLE_SPECS.items():
            assert c.ESSENTIAL_FIELDS[name] == list(spec.essential_fields), name
            assert c.DETAIL_FIELDS[name] == list(spec.detail_fields), name

    def test_error_messages_derived_correctly(self):
        for name, spec in TABLE_SPECS.items():
            assert c.TABLE_ERROR_MESSAGES[name] == spec.error_message, name

    def test_table_configs_fields_derived_correctly(self):
        for name, spec in TABLE_SPECS.items():
            cfg = c.TABLE_CONFIGS[name]
            assert cfg["api_name"] == name, name
            assert cfg["display_name"] == spec.display_name, name
            assert cfg["number_prefix"] == spec.number_prefix, name
            assert cfg["priority_field"] == spec.priority_field, name
            assert cfg["state_field"] == spec.state_field, name
            assert cfg["supports_work_notes"] == spec.supports_work_notes, name
            assert cfg["supports_comments"] == spec.supports_comments, name

    def test_text_search_map_is_the_non_default_overrides(self):
        for name, spec in TABLE_SPECS.items():
            assert c.text_search_field_for(name) == spec.text_search_field, name
        overrides = {
            n: s.text_search_field
            for n, s in TABLE_SPECS.items()
            if s.text_search_field != c.TEXT_SEARCH_FIELD
        }
        assert c.TEXT_SEARCH_FIELD_BY_TABLE == overrides


class TestConstructionInvariants:
    """__post_init__ refuses number_field / number_prefix desync, and the registry
    is read-only so derived views cannot silently drift from it."""

    def test_prefix_without_number_field_is_rejected(self):
        with pytest.raises(ValueError):
            TableSpec(
                key="x", display_name="X", number_prefix="X", number_field=None,
                priority_field=None, state_field="state",
                text_search_field="short_description",
                supports_work_notes=False, supports_comments=False,
                essential_fields=("number",), detail_fields=("number",),
                error_message="X not found.",
            )

    def test_number_field_without_prefix_is_rejected(self):
        with pytest.raises(ValueError):
            TableSpec(
                key="x", display_name="X", number_prefix=None, number_field="number",
                priority_field=None, state_field="state",
                text_search_field="short_description",
                supports_work_notes=False, supports_comments=False,
                essential_fields=("number",), detail_fields=("number",),
                error_message="X not found.",
            )

    def test_non_number_identity_field_is_rejected(self):
        with pytest.raises(ValueError):
            TableSpec(
                key="x", display_name="X", number_prefix="X", number_field="task",
                priority_field=None, state_field="state",
                text_search_field="short_description",
                supports_work_notes=False, supports_comments=False,
                essential_fields=("number",), detail_fields=("number",),
                error_message="X not found.",
            )

    def test_registry_is_read_only(self):
        with pytest.raises(TypeError):
            TABLE_SPECS["incident"] = None  # type: ignore[index]
