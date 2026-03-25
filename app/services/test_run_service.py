from uuid import uuid4

from app.models.test_cycle import TestCycle
from app.models.test_run import TestRun


def create_test_run(run_name: str, test_cycle: TestCycle) -> TestRun:
    return TestRun(
        run_id=f"run-{uuid4()}",
        cycle_id=test_cycle.cycle_id,
        run_name=run_name,
        cycle_snapshot_entries=test_cycle.tc_list_entries,
    )
