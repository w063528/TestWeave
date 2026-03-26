from dataclasses import asdict

from app.models.tc_list_entry import TCListEntry
from app.models.test_run import TestRun


class InMemoryTestRunRepository:
    def __init__(self) -> None:
        self._records: dict[str, dict[str, object]] = {}

    def save(self, test_run: TestRun) -> None:
        self._records[test_run.run_id] = {
            "run_id": test_run.run_id,
            "cycle_id": test_run.cycle_id,
            "run_name": test_run.run_name,
            "cycle_snapshot_entries": [
                asdict(entry) for entry in test_run.cycle_snapshot_entries
            ],
        }

    def get(self, run_id: str) -> TestRun | None:
        record = self._records.get(run_id)
        if record is None:
            return None
        return self._from_record(record)

    def list_all(self) -> tuple[TestRun, ...]:
        return tuple(self._from_record(record) for record in self._records.values())

    @staticmethod
    def _from_record(record: dict[str, object]) -> TestRun:
        raw_entries = record["cycle_snapshot_entries"]
        entries = tuple(TCListEntry(**entry) for entry in raw_entries)
        return TestRun(
            run_id=record["run_id"],
            cycle_id=record["cycle_id"],
            run_name=record["run_name"],
            cycle_snapshot_entries=entries,
        )
