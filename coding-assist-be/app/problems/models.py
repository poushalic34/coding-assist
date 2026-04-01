from typing import Any, Literal

from pydantic import BaseModel, Field


Verdict = Literal["accepted", "wrong_answer", "runtime_error", "timeout"]
FailureCategory = Literal["none", "logic_error", "runtime_error", "timeout"]
HintSource = Literal["model", "fallback"]
HintLevel = Literal["diagnosis", "next_step", "complexity"]
CoachingMode = Literal["strict", "balanced", "fast-track"]


class TestCase(BaseModel):
    input: str
    expected_output: str


class Problem(BaseModel):
    id: str
    title: str
    difficulty: Literal["easy", "medium", "hard"]
    description: str
    topics: list[str] = []
    constraints: list[str] = []
    learning_objectives: list[str] = []
    starter_code: str
    function_name: str
    sample_tests: list[TestCase]
    hidden_tests: list[TestCase]


class ProblemSummary(BaseModel):
    id: str
    title: str
    difficulty: Literal["easy", "medium", "hard"]
    topics: list[str] = []


class RunSubmissionRequest(BaseModel):
    problem_id: str
    code: str = Field(min_length=1)
    custom_input: str | None = None


class FailedCaseSummary(BaseModel):
    scope: Literal["sample", "hidden", "custom"]
    message: str
    input: str | None = None
    expected_output: str | None = None
    actual_output: str | None = None


class SampleTestResult(BaseModel):
    index: int
    passed: bool
    input: str
    expected_output: str
    actual_output: str


class RunSubmissionResponse(BaseModel):
    verdict: Verdict
    failure_category: FailureCategory = "none"
    passed_count: int
    total_count: int
    runtime_ms: int
    hidden_passed_count: int = 0
    hidden_total_count: int = 0
    sample_results: list[SampleTestResult] = []
    next_recommendation: str | None = None
    failed_case_summary: FailedCaseSummary | None = None
    error: str | None = None


class ExecutionResult(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    runtime_ms: int


class BedrockHintRequest(BaseModel):
    problem_id: str
    code: str
    latest_verdict: str
    user_question: str
    attempt_number: int | None = None
    latest_failure_summary: str | None = None
    coaching_mode: CoachingMode = "balanced"
    focus_area: str | None = None
    conversation_id: str | None = None
    requested_hint_level: HintLevel | None = None


class BedrockHintResponse(BaseModel):
    source: HintSource
    hint_level: HintLevel
    next_hint_level: HintLevel
    confidence: float = Field(ge=0, le=1)
    conversation_id: str
    guided_hint: str
    strategy: str
    complexity_suggestion: str
