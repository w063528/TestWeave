from copy import deepcopy

from app.models.test_run import TestRun


class InMemoryTestRunRepository:
    def __init__(self) -> None:
        self._runs: dict[str, TestRun] = {}

    def save(self, run: TestRun) -> None:
        self._runs[run.run_id] = deepcopy(run)

    def get_by_id(self, run_id: str) -> TestRun | None:
        run = self._runs.get(run_id)
        if run is None:
            return None
        return deepcopy(run)
