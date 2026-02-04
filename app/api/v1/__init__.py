from fastapi import APIRouter
from app.api.v1.endpoints import agent, sessions, feedback

router = APIRouter()

# 라우터 등록
router.include_router(sessions.router)  # /api/v1/sessions
router.include_router(agent.router)     # /api/v1/agent
router.include_router(feedback.router)  # /api/v1/feedback

__all__ = ["router"]
