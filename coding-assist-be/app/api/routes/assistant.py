from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.agents.bedrock_client import BedrockClient
from app.agents.memory import load_recent_turns, save_turn
from app.agents.prompts import build_system_prompt, build_user_prompt
from app.agents.safety import is_policy_bypass_attempt
from app.problems.models import BedrockHintRequest, BedrockHintResponse
from app.problems.repository import get_problem

router = APIRouter(prefix="/assistant", tags=["assistant"])


def _next_hint_level(current_level: str) -> str:
    if current_level == "diagnosis":
        return "next_step"
    if current_level == "next_step":
        return "complexity"
    return "complexity"


def _strict_spoiler_attempt(question: str) -> bool:
    lowered = question.lower()
    blocked_phrases = (
        "full solution",
        "complete code",
        "give me code",
        "final answer",
        "just the answer",
    )
    return any(phrase in lowered for phrase in blocked_phrases)


def fallback_hint(
    *,
    latest_verdict: str | None = None,
    coaching_mode: str = "balanced",
    conversation_id: str,
) -> BedrockHintResponse:
    confidence = 0.55
    if latest_verdict == "runtime_error":
        return BedrockHintResponse(
            source="fallback",
            hint_level="diagnosis",
            next_hint_level="next_step",
            confidence=confidence,
            conversation_id=conversation_id,
            guided_hint="Focus on where your code may raise an exception for empty or edge-case input.",
            strategy="Add small guard clauses and print intermediate values locally to isolate failing branches.",
            complexity_suggestion="Stabilize correctness first, then optimize complexity.",
        )
    if latest_verdict == "wrong_answer":
        guided_hint = (
            "Compare expected vs actual for one sample and identify the first decision point where they diverge."
        )
        if coaching_mode == "strict":
            guided_hint = (
                "Write down the invariant for your loop and validate it on one passing and one failing sample."
            )
        return BedrockHintResponse(
            source="fallback",
            hint_level="next_step",
            next_hint_level="complexity",
            confidence=confidence,
            conversation_id=conversation_id,
            guided_hint=guided_hint,
            strategy="Write down your invariant for each loop iteration and verify it holds for edge cases.",
            complexity_suggestion="After correctness, target O(n) when hash lookup is possible.",
        )
    return BedrockHintResponse(
        source="fallback",
        hint_level="complexity",
        next_hint_level="complexity",
        confidence=confidence,
        conversation_id=conversation_id,
        guided_hint="Start by identifying what information must be remembered while scanning the input once.",
        strategy="Try writing a brute-force solution first, then replace repeated lookups with a hash map.",
        complexity_suggestion="Aim for O(n) time and O(n) space if this is a pair-search style problem.",
    )


@router.post("/hint", response_model=BedrockHintResponse)
def get_hint(payload: BedrockHintRequest) -> BedrockHintResponse:
    problem = get_problem(payload.problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    conversation_id = payload.conversation_id or str(uuid4())
    recent_turns = load_recent_turns(
        conversation_id=conversation_id,
        problem_id=payload.problem_id,
        limit=5,
    )

    if is_policy_bypass_attempt(payload.user_question):
        return BedrockHintResponse(
            source="fallback",
            hint_level="diagnosis",
            next_hint_level="next_step",
            confidence=0.5,
            conversation_id=conversation_id,
            guided_hint="I can help with guided steps, but I can't bypass solving. Start by explaining your current approach.",
            strategy="Share your current logic and I will point out one improvement at a time.",
            complexity_suggestion="State the current time and space complexity of your approach first.",
        )
    if payload.coaching_mode == "strict" and _strict_spoiler_attempt(payload.user_question):
        response = BedrockHintResponse(
            source="fallback",
            hint_level="diagnosis",
            next_hint_level="next_step",
            confidence=0.62,
            conversation_id=conversation_id,
            guided_hint="In strict coaching mode, I cannot provide full code. Start with the core invariant your solution must maintain.",
            strategy="Break the task into input parsing, state update, and termination conditions before coding.",
            complexity_suggestion="After the invariant is clear, choose data structures to hit the target complexity.",
        )
        save_turn(
            conversation_id=conversation_id,
            problem_id=payload.problem_id,
            question=payload.user_question,
            latest_verdict=payload.latest_verdict,
            coaching_mode=payload.coaching_mode,
            focus_area=payload.focus_area,
            hint_level=response.hint_level,
            guided_hint=response.guided_hint,
            strategy=response.strategy,
            complexity_suggestion=response.complexity_suggestion,
        )
        return response

    try:
        client = BedrockClient()
        result = client.generate_hint(
            system_prompt=build_system_prompt(),
            user_prompt=build_user_prompt(
                problem_title=problem.title,
                problem_description=problem.description,
                latest_verdict=payload.latest_verdict,
                code=payload.code,
                user_question=payload.user_question,
                attempt_number=payload.attempt_number,
                latest_failure_summary=payload.latest_failure_summary,
                coaching_mode=payload.coaching_mode,
                focus_area=payload.focus_area,
                recent_turns=recent_turns,
                requested_hint_level=payload.requested_hint_level,
            ),
        )
        hint_level = str(result.get("hint_level", "diagnosis"))
        response = BedrockHintResponse(
            source="model",
            hint_level=hint_level,
            next_hint_level=str(result.get("next_hint_level", _next_hint_level(hint_level))),
            confidence=float(result.get("confidence", 0.82)),
            conversation_id=conversation_id,
            guided_hint=str(result.get("guided_hint", "")),
            strategy=str(result.get("strategy", "")),
            complexity_suggestion=str(result.get("complexity_suggestion", "")),
        )
    except Exception:
        # Deterministic fallback keeps local dev flow usable without Bedrock.
        response = fallback_hint(
            latest_verdict=payload.latest_verdict,
            coaching_mode=payload.coaching_mode,
            conversation_id=conversation_id,
        )
    save_turn(
        conversation_id=conversation_id,
        problem_id=payload.problem_id,
        question=payload.user_question,
        latest_verdict=payload.latest_verdict,
        coaching_mode=payload.coaching_mode,
        focus_area=payload.focus_area,
        hint_level=response.hint_level,
        guided_hint=response.guided_hint,
        strategy=response.strategy,
        complexity_suggestion=response.complexity_suggestion,
    )
    return response
