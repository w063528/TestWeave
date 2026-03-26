from dataclasses import asdict

from app.models.tc_list_entry import TCListEntry
from app.models.test_cycle import TestCycle


class InMemoryTestCycleRepository:
    def __init__(self) -> None:
        self._records: dict[str, dict[str, object]] = {}

    def save(self, test_cycle: TestCycle) -> None:
        self._records[test_cycle.cycle_id] = {
            "cycle_id": test_cycle.cycle_id,
            "cycle_name": test_cycle.cycle_name,
            "tc_list_entries": [asdict(entry) for entry in test_cycle.tc_list_entries],
        }

    def get(self, cycle_id: str) -> TestCycle | None:
        record = self._records.get(cycle_id)
        if record is None:
            return None
        return self._from_record(record)

    def list_all(self) -> tuple[TestCycle, ...]:
        return tuple(self._from_record(record) for record in self._records.values())

    @staticmethod
    def _from_record(record: dict[str, object]) -> TestCycle:
        raw_entries = record["tc_list_entries"]
        entries = tuple(TCListEntry(**entry) for entry in raw_entries)
        return TestCycle(
            cycle_id=record["cycle_id"],
            cycle_name=record["cycle_name"],
            tc_list_entries=entries,
        )
