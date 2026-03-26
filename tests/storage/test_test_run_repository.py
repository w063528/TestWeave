from app.models.tc_list_entry import TCListEntry
from app.models.test_run import TestRun
from app.storage.test_run_repository import InMemoryTestRunRepository


def test_save_then_load_test_run_preserves_entity_integrity():
    repository = InMemoryTestRunRepository()
    entity = TestRun(
        run_id="run-001",
        cycle_id="cycle-001",
        run_name="Smoke Run 1",
        cycle_snapshot_entries=(
            TCListEntry(
                suite_id="suite-auth",
                suite_name="Auth",
                testcase_id="TC-001",
                testcase_name="User logs in",
            ),
        ),
    )

    repository.save(entity)
    loaded = repository.load("run-001")

    assert loaded == entity
