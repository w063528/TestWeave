import pytest

from app.models.tc_list_entry import TCListEntry
from app.models.test_cycle import TestCycle
from app.storage.test_cycle_repository import InMemoryTestCycleRepository


def _entry(testcase_id: str) -> TCListEntry:
    return TCListEntry(
        suite_id="suite-auth-001",
        suite_name="Auth",
        testcase_id=testcase_id,
        testcase_name=f"case-{testcase_id}",
    )


def test_cycle_repository_save_and_load_integrity():
    repository = InMemoryTestCycleRepository()
    cycle = TestCycle(
        cycle_id="cycle-001",
        cycle_name="Smoke",
        tc_list_entries=(_entry("TC-001"), _entry("TC-002")),
    )

    repository.save(cycle)
    loaded = repository.get("cycle-001")

    assert loaded == cycle
    assert loaded.cycle_id == "cycle-001"
    assert hasattr(loaded, "results") is False
    assert hasattr(loaded, "summary") is False


def test_cycle_repository_identity_preserved_across_list_and_get():
    repository = InMemoryTestCycleRepository()
    cycle = TestCycle(
        cycle_id="cycle-identity",
        cycle_name="Identity",
        tc_list_entries=(_entry("TC-010"),),
    )

    repository.save(cycle)

    assert repository.list_all() == (cycle,)
    assert repository.get("cycle-identity").cycle_id == cycle.cycle_id


def test_cycle_repository_get_unknown_cycle_raises_key_error():
    repository = InMemoryTestCycleRepository()

    with pytest.raises(KeyError, match="Unknown cycle_id"):
        repository.get("cycle-missing")
