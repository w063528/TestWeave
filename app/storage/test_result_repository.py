from copy import deepcopy

from app.models.test_result import TestResult
from app.storage.test_run_repository import InMemoryTestRunRepository


class InMemoryTestResultRepository:
    def __init__(self, run_repository: InMemoryTestRunRepository) -> None:
        self._run_repository = run_repository
        self._results: dict[str, TestResult] = {}
        self._result_ids_by_run: dict[str, list[str]] = {}

    def save(self, result: TestResult) -> None:
        if self._run_repository.get_by_id(result.run_id) is None:
            raise ValueError(f"Cannot save TestResult for missing run_id: {result.run_id}")

        self._results[result.result_id] = deepcopy(result)
        ids = self._result_ids_by_run.setdefault(result.run_id, [])
        if result.result_id not in ids:
            ids.append(result.result_id)

    def get_by_id(self, result_id: str) -> TestResult | None:
        result = self._results.get(result_id)
        if result is None:
            return None
        return deepcopy(result)

    def list_by_run_id(self, run_id: str) -> tuple[TestResult, ...]:
        ids = self._result_ids_by_run.get(run_id, [])
        return tuple(deepcopy(self._results[result_id]) for result_id in ids)
