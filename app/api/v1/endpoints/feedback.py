from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.feedback import SessionFeedback
from app.schemas.feedback import FeedbackResponse

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.get("/{session_id}", response_model=FeedbackResponse)
async def get_feedback(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    세션의 최종 피드백 조회 (DB에서 조회만)
    
    ✅ 역할:
    - DB에서 저장된 피드백 조회
    - 단순 조회 기능만 제공
    
    세션이 종료된 후에만 조회 가능합니다.
    """
    feedback = db.query(SessionFeedback).filter(
        SessionFeedback.session_id == session_id
    ).first()
    
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found. Session may not be ended yet."
        )
    
    return {
        "session_id": session_id,
        "feedback": feedback
    }
