from dataclasses import fields

import pytest

from app.models.tc_list_entry import TCListEntry
from app.models.test_cycle import TestCycle
from app.models.test_result import TestResult
from app.models.test_run import TestRun
from app.services.test_cycle_service import create_test_cycle
from app.services.test_result_service import create_test_result
from app.services.test_run_service import create_test_run


@pytest.mark.parametrize("status", ["Not Run", "Pass", "Fail", "Blocked"])
def test_create_test_result_records_execution_outcome_per_testcase(status: str):
    result = create_test_result(
        run_id="run-123",
        testcase_id="TC-001",
        status=status,
        notes="manual execution note",
    )

    assert result == TestResult(
        run_id="run-123",
        testcase_id="TC-001",
        status=status,
        notes="manual execution note",
    )


def test_create_test_result_rejects_undocumented_status():
    with pytest.raises(ValueError, match="Unsupported TestResult status"):
        create_test_result(
            run_id="run-123",
            testcase_id="TC-001",
            status="Skipped",
            notes="",
        )


def test_create_test_result_contains_only_phase_7_fields_and_no_summary_leakage():
    result = create_test_result(
        run_id="run-123",
        testcase_id="TC-001",
        status="Pass",
        notes="",
    )

    assert [field.name for field in fields(TestResult)] == [
        "run_id",
        "testcase_id",
        "status",
        "notes",
    ]
    assert hasattr(result, "cycle_id") is False
    assert hasattr(result, "run_name") is False
    assert hasattr(result, "pass_count") is False
    assert hasattr(result, "fail_count") is False
    assert hasattr(result, "summary") is False


def test_create_test_result_keeps_results_separate_from_test_run_and_test_cycle():
    cycle_entries = [
        TCListEntry(
            suite_id="suite-auth-001",
            suite_name="Auth",
            testcase_id="TC-001",
            testcase_name="Login succeeds",
        )
    ]
    cycle = create_test_cycle("Auth Cycle", cycle_entries)
    run = create_test_run("Auth Run 1", cycle)
    original_cycle_snapshot = cycle.tc_list_entries
    original_run_snapshot = run.cycle_snapshot_entries

    result = create_test_result(
        run_id=run.run_id,
        testcase_id=cycle_entries[0].testcase_id,
        status="Fail",
        notes="assertion mismatch",
    )

    assert isinstance(result, TestResult)
    assert isinstance(cycle, TestCycle)
    assert isinstance(run, TestRun)
    assert result.run_id == run.run_id
    assert result.testcase_id == cycle_entries[0].testcase_id
    assert cycle.tc_list_entries == original_cycle_snapshot
    assert run.cycle_snapshot_entries == original_run_snapshot
    assert hasattr(run, "results") is False
    assert hasattr(cycle, "results") is False
