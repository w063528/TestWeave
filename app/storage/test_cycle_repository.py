from copy import deepcopy

from app.models.test_cycle import TestCycle


class InMemoryTestCycleRepository:
    def __init__(self) -> None:
        self._cycles: dict[str, TestCycle] = {}

    def save(self, cycle: TestCycle) -> None:
        self._cycles[cycle.cycle_id] = deepcopy(cycle)

    def get_by_id(self, cycle_id: str) -> TestCycle | None:
        cycle = self._cycles.get(cycle_id)
        if cycle is None:
            return None
        return deepcopy(cycle)
