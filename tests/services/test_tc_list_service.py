from dataclasses import fields

import pytest

from app.models.extracted_testcase import ExtractedTestCase
from app.models.extracted_testsuite import ExtractedTestSuite
from app.models.tc_list_entry import TCListEntry
from app.services.tc_list_service import generate_tc_list_entries


def test_generate_tc_list_entries_transforms_extracted_models():
    suites = [
        ExtractedTestSuite(
            suite_id="suite-auth-001",
            suite_name="Auth Flow",
            source_file_path="specs/auth.feature",
        ),
        ExtractedTestSuite(
            suite_id="suite-billing-002",
            suite_name="Billing Flow",
            source_file_path="specs/billing.md",
        ),
    ]
    testcases = [
        ExtractedTestCase(
            testcase_id="TC-001",
            testcase_name="User logs in",
            suite_id="suite-auth-001",
            source_file_path="specs/auth.feature",
        ),
        ExtractedTestCase(
            testcase_id="TC-101",
            testcase_name="User updates card",
            suite_id="suite-billing-002",
            source_file_path="specs/billing.md",
        ),
    ]

    entries = generate_tc_list_entries(suites, testcases)

    assert entries == [
        TCListEntry(
            suite_id="suite-auth-001",
            suite_name="Auth Flow",
            testcase_id="TC-001",
            testcase_name="User logs in",
        ),
        TCListEntry(
            suite_id="suite-billing-002",
            suite_name="Billing Flow",
            testcase_id="TC-101",
            testcase_name="User updates card",
        ),
    ]


def test_generate_tc_list_entries_contains_only_definition_side_fields():
    suites = [
        ExtractedTestSuite(
            suite_id="suite-001",
            suite_name="Profile",
            source_file_path="specs/profile.md",
        )
    ]
    testcases = [
        ExtractedTestCase(
            testcase_id="TC-200",
            testcase_name="Open profile page",
            suite_id="suite-001",
            source_file_path="specs/profile.md",
        )
    ]

    entries = generate_tc_list_entries(suites, testcases)

    assert [field.name for field in fields(TCListEntry)] == [
        "suite_id",
        "suite_name",
        "testcase_id",
        "testcase_name",
    ]
    assert hasattr(entries[0], "status") is False
    assert hasattr(entries[0], "run_id") is False
    assert hasattr(entries[0], "notes") is False


def test_generate_tc_list_entries_raises_when_suite_is_missing():
    suites = []
    testcases = [
        ExtractedTestCase(
            testcase_id="TC-404",
            testcase_name="Missing suite mapping",
            suite_id="suite-missing",
            source_file_path="specs/missing.md",
        )
    ]

    with pytest.raises(ValueError, match="Missing ExtractedTestSuite"):
        generate_tc_list_entries(suites, testcases)
