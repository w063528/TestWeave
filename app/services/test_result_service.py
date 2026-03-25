from app.models.test_result import ALLOWED_TEST_RESULT_STATUSES, TestResult


def create_test_result(
    run_id: str,
    testcase_id: str,
    status: str,
    notes: str = "",
) -> TestResult:
    if status not in ALLOWED_TEST_RESULT_STATUSES:
        allowed = ", ".join(ALLOWED_TEST_RESULT_STATUSES)
        raise ValueError(f"Unsupported TestResult status: {status}. Allowed: {allowed}")

    return TestResult(
        run_id=run_id,
        testcase_id=testcase_id,
        status=status,
        notes=notes,
    )
