from fastapi import APIRouter
from app.api.v1.endpoints import agent, sessions, feedback, users

router = APIRouter()

# 라우터 등록
router.include_router(sessions.router)  # /api/v1/sessions
router.include_router(agent.router)     # /api/v1/agent
router.include_router(feedback.router)  # /api/v1/feedback
router.include_router(users.router)

__all__ = ["router"]
