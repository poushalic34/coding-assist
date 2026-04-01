from collections import deque
from threading import Lock
from typing import Any

from app.db.connection import db_cursor, ensure_schema, is_db_configured

_LOCAL_MEMORY_LIMIT = 20
_local_memory: dict[tuple[str, str], deque[dict[str, Any]]] = {}
_local_lock = Lock()


def load_recent_turns(
    *, conversation_id: str, problem_id: str, limit: int = 5
) -> list[dict[str, Any]]:
    if is_db_configured():
        try:
            ensure_schema()
            with db_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT question, hint_level, guided_hint, strategy, complexity_suggestion, latest_verdict
                    FROM assistant_history
                    WHERE conversation_id = %s AND problem_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (conversation_id, problem_id, limit),
                )
                rows = cursor.fetchall()
            rows.reverse()
            return [dict(row) for row in rows]
        except Exception:
            # Graceful fallback keeps local/dev tests independent from cloud DB connectivity.
            pass

    key = (conversation_id, problem_id)
    with _local_lock:
        turns = list(_local_memory.get(key, deque()))
    return turns[-limit:]


def save_turn(
    *,
    conversation_id: str,
    problem_id: str,
    question: str,
    latest_verdict: str,
    coaching_mode: str,
    focus_area: str | None,
    hint_level: str,
    guided_hint: str,
    strategy: str,
    complexity_suggestion: str,
) -> None:
    if is_db_configured():
        try:
            ensure_schema()
            with db_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO assistant_history (
                        conversation_id, problem_id, question, latest_verdict, coaching_mode,
                        focus_area, hint_level, guided_hint, strategy, complexity_suggestion
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        conversation_id,
                        problem_id,
                        question,
                        latest_verdict,
                        coaching_mode,
                        focus_area,
                        hint_level,
                        guided_hint,
                        strategy,
                        complexity_suggestion,
                    ),
                )
            return
        except Exception:
            # If DB write fails, keep history in process memory.
            pass

    key = (conversation_id, problem_id)
    record = {
        "question": question,
        "latest_verdict": latest_verdict,
        "hint_level": hint_level,
        "guided_hint": guided_hint,
        "strategy": strategy,
        "complexity_suggestion": complexity_suggestion,
    }
    with _local_lock:
        turns = _local_memory.setdefault(key, deque(maxlen=_LOCAL_MEMORY_LIMIT))
        turns.append(record)
