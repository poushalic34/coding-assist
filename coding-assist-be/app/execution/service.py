from app.problems.models import (
    ExecutionResult,
    FailedCaseSummary,
    Problem,
    RunSubmissionResponse,
    SampleTestResult,
)


def normalize_output(value: str) -> str:
    return value.strip().replace("\r\n", "\n")


def evaluate_submission(problem: Problem, result_by_input: dict[str, ExecutionResult]) -> RunSubmissionResponse:
    sample_results: list[SampleTestResult] = []
    aggregate_runtime = 0
    sample_passed_count = 0
    hidden_passed_count = 0
    hidden_total_count = len(problem.hidden_tests)
    total_count = len(problem.sample_tests) + hidden_total_count

    for idx, sample_test in enumerate(problem.sample_tests, start=1):
        execution = result_by_input[sample_test.input]
        aggregate_runtime += execution.runtime_ms
        expected = normalize_output(sample_test.expected_output)
        actual = normalize_output(execution.stdout)
        passed = (
            not execution.timed_out and execution.exit_code == 0 and actual == expected
        )
        if passed:
            sample_passed_count += 1
        sample_results.append(
            SampleTestResult(
                index=idx,
                passed=passed,
                input=sample_test.input,
                expected_output=expected,
                actual_output=actual,
            )
        )

        if execution.timed_out:
            return RunSubmissionResponse(
                verdict="timeout",
                failure_category="timeout",
                passed_count=sample_passed_count,
                total_count=total_count,
                runtime_ms=aggregate_runtime,
                hidden_passed_count=0,
                hidden_total_count=hidden_total_count,
                sample_results=sample_results,
                failed_case_summary=FailedCaseSummary(
                    scope="sample",
                    message="Your program timed out on a sample test.",
                    input=sample_test.input,
                    expected_output=expected,
                    actual_output=actual,
                ),
                error="Execution timed out",
                next_recommendation="Review loops and reduce unnecessary repeated work.",
            )
        if execution.exit_code != 0:
            error_message = execution.stderr.strip() or "Runtime error"
            return RunSubmissionResponse(
                verdict="runtime_error",
                failure_category="runtime_error",
                passed_count=sample_passed_count,
                total_count=total_count,
                runtime_ms=aggregate_runtime,
                hidden_passed_count=0,
                hidden_total_count=hidden_total_count,
                sample_results=sample_results,
                failed_case_summary=FailedCaseSummary(
                    scope="sample",
                    message="Your code raised a runtime error on a sample test.",
                    input=sample_test.input,
                    expected_output=expected,
                    actual_output=actual,
                ),
                error=error_message,
                next_recommendation="Re-run with custom input and check edge-case handling.",
            )
        if actual != expected:
            return RunSubmissionResponse(
                verdict="wrong_answer",
                failure_category="logic_error",
                passed_count=sample_passed_count,
                total_count=total_count,
                runtime_ms=aggregate_runtime,
                hidden_passed_count=0,
                hidden_total_count=hidden_total_count,
                sample_results=sample_results,
                failed_case_summary=FailedCaseSummary(
                    scope="sample",
                    message="Output mismatch on a sample test.",
                    input=sample_test.input,
                    expected_output=expected,
                    actual_output=actual,
                ),
                next_recommendation="Compare your output format and intermediate logic step-by-step.",
            )

    for hidden_test in problem.hidden_tests:
        execution = result_by_input[hidden_test.input]
        aggregate_runtime += execution.runtime_ms
        expected = normalize_output(hidden_test.expected_output)
        actual = normalize_output(execution.stdout)

        if execution.timed_out:
            return RunSubmissionResponse(
                verdict="timeout",
                failure_category="timeout",
                passed_count=sample_passed_count + hidden_passed_count,
                total_count=total_count,
                runtime_ms=aggregate_runtime,
                hidden_passed_count=hidden_passed_count,
                hidden_total_count=hidden_total_count,
                sample_results=sample_results,
                failed_case_summary=FailedCaseSummary(
                    scope="hidden",
                    message="Timed out on a hidden test case.",
                ),
                error="Execution timed out",
                next_recommendation="Try reducing time complexity for larger inputs.",
            )
        if execution.exit_code != 0:
            return RunSubmissionResponse(
                verdict="runtime_error",
                failure_category="runtime_error",
                passed_count=sample_passed_count + hidden_passed_count,
                total_count=total_count,
                runtime_ms=aggregate_runtime,
                hidden_passed_count=hidden_passed_count,
                hidden_total_count=hidden_total_count,
                sample_results=sample_results,
                failed_case_summary=FailedCaseSummary(
                    scope="hidden",
                    message="Runtime error on a hidden test case.",
                ),
                error=execution.stderr.strip() or "Runtime error",
                next_recommendation="Guard assumptions and validate boundary conditions.",
            )
        if actual != expected:
            return RunSubmissionResponse(
                verdict="wrong_answer",
                failure_category="logic_error",
                passed_count=sample_passed_count + hidden_passed_count,
                total_count=total_count,
                runtime_ms=aggregate_runtime,
                hidden_passed_count=hidden_passed_count,
                hidden_total_count=hidden_total_count,
                sample_results=sample_results,
                failed_case_summary=FailedCaseSummary(
                    scope="hidden",
                    message="Wrong answer on a hidden test case.",
                ),
                next_recommendation="Test additional edge cases and revisit your core invariant.",
            )
        hidden_passed_count += 1

    return RunSubmissionResponse(
        verdict="accepted",
        failure_category="none",
        passed_count=total_count,
        total_count=total_count,
        runtime_ms=aggregate_runtime,
        hidden_passed_count=hidden_passed_count,
        hidden_total_count=hidden_total_count,
        sample_results=sample_results,
        next_recommendation="Great work. Try improving readability or reducing memory use further.",
    )


def evaluate_custom_run(execution: ExecutionResult) -> RunSubmissionResponse:
    if execution.timed_out:
        return RunSubmissionResponse(
            verdict="timeout",
            failure_category="timeout",
            passed_count=0,
            total_count=0,
            runtime_ms=execution.runtime_ms,
            failed_case_summary=FailedCaseSummary(
                scope="custom",
                message="Timed out on your custom input.",
            ),
            error="Execution timed out",
            next_recommendation="Reduce complexity before running against full tests.",
        )
    if execution.exit_code != 0:
        return RunSubmissionResponse(
            verdict="runtime_error",
            failure_category="runtime_error",
            passed_count=0,
            total_count=0,
            runtime_ms=execution.runtime_ms,
            failed_case_summary=FailedCaseSummary(
                scope="custom",
                message="Runtime error on your custom input.",
                actual_output=normalize_output(execution.stdout),
            ),
            error=execution.stderr.strip() or "Runtime error",
            next_recommendation="Fix runtime issues, then run full problem tests.",
        )
    return RunSubmissionResponse(
        verdict="accepted",
        failure_category="none",
        passed_count=0,
        total_count=0,
        runtime_ms=execution.runtime_ms,
        failed_case_summary=FailedCaseSummary(
            scope="custom",
            message="Custom input executed successfully.",
            actual_output=normalize_output(execution.stdout),
        ),
        next_recommendation="Use Submit mode to validate against sample and hidden tests.",
    )
