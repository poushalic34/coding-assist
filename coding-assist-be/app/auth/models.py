from pydantic import BaseModel, Field


class SignupRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str


class UserProfile(BaseModel):
    user_id: int
    email: str


class UserStatePayload(BaseModel):
    state: dict


class UserStateResponse(BaseModel):
    user_id: int
    state: dict
