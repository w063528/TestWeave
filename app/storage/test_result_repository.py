from copy import deepcopy

from app.models.test_result import TestResult


class InMemoryTestResultRepository:
    def __init__(self) -> None:
        self._results: dict[str, TestResult] = {}

    def save(self, result: TestResult) -> TestResult:
        stored = deepcopy(result)
        self._results[stored.result_id] = stored
        return deepcopy(stored)

    def get(self, result_id: str) -> TestResult:
        result = self._results.get(result_id)
        if result is None:
            raise KeyError(f"Unknown result_id: {result_id}")
        return deepcopy(result)

    def list_by_run_id(self, run_id: str) -> tuple[TestResult, ...]:
        results = (result for result in self._results.values() if result.run_id == run_id)
        return tuple(deepcopy(result) for result in results)
