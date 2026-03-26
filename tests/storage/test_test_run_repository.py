from app.models.tc_list_entry import TCListEntry
from app.models.test_run import TestRun
from app.storage.test_run_repository import InMemoryTestRunRepository


def test_run_repository_save_and_load_preserves_run_integrity():
    repository = InMemoryTestRunRepository()
    run = TestRun(
        run_id="run-001",
        cycle_id="cycle-001",
        run_name="Smoke Run 1",
        cycle_snapshot_entries=(
            TCListEntry(
                suite_id="suite-001",
                suite_name="Auth",
                testcase_id="TC-001",
                testcase_name="Login works",
            ),
        ),
    )

    repository.save(run)
    loaded = repository.get("run-001")

    assert loaded == run
    assert loaded is not run
    assert loaded is not None
    assert loaded.run_id == "run-001"
    assert loaded.cycle_id == "cycle-001"
    assert hasattr(loaded, "summary") is False
    assert hasattr(loaded, "pass_count") is False


def test_run_repository_stores_only_runs():
    repository = InMemoryTestRunRepository()
    first = TestRun(
        run_id="run-001",
        cycle_id="cycle-001",
        run_name="Run A",
        cycle_snapshot_entries=(),
    )
    second = TestRun(
        run_id="run-002",
        cycle_id="cycle-001",
        run_name="Run B",
        cycle_snapshot_entries=(),
    )

    repository.save(first)
    repository.save(second)

    all_runs = repository.list_all()
    assert {run.run_id for run in all_runs} == {"run-001", "run-002"}
