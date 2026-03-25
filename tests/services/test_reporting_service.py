from dataclasses import fields

from app.models.test_report import TestReport
from app.models.test_result import TestResult
from app.services.reporting_service import generate_test_report
from app.services.test_result_service import create_test_result


def test_generate_test_report_aggregates_passed_failed_and_skipped_counts():
    results = [
        create_test_result("run-1", "TC-001", "Pass"),
        create_test_result("run-1", "TC-002", "Fail"),
        create_test_result("run-1", "TC-003", "Not Run"),
        create_test_result("run-1", "TC-004", "Blocked"),
    ]

    report = generate_test_report(results)

    assert report == TestReport(
        total=4,
        passed=1,
        failed=1,
        skipped=2,
    )


def test_generate_test_report_supports_skipped_status_string_if_present():
    results = [
        TestResult(
            result_id="result-1",
            run_id="run-1",
            testcase_id="TC-001",
            status="Skipped",
            notes="",
        )
    ]

    report = generate_test_report(results)

    assert report.total == 1
    assert report.passed == 0
    assert report.failed == 0
    assert report.skipped == 1


def test_generate_test_report_handles_empty_result_list():
    report = generate_test_report([])

    assert report == TestReport(total=0, passed=0, failed=0, skipped=0)


def test_test_report_model_has_only_phase_8_reporting_fields():
    assert [field.name for field in fields(TestReport)] == [
        "total",
        "passed",
        "failed",
        "skipped",
    ]

