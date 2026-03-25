from dataclasses import fields

import pytest

from app.models.tc_list_entry import TCListEntry
from app.models.test_run import TestRun
from app.services.test_cycle_service import create_test_cycle
from app.services.test_run_service import (
    clear_test_run_store,
    create_test_run,
    get_test_run,
    list_test_runs,
    save_test_run,
)


@pytest.fixture(autouse=True)
def _clear_run_store_between_tests():
    clear_test_run_store()
    yield
    clear_test_run_store()


def test_create_test_run_builds_execution_instance_from_test_cycle():
    cycle_entries = [
        TCListEntry(
            suite_id="suite-auth-001",
            suite_name="Auth",
            testcase_id="TC-001",
            testcase_name="Login succeeds",
        ),
        TCListEntry(
            suite_id="suite-auth-001",
            suite_name="Auth",
            testcase_id="TC-002",
            testcase_name="Login fails with wrong password",
        ),
    ]
    cycle = create_test_cycle("Auth Regression", cycle_entries)

    run = create_test_run("Auth Regression Run 1", cycle)

    assert run.run_id.startswith("run-")
    assert run.cycle_id == cycle.cycle_id
    assert run.run_name == "Auth Regression Run 1"
    assert run.cycle_snapshot_entries == cycle.tc_list_entries


def test_create_test_run_contains_only_allowed_fields_and_no_result_leakage():
    assert [field.name for field in fields(TestRun)] == [
        "run_id",
        "cycle_id",
        "run_name",
        "cycle_snapshot_entries",
    ]

    cycle = create_test_cycle("Core Flow", [])
    run = create_test_run("Core Flow Run", cycle)

    assert hasattr(run, "results") is False
    assert hasattr(run, "result_count") is False
    assert hasattr(run, "pass_count") is False
    assert hasattr(run, "fail_count") is False
    assert hasattr(run, "summary") is False
    assert hasattr(run, "status") is False


def test_create_test_run_does_not_mutate_test_cycle_snapshot():
    initial_entries = [
        TCListEntry(
            suite_id="suite-billing-002",
            suite_name="Billing",
            testcase_id="TC-101",
            testcase_name="Card update works",
        )
    ]
    cycle = create_test_cycle("Billing Cycle", initial_entries)
    original_snapshot = cycle.tc_list_entries

    run = create_test_run("Billing Run", cycle)

    assert cycle.tc_list_entries == original_snapshot
    assert run.cycle_snapshot_entries == original_snapshot


def test_test_run_can_be_saved_and_loaded_from_store():
    cycle = create_test_cycle("Execution Cycle", [])
    run = create_test_run("Execution Run", cycle)

    save_test_run(run)
    loaded = get_test_run(run.run_id)

    assert loaded == run


def test_list_test_runs_returns_all_persisted_runs():
    cycle = create_test_cycle("Regression", [])
    first = create_test_run("Run 1", cycle)
    second = create_test_run("Run 2", cycle)

    save_test_run(first)
    save_test_run(second)

    persisted = list_test_runs()

    assert persisted == (first, second)
