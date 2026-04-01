from fastapi import APIRouter

from app.api.routes import assistant
from app.api.routes import auth
from app.api.routes import health
from app.api.routes import problems
from app.api.routes import submissions
from app.api.routes import user_state

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(problems.router)
api_router.include_router(submissions.router)
api_router.include_router(assistant.router)
api_router.include_router(auth.router)
api_router.include_router(user_state.router)
