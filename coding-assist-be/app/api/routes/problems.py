from fastapi import APIRouter, HTTPException
from fastapi import Query

from app.problems.models import Problem, ProblemSummary
from app.problems.repository import get_problem, list_problem_summaries

router = APIRouter(prefix="/problems", tags=["problems"])


@router.get("", response_model=list[ProblemSummary])
def list_problems(
    difficulty: str | None = Query(default=None),
    topic: str | None = Query(default=None),
    q: str | None = Query(default=None),
) -> list[ProblemSummary]:
    problems = list_problem_summaries()
    if difficulty:
        problems = [item for item in problems if item.difficulty == difficulty]
    if topic:
        lowered_topic = topic.strip().lower()
        problems = [
            item
            for item in problems
            if any(existing.lower() == lowered_topic for existing in item.topics)
        ]
    if q:
        lowered_query = q.strip().lower()
        problems = [item for item in problems if lowered_query in item.title.lower()]
    return problems


@router.get("/{problem_id}", response_model=Problem)
def problem_details(problem_id: str) -> Problem:
    problem = get_problem(problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem
