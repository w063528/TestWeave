import json
from pathlib import Path

from app.models.test_result import TestResult


class TestResultRepository:
    __test__ = False

    def __init__(self, file_path: Path):
        self._file_path = Path(file_path)

    def save(self, result: TestResult) -> None:
        payload = self._read_payload()
        payload[result.result_id] = {
            "result_id": result.result_id,
            "run_id": result.run_id,
            "testcase_id": result.testcase_id,
            "status": result.status,
            "notes": result.notes,
        }
        self._write_payload(payload)

    def load(self, result_id: str) -> TestResult:
        payload = self._read_payload()
        data = payload[result_id]
        return TestResult(
            result_id=data["result_id"],
            run_id=data["run_id"],
            testcase_id=data["testcase_id"],
            status=data["status"],
            notes=data["notes"],
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
