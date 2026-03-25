from app.models.test_report import TestReport
from app.models.test_result import TestResult


def generate_test_report(results: list[TestResult] | tuple[TestResult, ...]) -> TestReport:
    passed = 0
    failed = 0
    skipped = 0

    for result in results:
        if result.status == "Pass":
            passed += 1
        elif result.status == "Fail":
            failed += 1
        else:
            skipped += 1

    return TestReport(
        total=len(results),
        passed=passed,
        failed=failed,
        skipped=skipped,
    )
