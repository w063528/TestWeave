from app.models.tc_list_entry import TCListEntry
from app.models.test_cycle import TestCycle
from app.storage.test_cycle_repository import TestCycleRepository


def test_save_and_load_test_cycle_preserves_all_fields(tmp_path):
    repository = TestCycleRepository(tmp_path / "test_cycles.json")
    cycle = TestCycle(
        cycle_id="cycle-001",
        cycle_name="Smoke Cycle",
        tc_list_entries=(
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

    repository.save(cycle)
    loaded = repository.load("cycle-001")

    assert loaded == cycle
