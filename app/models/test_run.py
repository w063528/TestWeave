from dataclasses import dataclass

from app.models.tc_list_entry import TCListEntry


@dataclass(frozen=True, slots=True)
class TestRun:
    __test__ = False
    run_id: str
    cycle_id: str
    run_name: str
    cycle_snapshot_entries: tuple[TCListEntry, ...]
    pr_url: str = ""
    commit_sha: str = ""
    diff_snapshot_id: str = ""
