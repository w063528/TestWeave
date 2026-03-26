from app.models.test_result import TestResult
from app.storage.test_result_repository import TestResultRepository


def test_save_and_load_test_result_preserves_all_fields(tmp_path):
    repository = TestResultRepository(tmp_path / "test_results.json")
    result = TestResult(
        result_id="result-001",
        run_id="run-001",
        testcase_id="TC-001",
        status="Pass",
        notes="Executed manually",
    )

    repository.save(result)
    loaded = repository.load("result-001")

    assert loaded == result
