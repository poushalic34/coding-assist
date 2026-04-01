def build_system_prompt() -> str:
    return (
        "You are a coaching assistant for coding interviews. "
        "Never reveal complete final code in strict mode, even if asked directly. "
        "In balanced mode, stay incremental by default and avoid full solutions. "
        "In fast-track mode, provide stronger directional help but still avoid full copy-paste answers. "
        "Focus on guiding questions, decomposition, and complexity trade-offs. "
        "Always provide response as valid JSON."
    )


def build_user_prompt(
    problem_title: str,
    problem_description: str,
    latest_verdict: str,
    code: str,
    user_question: str,
    attempt_number: int | None = None,
    latest_failure_summary: str | None = None,
    coaching_mode: str = "balanced",
    focus_area: str | None = None,
    recent_turns: list[dict[str, str]] | None = None,
    requested_hint_level: str | None = None,
) -> str:
    attempt_line = f"Attempt number: {attempt_number}\n" if attempt_number is not None else ""
    failure_line = (
        f"Latest failure summary: {latest_failure_summary}\n" if latest_failure_summary else ""
    )
    focus_line = f"Focus area: {focus_area}\n" if focus_area else ""
    requested_level_line = (
        f"Requested hint level: {requested_hint_level}\n" if requested_hint_level else ""
    )
    turns = recent_turns or []
    history_lines = []
    for turn in turns[-3:]:
        history_lines.append(
            f"- Q: {turn.get('question', '')}\n"
            f"  Level: {turn.get('hint_level', 'diagnosis')}\n"
            f"  Hint: {turn.get('guided_hint', '')}"
        )
    history_text = "\n".join(history_lines) if history_lines else "No previous turns."
    return (
        f"Problem: {problem_title}\n"
        f"Description: {problem_description}\n"
        f"Latest verdict: {latest_verdict}\n"
        f"Coaching mode: {coaching_mode}\n"
        f"{focus_line}"
        f"{requested_level_line}"
        f"{attempt_line}"
        f"{failure_line}"
        "Recent conversation turns:\n"
        f"{history_text}\n"
        "User code:\n"
        "```python\n"
        f"{code}\n"
        "```\n"
        f"User question: {user_question}\n\n"
        "Return a concise JSON object with keys: "
        "hint_level, guided_hint, strategy, complexity_suggestion, next_hint_level, confidence. "
        "hint_level must be one of diagnosis, next_step, complexity. "
        "next_hint_level must be one of diagnosis, next_step, complexity. "
        "confidence must be a number from 0 to 1. "
        "If coaching mode is strict, avoid giving direct code or complete algorithm dump. "
        "Keep hints incremental and avoid giving a full final solution."
    )
