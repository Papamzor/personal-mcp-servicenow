"""One spec per supported table — the single source of truth (v5.0 "Boron" Tier 3.2).

Before this, a table's configuration was scattered across five collections in
`constants.py`: `TABLE_CONFIGS`, `ESSENTIAL_FIELDS`, `DETAIL_FIELDS`,
`TABLE_ERROR_MESSAGES`, and the `TABLES_WITHOUT_RECORD_IDENTITY` / text-search
maps. Commit cf2d7e2 ("allow meta and meta_description on knowledge article
updates") needed coordinated edits to three of them for one logical change, and
nothing stopped a table being added to one and forgotten in another.

`TABLE_SPECS` collapses all of it into one `TableSpec` per table. `constants.py`
derives the old dicts from it (compatibility views — every existing
`from constants import ESSENTIAL_FIELDS` still works), so the surface is
unchanged; only the source of truth moved. Change a table in exactly one place.

The `task_sla` foot-gun is now structural, not a hand-maintained exclusion list:
`number_field=None` means "cannot be addressed by number", and
`TABLES_WITHOUT_RECORD_IDENTITY` is *derived* from that. A table with no number
field cannot be left out of the guard, because the guard IS the set of
number_field-less specs. (task_sla has no `number` and no `short_description` of
its own — a filter against either is silently dropped by ServiceNow, the same
failure mode as the 1.2M-token get_sla_details bug.)

`tests/test_table_spec.py` pins the key-set consistency the scattered dicts never
had: every derived view has exactly the TABLE_SPECS key set, and each spec is
well-formed.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Optional, Tuple

# Default free-text search column, and the task_sla dot-walk override. task_sla
# carries no short_description of its own — the text lives on the referenced task.
# Public (not underscored) because constants.TEXT_SEARCH_FIELD /
# TASK_SLA_TEXT_SEARCH_FIELD are derived from these SAME literals — the exact
# columns whose mismatch historically caused silent ServiceNow drops live in one
# place, not two independent copies.
DEFAULT_TEXT_SEARCH_FIELD = "short_description"
TASK_SLA_TEXT_SEARCH_FIELD = "task.short_description"


@dataclass(frozen=True)
class TableSpec:
    """Everything the server needs to know about one ServiceNow table.

    `number_field` is the structural identity marker: `None` means the table
    cannot be addressed by a record number (task_sla), which is what makes the
    number-/text-addressed generic tools refuse it up front rather than build a
    query against a field that does not exist.
    """
    key: str
    display_name: str
    number_prefix: Optional[str]
    number_field: Optional[str]
    priority_field: Optional[str]
    state_field: str
    text_search_field: str
    supports_work_notes: bool
    supports_comments: bool
    essential_fields: Tuple[str, ...]
    detail_fields: Tuple[str, ...]
    error_message: str

    @property
    def has_record_identity(self) -> bool:
        """True when the table can be addressed by a record number."""
        return self.number_field is not None

    def __post_init__(self) -> None:
        """Enforce the number_field / number_prefix co-movement invariant.

        The old hand-maintained exclusion list implicitly tied "no number" to "no
        prefix". Splitting them into two fields would let a future edit desync
        them — `number_prefix="X"` with `number_field=None` (guard refuses
        identity tools while the prefix looks real), or the reverse. Both are
        nonsense; refuse them at construction so `has_record_identity` and the
        prefix consumers can never disagree.
        """
        if (self.number_field is None) != (self.number_prefix is None):
            raise ValueError(
                f"{self.key}: number_field and number_prefix must both be set "
                f"or both be None (got number_field={self.number_field!r}, "
                f"number_prefix={self.number_prefix!r})"
            )
        if self.number_field is not None:
            if self.number_field != "number":
                raise ValueError(
                    f"{self.key}: an addressable table's number_field must be "
                    f"'number', got {self.number_field!r}"
                )
            if not self.number_prefix:
                raise ValueError(f"{self.key}: an addressable table needs a non-empty number_prefix")


def _spec(**kwargs) -> TableSpec:
    # Every table addressable by number uses the literal `number` field, and
    # short_description as its text-search column; the two exceptions (task_sla)
    # pass explicit values. Defaults keep the registry below readable.
    kwargs.setdefault("number_field", "number")
    kwargs.setdefault("text_search_field", DEFAULT_TEXT_SEARCH_FIELD)
    return TableSpec(**kwargs)


# Read-only mapping: the SSOT registry is the one structure that most benefits
# from immutability, since constants.py snapshots derived views at import — an
# accidental TABLE_SPECS[...] = ... / .pop after import would desync them.
TABLE_SPECS = MappingProxyType({
    "incident": _spec(
        key="incident",
        display_name="Incident",
        number_prefix="INC",
        priority_field="priority",
        state_field="state",
        supports_work_notes=True,
        supports_comments=True,
        essential_fields=("number", "short_description", "priority", "state", "category", "sys_created_on"),
        detail_fields=(
            "number", "short_description", "description", "priority", "state", "category",
            "sys_created_on", "sys_updated_on", "opened_at", "assigned_to", "assignment_group",
            "work_notes", "comments", "u_reference_1", "company", "cmdb_ci", "correlation_id",
            "major_incident_state",
        ),
        error_message="Incident not found.",
    ),
    "change_request": _spec(
        key="change_request",
        display_name="Change Request",
        number_prefix="CHG",
        priority_field="priority",
        state_field="state",
        supports_work_notes=True,
        supports_comments=True,
        essential_fields=("number", "short_description", "priority", "state", "sys_created_on"),
        detail_fields=(
            "number", "short_description", "description", "priority", "state", "sys_created_on",
            "sys_updated_on", "opened_at", "assigned_to", "assignment_group", "work_notes",
            "comments", "u_reference_1", "company", "cmdb_ci", "type", "urgency", "impact", "risk",
            "start_date", "end_date", "implementation_plan", "backout_plan", "test_plan",
            "u_communication",
        ),
        error_message="Change not found.",
    ),
    "sc_req_item": _spec(
        key="sc_req_item",
        display_name="Service Catalog Request Item",
        number_prefix="RITM",
        priority_field="priority",
        state_field="state",
        supports_work_notes=False,
        supports_comments=True,
        essential_fields=("number", "short_description", "priority", "state", "sys_created_on", "cat_item"),
        detail_fields=(
            "number", "short_description", "description", "priority", "state", "sys_created_on",
            "assigned_to", "assignment_group", "comments", "cat_item", "request", "stage",
        ),
        error_message="Request Item not found.",
    ),
    "sc_task": _spec(
        key="sc_task",
        display_name="Service Catalog Task",
        number_prefix="SCTASK",
        priority_field="priority",
        state_field="state",
        supports_work_notes=True,
        supports_comments=True,
        essential_fields=("number", "short_description", "priority", "state", "sys_created_on", "request_item"),
        detail_fields=(
            "number", "short_description", "description", "priority", "state", "sys_created_on",
            "sys_updated_on", "opened_at", "assigned_to", "assignment_group", "comments",
            "request_item", "request",
        ),
        error_message="Service Catalog Task not found.",
    ),
    "universal_request": _spec(
        key="universal_request",
        display_name="Universal Request",
        number_prefix="UR",
        priority_field="priority",
        state_field="state",
        supports_work_notes=False,
        supports_comments=True,
        essential_fields=("number", "short_description", "priority", "state", "sys_created_on"),
        detail_fields=(
            "number", "short_description", "priority", "state", "sys_created_on", "sys_updated_on",
            "assigned_to", "assignment_group", "comments", "u_reference_1", "company", "cmdb_ci",
        ),
        error_message="Universal Request not found.",
    ),
    "kb_knowledge": _spec(
        key="kb_knowledge",
        display_name="Knowledge Base Article",
        number_prefix="KB",
        priority_field=None,
        state_field="workflow_state",
        supports_work_notes=False,
        supports_comments=False,
        essential_fields=("number", "short_description", "kb_category", "workflow_state", "sys_created_on"),
        detail_fields=(
            "number", "short_description", "text", "kb_category", "workflow_state",
            "sys_created_on", "assigned_to", "meta", "meta_description",
        ),
        error_message="Knowledge article not found.",
    ),
    "vtb_task": _spec(
        key="vtb_task",
        display_name="Private Task",
        number_prefix="VTB",
        priority_field="priority",
        state_field="state",
        supports_work_notes=True,
        supports_comments=True,
        essential_fields=("number", "short_description", "priority", "state", "sys_created_on"),
        detail_fields=(
            "number", "short_description", "priority", "state", "sys_created_on", "assigned_to",
            "assignment_group", "work_notes", "comments",
        ),
        error_message="Private task not found.",
    ),
    "task_sla": _spec(
        key="task_sla",
        display_name="Task SLA",
        number_prefix=None,
        number_field=None,  # no record number -> structurally lacks record identity
        priority_field=None,
        state_field="stage",
        text_search_field=TASK_SLA_TEXT_SEARCH_FIELD,  # no short_description of its own
        supports_work_notes=False,
        supports_comments=False,
        essential_fields=("task", "sla", "stage", "business_percentage", "active", "sys_created_on"),
        detail_fields=(
            "task", "sla", "stage", "business_percentage", "active", "sys_created_on", "breach_time",
            "business_time_left", "duration", "has_breached", "business_duration",
            "business_elapsed_time", "planned_end_time",
        ),
        error_message="SLA record not found.",
    ),
})
