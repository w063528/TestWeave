from app.models.test_result import TestResult


class InMemoryTestResultRepository:
    def __init__(self) -> None:
        self._records: dict[str, dict[str, str]] = {}

    def save(self, test_result: TestResult) -> None:
        self._records[test_result.result_id] = {
            "result_id": test_result.result_id,
            "run_id": test_result.run_id,
            "testcase_id": test_result.testcase_id,
            "status": test_result.status,
            "notes": test_result.notes,
        }

    def get(self, result_id: str) -> TestResult | None:
        record = self._records.get(result_id)
        if record is None:
            return None
        return self._from_record(record)

    def list_by_run(self, run_id: str) -> tuple[TestResult, ...]:
        return tuple(
            self._from_record(record)
            for record in self._records.values()
            if record["run_id"] == run_id
        )

    @staticmethod
    def _from_record(record: dict[str, str]) -> TestResult:
        return TestResult(
            result_id=record["result_id"],
            run_id=record["run_id"],
            testcase_id=record["testcase_id"],
            status=record["status"],
            notes=record["notes"],
        )
