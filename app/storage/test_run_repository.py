from copy import deepcopy

from app.models.test_run import TestRun


class InMemoryTestRunRepository:
    def __init__(self) -> None:
        self._runs: dict[str, TestRun] = {}

    def save(self, run: TestRun) -> TestRun:
        stored = deepcopy(run)
        self._runs[stored.run_id] = stored
        return deepcopy(stored)

    def get(self, run_id: str) -> TestRun:
        run = self._runs.get(run_id)
        if run is None:
            raise KeyError(f"Unknown run_id: {run_id}")
        return deepcopy(run)

    def list_by_cycle_id(self, cycle_id: str) -> tuple[TestRun, ...]:
        runs = (run for run in self._runs.values() if run.cycle_id == cycle_id)
        return tuple(deepcopy(run) for run in runs)
