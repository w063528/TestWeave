from dataclasses import asdict, replace

import pytest

from app.models.tc_list_entry import TCListEntry
from app.models.test_cycle import TestCycle
from app.models.test_result import TestResult
from app.models.test_run import TestRun
from app.storage.test_cycle_repository import InMemoryTestCycleRepository
from app.storage.test_result_repository import InMemoryTestResultRepository
from app.storage.test_run_repository import InMemoryTestRunRepository


def _cycle(cycle_id: str, cycle_name: str = "Cycle") -> TestCycle:
    return TestCycle(
        cycle_id=cycle_id,
        cycle_name=cycle_name,
        tc_list_entries=(
            TCListEntry(
                suite_id="suite-1",
                suite_name="Suite",
                testcase_id="TC-1",
                testcase_name="Case",
            ),
        ),
    )


def _run(run_id: str, cycle_id: str, run_name: str = "Run Alpha") -> TestRun:
    return TestRun(
        run_id=run_id,
        cycle_id=cycle_id,
        run_name=run_name,
        cycle_snapshot_entries=(
            TCListEntry(
                suite_id="suite-1",
                suite_name="Suite",
                testcase_id="TC-1",
                testcase_name="Case",
            ),
        ),
    )


def _result(result_id: str, run_id: str, status: str, notes: str = "") -> TestResult:
    return TestResult(
        result_id=result_id,
        run_id=run_id,
        testcase_id="TC-1",
        status=status,
        notes=notes,
    )


def test_risk1_identity_integrity_distinct_long_ids_do_not_collide() -> None:
    repository = InMemoryTestCycleRepository()
    long_prefix = "ID_STRICT_TEST_LONG_" + ("X" * 260)
    first_id = long_prefix + "A"
    second_id = long_prefix + "B"

    repository.save(_cycle(first_id, "Suite A"))
    repository.save(_cycle(second_id, "Suite B"))

    first_loaded = repository.get_by_id(first_id)
    second_loaded = repository.get_by_id(second_id)

    assert first_loaded is not None
    assert second_loaded is not None
    assert first_loaded.cycle_name == "Suite A"
    assert second_loaded.cycle_name == "Suite B"
    assert first_loaded != second_loaded


def test_risk2_referential_integrity_rejects_result_for_missing_run() -> None:
    run_repository = InMemoryTestRunRepository()
    result_repository = InMemoryTestResultRepository(run_repository)

    missing_parent = _result("result-1", "MISSING_999", "Fail", "orphan attempt")

    with pytest.raises(ValueError, match="missing run_id"):
        result_repository.save(missing_parent)
    assert result_repository.list_by_run_id("MISSING_999") == ()


def test_risk3_snapshot_immutability_prevents_post_retrieval_mutation_leak() -> None:
    run_repository = InMemoryTestRunRepository()
    run_repository.save(_run("run-alpha", "cycle-1", "Alpha"))

    loaded = run_repository.get_by_id("run-alpha")
    assert loaded is not None
    object.__setattr__(loaded, "run_name", "Beta")

    reloaded = run_repository.get_by_id("run-alpha")
    assert reloaded is not None
    assert reloaded.run_name == "Alpha"


def test_risk4_repository_isolation_allows_same_id_for_cycle_and_run() -> None:
    shared_id = "SHARED_ID"
    cycle_repository = InMemoryTestCycleRepository()
    run_repository = InMemoryTestRunRepository()

    cycle_repository.save(_cycle(shared_id, "Cycle Shared"))
    run_repository.save(_run(shared_id, shared_id, "Run Shared"))

    cycle_loaded = cycle_repository.get_by_id(shared_id)
    run_loaded = run_repository.get_by_id(shared_id)

    assert cycle_loaded is not None
    assert run_loaded is not None
    assert cycle_loaded.cycle_name == "Cycle Shared"
    assert run_loaded.run_name == "Run Shared"


def test_risk5_missing_entity_returns_explicit_none() -> None:
    result_repository = InMemoryTestResultRepository(InMemoryTestRunRepository())

    assert result_repository.get_by_id("NON_EXISTENT_ID_000") is None
    assert result_repository.get_by_id("!@#$%^&*()") is None
    assert result_repository.get_by_id("") is None


def test_risk6_stress_behavior_preserves_large_notes_payload_exactly() -> None:
    run_repository = InMemoryTestRunRepository()
    run_repository.save(_run("run-load", "cycle-1"))
    result_repository = InMemoryTestResultRepository(run_repository)
    large_notes = "X" * 1_000_000

    result_repository.save(_result("result-load", "run-load", "Fail", large_notes))
    loaded = result_repository.get_by_id("result-load")

    assert loaded is not None
    assert len(loaded.notes) == 1_000_000
    assert loaded.notes == large_notes


def test_risk7_phase_boundary_no_summary_persistence_on_run_records() -> None:
    run_repository = InMemoryTestRunRepository()
    run_repository.save(_run("run-summary-check", "cycle-1", "Summary Guard Run"))
    result_repository = InMemoryTestResultRepository(run_repository)

    statuses = ("Pass", "Fail", "Pass", "Fail", "Pass", "Fail", "Pass", "Fail", "Pass", "Fail")
    for idx, status in enumerate(statuses):
        result_repository.save(_result(f"result-{idx}", "run-summary-check", status, "n"))

    loaded_run = run_repository.get_by_id("run-summary-check")
    assert loaded_run is not None
    assert set(asdict(loaded_run).keys()) == {
        "run_id",
        "cycle_id",
        "run_name",
        "cycle_snapshot_entries",
        "pr_url",
        "commit_sha",
        "diff_snapshot_id",
    }
    assert loaded_run.pr_url == ""
    assert loaded_run.commit_sha == ""
    assert loaded_run.diff_snapshot_id == ""
    assert not hasattr(loaded_run, "pass_count")
    assert not hasattr(loaded_run, "fail_count")
    assert not hasattr(loaded_run, "failure_rate")
    assert not hasattr(loaded_run, "total_passed")

    original_result = result_repository.get_by_id("result-1")
    assert original_result is not None
    result_repository.save(replace(original_result, status="Pass"))

    loaded_run_after_update = run_repository.get_by_id("run-summary-check")
    assert loaded_run_after_update is not None
    assert set(asdict(loaded_run_after_update).keys()) == {
        "run_id",
        "cycle_id",
        "run_name",
        "cycle_snapshot_entries",
        "pr_url",
        "commit_sha",
        "diff_snapshot_id",
    }
