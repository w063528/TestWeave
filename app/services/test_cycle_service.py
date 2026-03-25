from collections.abc import Iterable
from uuid import uuid4

from app.models.tc_list_entry import TCListEntry
from app.models.test_cycle import TestCycle

_test_cycle_store: dict[str, TestCycle] = {}


def create_test_cycle(cycle_name: str, tc_list_entries: Iterable[TCListEntry]) -> TestCycle:
    return TestCycle(
        cycle_id=f"cycle-{uuid4()}",
        cycle_name=cycle_name,
        tc_list_entries=tuple(tc_list_entries),
    )


def save_test_cycle(test_cycle: TestCycle) -> None:
    _test_cycle_store[test_cycle.cycle_id] = test_cycle


def get_test_cycle(cycle_id: str) -> TestCycle | None:
    return _test_cycle_store.get(cycle_id)


def list_test_cycles() -> tuple[TestCycle, ...]:
    return tuple(_test_cycle_store.values())


def clear_test_cycle_store() -> None:
    _test_cycle_store.clear()
