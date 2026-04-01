import re


UNSAFE_PATTERNS = [
    r"\bignore\b.*\binstruction",
    r"\breveal\b.*\bhidden\b.*\btest",
    r"\bprint\b.*\banswer\b.*\bonly\b",
    r"\bjust give\b.*\bfinal code\b",
]


def is_policy_bypass_attempt(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in UNSAFE_PATTERNS)
