from dataclasses import dataclass

from app.models.tc_list_entry import TCListEntry


@dataclass(frozen=True, slots=True)
class TestCycle:
    __test__ = False
    cycle_id: str
    cycle_name: str
    tc_list_entries: tuple[TCListEntry, ...]
