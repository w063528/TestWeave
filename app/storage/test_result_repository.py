from app.models.test_result import TestResult


class InMemoryTestResultRepository:
    def __init__(self) -> None:
        self._records: dict[str, TestResult] = {}

    def save(self, test_result: TestResult) -> None:
        self._records[test_result.result_id] = test_result

    def load(self, result_id: str) -> TestResult | None:
        return self._records.get(result_id)
