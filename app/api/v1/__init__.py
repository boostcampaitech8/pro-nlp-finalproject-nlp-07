from fastapi import APIRouter
from app.api.v1.endpoints import chat, agent  # ← agent 추가

router = APIRouter()

router.include_router(chat.router, prefix="/chat", tags=["chat"])
router.include_router(agent.router, prefix="/agent", tags=["agent"])
