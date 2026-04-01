from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.models import AuthResponse, LoginRequest, SignupRequest, UserProfile
from app.auth.security import create_access_token, get_current_user, hash_password, verify_password
from app.db.connection import db_cursor, ensure_schema

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest) -> AuthResponse:
    ensure_schema()
    email = payload.email.strip().lower()
    with db_cursor() as cursor:
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="Email already exists")
        password_hash = hash_password(payload.password)
        cursor.execute(
            """
            INSERT INTO users (email, password_hash)
            VALUES (%s, %s)
            RETURNING id, email
            """,
            (email, password_hash),
        )
        created_user = cursor.fetchone()
    user_id = int(created_user["id"])
    token = create_access_token(user_id=user_id, email=str(created_user["email"]))
    return AuthResponse(
        access_token=token,
        user_id=user_id,
        email=str(created_user["email"]),
    )


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    ensure_schema()
    email = payload.email.strip().lower()
    with db_cursor() as cursor:
        cursor.execute(
            "SELECT id, email, password_hash FROM users WHERE email = %s",
            (email,),
        )
        user = cursor.fetchone()
    if not user or not verify_password(payload.password, str(user["password_hash"])):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    user_id = int(user["id"])
    token = create_access_token(user_id=user_id, email=str(user["email"]))
    return AuthResponse(
        access_token=token,
        user_id=user_id,
        email=str(user["email"]),
    )


@router.get("/me", response_model=UserProfile)
def me(current_user: dict = Depends(get_current_user)) -> UserProfile:
    return UserProfile(user_id=current_user["user_id"], email=current_user["email"])
