import pytest

from app.models.tc_list_entry import TCListEntry
from app.models.test_run import TestRun
from app.storage.test_run_repository import InMemoryTestRunRepository


def _snapshot() -> tuple[TCListEntry, ...]:
    return (
        TCListEntry(
            suite_id="suite-auth-001",
            suite_name="Auth",
            testcase_id="TC-001",
            testcase_name="Login",
        ),
    )


def test_run_repository_save_and_load_integrity():
    repository = InMemoryTestRunRepository()
    run = TestRun(
        run_id="run-001",
        cycle_id="cycle-001",
        run_name="Run 1",
        cycle_snapshot_entries=_snapshot(),
    )

    repository.save(run)
    loaded = repository.get("run-001")

    assert loaded == run
    assert loaded.cycle_id == "cycle-001"
    assert hasattr(loaded, "pass_count") is False
    assert hasattr(loaded, "fail_count") is False
    assert hasattr(loaded, "summary") is False


def test_run_repository_separates_cycles_when_listing_runs():
    repository = InMemoryTestRunRepository()
    run_a = TestRun(
        run_id="run-A",
        cycle_id="cycle-A",
        run_name="A",
        cycle_snapshot_entries=_snapshot(),
    )
    run_b = TestRun(
        run_id="run-B",
        cycle_id="cycle-B",
        run_name="B",
        cycle_snapshot_entries=_snapshot(),
    )
    repository.save(run_a)
    repository.save(run_b)

    assert repository.list_by_cycle_id("cycle-A") == (run_a,)
    assert repository.list_by_cycle_id("cycle-B") == (run_b,)


def test_run_repository_get_unknown_run_raises_key_error():
    repository = InMemoryTestRunRepository()

    with pytest.raises(KeyError, match="Unknown run_id"):
        repository.get("run-missing")
