from uuid import uuid4

from app.models.test_result import ALLOWED_TEST_RESULT_STATUSES, TestResult

_test_result_store: dict[str, TestResult] = {}


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
        result_id=f"result-{uuid4()}",
        run_id=run_id,
        testcase_id=testcase_id,
        status=status,
        notes=notes,
    )


def save_test_result(test_result: TestResult) -> None:
    _test_result_store[test_result.result_id] = test_result


def get_test_result(result_id: str) -> TestResult | None:
    return _test_result_store.get(result_id)


def list_test_results() -> tuple[TestResult, ...]:
    return tuple(_test_result_store.values())


def clear_test_result_store() -> None:
    _test_result_store.clear()
