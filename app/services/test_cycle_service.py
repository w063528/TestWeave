from collections.abc import Iterable
from uuid import uuid4

from app.models.tc_list_entry import TCListEntry
from app.models.test_cycle import TestCycle


def create_test_cycle(cycle_name: str, tc_list_entries: Iterable[TCListEntry]) -> TestCycle:
    return TestCycle(
        cycle_id=f"cycle-{uuid4()}",
        cycle_name=cycle_name,
        tc_list_entries=tuple(tc_list_entries),
    )
