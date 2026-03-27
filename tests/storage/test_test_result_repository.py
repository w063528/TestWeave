import pytest

from app.models.test_result import TestResult
from app.storage.test_result_repository import InMemoryTestResultRepository


def _result(result_id: str, run_id: str, testcase_id: str, status: str) -> TestResult:
    return TestResult(
        result_id=result_id,
        run_id=run_id,
        testcase_id=testcase_id,
        status=status,
        notes="note",
    )


def test_result_repository_save_and_load_integrity():
    repository = InMemoryTestResultRepository()
    result = _result("result-001", "run-001", "TC-001", "Pass")

    repository.save(result)
    loaded = repository.get("result-001")

    assert loaded == result
    assert loaded.run_id == "run-001"
    assert loaded.testcase_id == "TC-001"
    assert hasattr(loaded, "summary") is False
    assert hasattr(loaded, "pass_count") is False


def test_result_repository_separates_results_by_run_id():
    repository = InMemoryTestResultRepository()
    run_1_a = _result("result-001", "run-1", "TC-001", "Pass")
    run_1_b = _result("result-002", "run-1", "TC-002", "Fail")
    run_2_a = _result("result-003", "run-2", "TC-003", "Blocked")

    repository.save(run_1_a)
    repository.save(run_1_b)
    repository.save(run_2_a)

    assert repository.list_by_run_id("run-1") == (run_1_a, run_1_b)
    assert repository.list_by_run_id("run-2") == (run_2_a,)


def test_result_repository_get_unknown_result_raises_key_error():
    repository = InMemoryTestResultRepository()

    with pytest.raises(KeyError, match="Unknown result_id"):
        repository.get("result-missing")
