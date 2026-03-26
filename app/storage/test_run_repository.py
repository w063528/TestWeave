import json
from pathlib import Path

from app.models.tc_list_entry import TCListEntry
from app.models.test_run import TestRun


class TestRunRepository:
    __test__ = False

    def __init__(self, file_path: Path):
        self._file_path = Path(file_path)

    def save(self, run: TestRun) -> None:
        payload = self._read_payload()
        payload[run.run_id] = {
            "run_id": run.run_id,
            "cycle_id": run.cycle_id,
            "run_name": run.run_name,
            "cycle_snapshot_entries": [
                {
                    "suite_id": entry.suite_id,
                    "suite_name": entry.suite_name,
                    "testcase_id": entry.testcase_id,
                    "testcase_name": entry.testcase_name,
                }
                for entry in run.cycle_snapshot_entries
            ],
        }
        self._write_payload(payload)

    def load(self, run_id: str) -> TestRun:
        payload = self._read_payload()
        data = payload[run_id]
        return TestRun(
            run_id=data["run_id"],
            cycle_id=data["cycle_id"],
            run_name=data["run_name"],
            cycle_snapshot_entries=tuple(
                TCListEntry(
                    suite_id=entry["suite_id"],
                    suite_name=entry["suite_name"],
                    testcase_id=entry["testcase_id"],
                    testcase_name=entry["testcase_name"],
                )
                for entry in data["cycle_snapshot_entries"]
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
