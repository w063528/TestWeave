from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExtractedTestSuite:
    suite_id: str
    suite_name: str
    source_file_path: str
