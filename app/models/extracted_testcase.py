from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExtractedTestCase:
    testcase_id: str
    testcase_name: str
    suite_id: str
    source_file_path: str
