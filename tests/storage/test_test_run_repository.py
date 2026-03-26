from app.models.tc_list_entry import TCListEntry
from app.models.test_run import TestRun
from app.storage.test_run_repository import TestRunRepository


def test_save_and_load_test_run_preserves_all_fields(tmp_path):
    repository = TestRunRepository(tmp_path / "test_runs.json")
    run = TestRun(
        run_id="run-001",
        cycle_id="cycle-001",
        run_name="Smoke Run 1",
        cycle_snapshot_entries=(
            TCListEntry(
                suite_id="suite-auth-001",
                suite_name="Auth",
                testcase_id="TC-001",
                testcase_name="Login succeeds",
            ),
            TCListEntry(
                suite_id="suite-billing-002",
                suite_name="Billing",
                testcase_id="TC-101",
                testcase_name="Update card",
            ),
        ),
    )

    repository.save(run)
    loaded = repository.load("run-001")

    assert loaded == run
