from dataclasses import dataclass
from typing import Final

ALLOWED_TEST_RESULT_STATUSES: Final[tuple[str, ...]] = (
    "Not Run",
    "Pass",
    "Fail",
    "Blocked",
)


@dataclass(frozen=True, slots=True)
class TestResult:
    __test__ = False
    result_id: str
    run_id: str
    testcase_id: str
    status: str
    notes: str
