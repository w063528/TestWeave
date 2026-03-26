from app.models.test_result import TestResult
from app.storage.test_result_repository import InMemoryTestResultRepository


def test_save_then_load_test_result_preserves_entity_integrity():
    repository = InMemoryTestResultRepository()
    entity = TestResult(
        result_id="result-001",
        run_id="run-001",
        testcase_id="TC-001",
        status="Pass",
        notes="manual pass",
    )

    repository.save(entity)
    loaded = repository.load("result-001")

    assert loaded == entity
