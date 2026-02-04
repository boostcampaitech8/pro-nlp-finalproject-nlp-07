from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.database import get_db
from app.models.session import ChatSession
from app.models.agent import AgentMessage
from app.models.feedback import SessionFeedback
from app.schemas.session import (
    SessionCreate,
    SessionResponse,
    SessionEndRequest,
    SessionEndResponse
)
from app.api.v1.services.session_service import SessionService
from app.api.v1.services.feedback_service import FeedbackService

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db)
):
    """새로운 채팅 세션 생성"""
    session = SessionService.create_session(session_data, db)
    return SessionResponse.model_validate(session)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """세션 정보 조회"""
    session = SessionService.get_session(session_id, db)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return SessionResponse.model_validate(session)


@router.post("/{session_id}/end", response_model=SessionEndResponse)
async def end_session(
    session_id: str,
    end_request: SessionEndRequest,
    db: Session = Depends(get_db)
):
    """
    세션 종료 및 최종 피드백 생성
    
    ✅ 역할:
    1. 세션 유효성 검증
    2. 대화 내역 조회
    3. FeedbackService로 피드백 생성 (비즈니스 로직)
    4. DB에 피드백 저장 (데이터 레이어)
    5. 세션 상태 업데이트
    6. 응답 반환
    """
    
    # 1. 세션 조회
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session already ended with status: {session.status}"
        )
    
    # 2. 대화 내역 가져오기
    messages = db.query(AgentMessage).filter(
        AgentMessage.session_id == session_id
    ).order_by(AgentMessage.timestamp).all()
    
    if not messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot end session without any messages"
        )
    
    # 3. ✅ FeedbackService로 피드백 생성 (비즈니스 로직)
    # TODO: 향후 AI 기반 피드백으로 변경
    # feedback_data = await FeedbackService.generate_ai_feedback(session, messages)
    feedback_data = FeedbackService.generate_feedback(session, messages)
    
    # 4. 통계 계산
    duration = (datetime.utcnow() - session.created_at).total_seconds() / 60
    
    # 5. 세션 종료
    session.status = "completed"
    session.ended_at = datetime.utcnow()
    session.end_reason = end_request.reason
    session.user_rating = end_request.user_rating
    
    # 6. ✅ DB에 피드백 저장 (데이터 레이어)
    feedback = SessionFeedback(
        session_id=session_id,
        overall_score=feedback_data["score"],
        strengths=feedback_data["strengths"],
        improvements=feedback_data["improvements"],
        summary=feedback_data["summary"],
        generated_at=datetime.utcnow()
    )
    
    db.add(feedback)
    db.commit()
    db.refresh(session)
    db.refresh(feedback)
    
    # 7. 응답 구성
    return {
        "session_id": session_id,
        "status": session.status,
        "ended_at": session.ended_at,
        "feedback": {
            "overall_score": feedback.overall_score,
            "strengths": feedback.strengths,
            "improvements": feedback.improvements,
            "summary": feedback.summary,
            "generated_at": feedback.generated_at
        },
        "statistics": {
            "total_messages": len(messages),
            "duration_minutes": int(duration),
            "average_response_time_seconds": 0.0
        }
    }


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """세션 삭제"""
    session = SessionService.get_session(session_id, db)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    db.delete(session)
    db.commit()
