from app.models.test_cycle import TestCycle
from app.models.test_result import TestResult
from app.models.test_run import TestRun
from app.storage.test_cycle_repository import InMemoryTestCycleRepository
from app.storage.test_result_repository import InMemoryTestResultRepository
from app.storage.test_run_repository import InMemoryTestRunRepository


def test_result_repository_save_and_load_preserves_result_integrity():
    repository = InMemoryTestResultRepository()
    result = TestResult(
        result_id="result-001",
        run_id="run-001",
        testcase_id="TC-001",
        status="Pass",
        notes="validated",
    )

    repository.save(result)
    loaded = repository.get("result-001")

    assert loaded == result
    assert loaded is not result
    assert loaded is not None
    assert loaded.result_id == "result-001"
    assert loaded.run_id == "run-001"
    assert hasattr(loaded, "summary") is False


def test_result_repository_filters_results_by_run_id():
    repository = InMemoryTestResultRepository()
    repository.save(
        TestResult(
            result_id="result-001",
            run_id="run-001",
            testcase_id="TC-001",
            status="Pass",
            notes="",
        )
    )
    repository.save(
        TestResult(
            result_id="result-002",
            run_id="run-002",
            testcase_id="TC-002",
            status="Fail",
            notes="",
        )
    )

    run_001_results = repository.list_by_run("run-001")
    assert len(run_001_results) == 1
    assert run_001_results[0].result_id == "result-001"


def test_cycle_run_result_repositories_are_separated_without_cross_contamination():
    cycle_repository = InMemoryTestCycleRepository()
    run_repository = InMemoryTestRunRepository()
    result_repository = InMemoryTestResultRepository()

    cycle_repository.save(
        TestCycle(cycle_id="cycle-001", cycle_name="Cycle", tc_list_entries=())
    )
    run_repository.save(
        TestRun(
            run_id="run-001",
            cycle_id="cycle-001",
            run_name="Run",
            cycle_snapshot_entries=(),
        )
    )
    result_repository.save(
        TestResult(
            result_id="result-001",
            run_id="run-001",
            testcase_id="TC-001",
            status="Blocked",
            notes="dependency missing",
        )
    )

    assert cycle_repository.get("cycle-001") is not None
    assert run_repository.get("run-001") is not None
    assert result_repository.get("result-001") is not None

    assert cycle_repository.get("run-001") is None
    assert run_repository.get("cycle-001") is None
    assert result_repository.get("cycle-001") is None
