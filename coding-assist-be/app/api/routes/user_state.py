import json

from fastapi import APIRouter, Depends

from app.auth.models import UserStatePayload, UserStateResponse
from app.auth.security import get_current_user
from app.db.connection import db_cursor, ensure_schema

router = APIRouter(prefix="/user-state", tags=["user-state"])


@router.get("", response_model=UserStateResponse)
def get_user_state(current_user: dict = Depends(get_current_user)) -> UserStateResponse:
    ensure_schema()
    user_id = current_user["user_id"]
    with db_cursor() as cursor:
        cursor.execute("SELECT state FROM user_state WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
    if not row:
        return UserStateResponse(user_id=user_id, state={})
    state_value = row["state"]
    if isinstance(state_value, str):
        state_value = json.loads(state_value)
    return UserStateResponse(user_id=user_id, state=state_value or {})


@router.put("", response_model=UserStateResponse)
def put_user_state(
    payload: UserStatePayload,
    current_user: dict = Depends(get_current_user),
) -> UserStateResponse:
    ensure_schema()
    user_id = current_user["user_id"]
    with db_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO user_state (user_id, state, updated_at)
            VALUES (%s, %s::jsonb, NOW())
            ON CONFLICT (user_id)
            DO UPDATE SET state = EXCLUDED.state, updated_at = NOW()
            """,
            (user_id, json.dumps(payload.state)),
        )
    return UserStateResponse(user_id=user_id, state=payload.state)
