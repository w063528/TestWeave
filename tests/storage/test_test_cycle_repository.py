from app.models.tc_list_entry import TCListEntry
from app.models.test_cycle import TestCycle
from app.storage.test_cycle_repository import InMemoryTestCycleRepository


def test_cycle_repository_save_and_load_preserves_cycle_integrity():
    repository = InMemoryTestCycleRepository()
    cycle = TestCycle(
        cycle_id="cycle-001",
        cycle_name="Smoke Cycle",
        tc_list_entries=(
            TCListEntry(
                suite_id="suite-001",
                suite_name="Auth",
                testcase_id="TC-001",
                testcase_name="Login works",
            ),
        ),
    )

    repository.save(cycle)
    loaded = repository.get("cycle-001")

    assert loaded == cycle
    assert loaded is not cycle
    assert loaded is not None
    assert loaded.cycle_id == "cycle-001"
    assert hasattr(loaded, "results") is False


def test_cycle_repository_stores_only_cycles():
    repository = InMemoryTestCycleRepository()
    first = TestCycle(cycle_id="cycle-001", cycle_name="Cycle A", tc_list_entries=())
    second = TestCycle(cycle_id="cycle-002", cycle_name="Cycle B", tc_list_entries=())

    repository.save(first)
    repository.save(second)

    all_cycles = repository.list_all()
    assert {cycle.cycle_id for cycle in all_cycles} == {"cycle-001", "cycle-002"}
