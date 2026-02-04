from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import uuid

from app.db.database import get_db
from app.models.session import ChatSession

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/generate-id")
async def generate_user_id(db: Session = Depends(get_db)):
    """
    새로운 익명 사용자 ID 생성
    
    - 중복되지 않는 anon_<UUID> 형식의 ID 생성
    - localStorage에 저장하여 사용
    
    Returns:
        user_id: 생성된 사용자 ID
    """
    max_attempts = 10
    
    for attempt in range(max_attempts):
        # UUID 생성
        new_user_id = f"anon_{uuid.uuid4()}"
        
        # 중복 확인
        existing = db.query(ChatSession).filter(
            ChatSession.user_id == new_user_id
        ).first()
        
        if not existing:
            return {
                "user_id": new_user_id,
                "message": "User ID generated successfully"
            }
    
    # 10번 시도했는데도 중복이면 (사실상 불가능)
    raise HTTPException(
        status_code=500,
        detail="Failed to generate unique user ID"
    )


@router.get("/check/{user_id}")
async def check_user_exists(user_id: str, db: Session = Depends(get_db)):
    """
    사용자 ID 존재 여부 확인
    
    - **user_id**: 확인할 사용자 ID
    
    Returns:
        exists: 존재 여부
        session_count: 해당 사용자의 세션 수
    """
    session_count = db.query(ChatSession).filter(
        ChatSession.user_id == user_id
    ).count()
    
    return {
        "user_id": user_id,
        "exists": session_count > 0,
        "session_count": session_count
    }
