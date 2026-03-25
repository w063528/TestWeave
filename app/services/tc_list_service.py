from collections.abc import Iterable

from app.models.extracted_testcase import ExtractedTestCase
from app.models.extracted_testsuite import ExtractedTestSuite
from app.models.tc_list_entry import TCListEntry


def generate_tc_list_entries(
    extracted_suites: Iterable[ExtractedTestSuite],
    extracted_testcases: Iterable[ExtractedTestCase],
) -> list[TCListEntry]:
    suite_name_by_id = {suite.suite_id: suite.suite_name for suite in extracted_suites}
    tc_list_entries: list[TCListEntry] = []

    for testcase in extracted_testcases:
        suite_name = suite_name_by_id.get(testcase.suite_id)
        if suite_name is None:
            raise ValueError(
                f"Missing ExtractedTestSuite for testcase_id={testcase.testcase_id}, "
                f"suite_id={testcase.suite_id}"
            )

        tc_list_entries.append(
            TCListEntry(
                suite_id=testcase.suite_id,
                suite_name=suite_name,
                testcase_id=testcase.testcase_id,
                testcase_name=testcase.testcase_name,
            )
        )

    return tc_list_entries
