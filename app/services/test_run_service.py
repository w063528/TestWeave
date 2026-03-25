from uuid import uuid4

from app.models.test_cycle import TestCycle
from app.models.test_run import TestRun

_test_run_store: dict[str, TestRun] = {}


def create_test_run(run_name: str, test_cycle: TestCycle) -> TestRun:
    return TestRun(
        run_id=f"run-{uuid4()}",
        cycle_id=test_cycle.cycle_id,
        run_name=run_name,
        cycle_snapshot_entries=test_cycle.tc_list_entries,
    )


def save_test_run(test_run: TestRun) -> None:
    _test_run_store[test_run.run_id] = test_run


def get_test_run(run_id: str) -> TestRun | None:
    return _test_run_store.get(run_id)


def list_test_runs() -> tuple[TestRun, ...]:
    return tuple(_test_run_store.values())


def clear_test_run_store() -> None:
    _test_run_store.clear()
