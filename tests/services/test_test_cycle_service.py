from dataclasses import fields

import pytest

from app.models.tc_list_entry import TCListEntry
from app.models.test_cycle import TestCycle
from app.services.test_cycle_service import (
    clear_test_cycle_store,
    create_test_cycle,
    get_test_cycle,
    list_test_cycles,
    save_test_cycle,
)


@pytest.fixture(autouse=True)
def _clear_cycle_store_between_tests():
    clear_test_cycle_store()
    yield
    clear_test_cycle_store()


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


def test_test_cycle_can_be_saved_and_loaded_from_store():
    cycle = create_test_cycle("Persistence Cycle", [])

    save_test_cycle(cycle)
    loaded = get_test_cycle(cycle.cycle_id)

    assert loaded == cycle


def test_list_test_cycles_returns_all_persisted_cycles():
    first = create_test_cycle("Cycle A", [])
    second = create_test_cycle("Cycle B", [])

    save_test_cycle(first)
    save_test_cycle(second)

    persisted = list_test_cycles()

    assert persisted == (first, second)
