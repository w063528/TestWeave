from app.models.test_run import TestRun


class InMemoryTestRunRepository:
    def __init__(self) -> None:
        self._records: dict[str, TestRun] = {}

    def save(self, test_run: TestRun) -> None:
        self._records[test_run.run_id] = test_run

    def load(self, run_id: str) -> TestRun | None:
        return self._records.get(run_id)
