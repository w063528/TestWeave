from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TCListEntry:
    suite_id: str
    suite_name: str
    testcase_id: str
    testcase_name: str
