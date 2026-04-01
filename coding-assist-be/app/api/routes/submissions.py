from fastapi import APIRouter, HTTPException

from app.execution.runner import run_python_code
from app.execution.service import evaluate_custom_run, evaluate_submission
from app.problems.models import RunSubmissionRequest, RunSubmissionResponse
from app.problems.repository import get_problem

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("/run", response_model=RunSubmissionResponse)
def run_submission(payload: RunSubmissionRequest) -> RunSubmissionResponse:
    problem = get_problem(payload.problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    if payload.custom_input is not None:
        execution = run_python_code(payload.code, payload.custom_input)
        return evaluate_custom_run(execution)

    result_by_input = {}
    for test in [*problem.sample_tests, *problem.hidden_tests]:
        result_by_input[test.input] = run_python_code(payload.code, test.input)

    return evaluate_submission(problem, result_by_input)
