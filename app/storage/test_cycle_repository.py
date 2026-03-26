from app.models.test_cycle import TestCycle


class InMemoryTestCycleRepository:
    def __init__(self) -> None:
        self._records: dict[str, TestCycle] = {}

    def save(self, test_cycle: TestCycle) -> None:
        self._records[test_cycle.cycle_id] = test_cycle

    def load(self, cycle_id: str) -> TestCycle | None:
        return self._records.get(cycle_id)
