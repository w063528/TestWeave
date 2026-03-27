from copy import deepcopy

from app.models.test_cycle import TestCycle


class InMemoryTestCycleRepository:
    def __init__(self) -> None:
        self._cycles: dict[str, TestCycle] = {}

    def save(self, cycle: TestCycle) -> TestCycle:
        stored = deepcopy(cycle)
        self._cycles[stored.cycle_id] = stored
        return deepcopy(stored)

    def get(self, cycle_id: str) -> TestCycle:
        cycle = self._cycles.get(cycle_id)
        if cycle is None:
            raise KeyError(f"Unknown cycle_id: {cycle_id}")
        return deepcopy(cycle)

    def list_all(self) -> tuple[TestCycle, ...]:
        return tuple(deepcopy(cycle) for cycle in self._cycles.values())
