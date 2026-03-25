from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TestReport:
    __test__ = False
    total: int
    passed: int
    failed: int
    skipped: int

