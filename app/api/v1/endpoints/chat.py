from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.chat import ChatMessageCreate, ChatResponse
from app.db.database import get_db

router = APIRouter()

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatMessageCreate,
    db: Session = Depends(get_db)
):
    print(f"📨 사용자 메시지: {request.message}")
    
    bot_reply = f"당신이 말한 '{request.message}'에 대해 답변합니다."
    
    return ChatResponse(message=bot_reply)


@router.get("/history")
async def get_chat_history(db: Session = Depends(get_db)):
    return {"messages": [], "total": 0}
