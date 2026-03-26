import json
from pathlib import Path

from app.models.tc_list_entry import TCListEntry
from app.models.test_cycle import TestCycle


class TestCycleRepository:
    __test__ = False

    def __init__(self, file_path: Path):
        self._file_path = Path(file_path)

    def save(self, cycle: TestCycle) -> None:
        payload = self._read_payload()
        payload[cycle.cycle_id] = {
            "cycle_id": cycle.cycle_id,
            "cycle_name": cycle.cycle_name,
            "tc_list_entries": [
                {
                    "suite_id": entry.suite_id,
                    "suite_name": entry.suite_name,
                    "testcase_id": entry.testcase_id,
                    "testcase_name": entry.testcase_name,
                }
                for entry in cycle.tc_list_entries
            ],
        }
        self._write_payload(payload)

    def load(self, cycle_id: str) -> TestCycle:
        payload = self._read_payload()
        data = payload[cycle_id]
        return TestCycle(
            cycle_id=data["cycle_id"],
            cycle_name=data["cycle_name"],
            tc_list_entries=tuple(
                TCListEntry(
                    suite_id=entry["suite_id"],
                    suite_name=entry["suite_name"],
                    testcase_id=entry["testcase_id"],
                    testcase_name=entry["testcase_name"],
                )
                for entry in data["tc_list_entries"]
            ),
        )

    def _read_payload(self) -> dict[str, dict]:
        if not self._file_path.exists():
            return {}
        return json.loads(self._file_path.read_text(encoding="utf-8"))

    def _write_payload(self, payload: dict[str, dict]) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        self._file_path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
