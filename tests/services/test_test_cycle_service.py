from dataclasses import fields

from app.models.tc_list_entry import TCListEntry
from app.models.test_cycle import TestCycle
from app.services.test_cycle_service import create_test_cycle


def test_create_test_cycle_builds_planning_snapshot_from_tc_list_entries():
    entries = [
        TCListEntry(
            suite_id="suite-auth-001",
            suite_name="Auth Flow",
            testcase_id="TC-001",
            testcase_name="User logs in",
        ),
        TCListEntry(
            suite_id="suite-billing-002",
            suite_name="Billing Flow",
            testcase_id="TC-101",
            testcase_name="User updates card",
        ),
    ]

    cycle = create_test_cycle("Smoke Cycle", entries)

    assert cycle.cycle_id.startswith("cycle-")
    assert cycle.cycle_name == "Smoke Cycle"
    assert cycle.tc_list_entries == tuple(entries)


def test_create_test_cycle_contains_only_allowed_cycle_fields():
    entries = [
        TCListEntry(
            suite_id="suite-001",
            suite_name="Profile",
            testcase_id="TC-200",
            testcase_name="Open profile page",
        )
    ]

    cycle = create_test_cycle("Profile Cycle", entries)

    assert [field.name for field in fields(TestCycle)] == [
        "cycle_id",
        "cycle_name",
        "tc_list_entries",
    ]
    assert hasattr(cycle, "status") is False
    assert hasattr(cycle, "run_id") is False
    assert hasattr(cycle, "results") is False


def test_create_test_cycle_keeps_snapshot_semantics_when_input_list_changes():
    entries = [
        TCListEntry(
            suite_id="suite-auth-001",
            suite_name="Auth Flow",
            testcase_id="TC-001",
            testcase_name="User logs in",
        )
    ]

    cycle = create_test_cycle("Initial Snapshot", entries)
    entries.append(
        TCListEntry(
            suite_id="suite-billing-002",
            suite_name="Billing Flow",
            testcase_id="TC-101",
            testcase_name="User updates card",
        )
    )

    assert len(cycle.tc_list_entries) == 1
    assert cycle.tc_list_entries[0].testcase_id == "TC-001"
