from app.models.tc_list_entry import TCListEntry
from app.models.test_cycle import TestCycle
from app.storage.test_cycle_repository import InMemoryTestCycleRepository


def test_save_then_load_test_cycle_preserves_entity_integrity():
    repository = InMemoryTestCycleRepository()
    entity = TestCycle(
        cycle_id="cycle-001",
        cycle_name="Smoke Cycle",
        tc_list_entries=(
            TCListEntry(
                suite_id="suite-auth",
                suite_name="Auth",
                testcase_id="TC-001",
                testcase_name="User logs in",
            ),
        ),
    )

    repository.save(entity)
    loaded = repository.load("cycle-001")

    assert loaded == entity
