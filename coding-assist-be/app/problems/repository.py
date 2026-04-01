import json
from functools import lru_cache
from pathlib import Path

from app.problems.models import Problem, ProblemSummary


def _seed_path() -> Path:
    return Path(__file__).with_name("seed_problems.json")


@lru_cache
def load_problems() -> dict[str, Problem]:
    raw = json.loads(_seed_path().read_text(encoding="utf-8"))
    problems = [Problem.model_validate(item) for item in raw]
    return {problem.id: problem for problem in problems}


def list_problem_summaries() -> list[ProblemSummary]:
    summaries: list[ProblemSummary] = []
    for problem in load_problems().values():
        summaries.append(
            ProblemSummary(
                id=problem.id,
                title=problem.title,
                difficulty=problem.difficulty,
                topics=problem.topics,
            )
        )
    return summaries


def get_problem(problem_id: str) -> Problem | None:
    return load_problems().get(problem_id)
