from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import case
from datetime import datetime
from typing import Optional

from app.db.database import get_db
from app.models.session import ChatSession
from app.models.message import Message  # ✅ 변경
from app.models.feedback import SessionFeedback
from app.schemas.session import (
    SessionCreate,
    SessionResponse,
    SessionListResponse,
    SessionListItem,
    SessionDifficultyUpdate,
    SessionEndRequest,
    SessionEndResponse,
    MessageItem,
    ConversationHistoryResponse
)
from app.api.v1.services.session_service import SessionService
from app.api.v1.services.feedback_service import FeedbackService


router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db)
):
    """
    새로운 채팅 세션 생성
    
    - **user_id**: 익명 사용자 ID (anon_<UUID> 형식)
    - **persona_name**: 페르소나 이름 (예: "면접관", "친한 친구")
    - **role_description**: 역할 설명
    - **difficulty**: 난이도 (1: 쉬움, 2: 보통, 3: 어려움)
    - **metadata**: 추가 메타데이터 (선택)
    """
    session = SessionService.create_session(session_data, db)
    return SessionResponse.model_validate(session)


@router.get("/user/{user_id}", response_model=SessionListResponse)
async def get_user_sessions(
    user_id: str,
    limit: int = Query(default=20, ge=1, le=100, description="최대 개수"),
    offset: int = Query(default=0, ge=0, description="시작 위치"),
    status: Optional[str] = Query(default=None, description="상태 필터 (active, completed)"),
    db: Session = Depends(get_db)
):
    """
    사용자의 세션 목록 조회 (최신순)
    
    - **user_id**: 사용자 ID (anon_<UUID> 형식)
    - **limit**: 최대 개수 (기본 20, 최대 100)
    - **offset**: 시작 위치 (페이징)
    - **status**: 상태 필터 (active, completed, 없으면 전체)
    
    Returns:
        사용자의 세션 목록 (최신순 정렬)
    """
    
    # 세션 목록 조회
    sessions = SessionService.get_user_sessions(
        user_id=user_id,
        db=db,
        limit=limit,
        offset=offset,
        status_filter=status
    )
    
    # 총 개수
    total = SessionService.count_user_sessions(
        user_id=user_id,
        db=db,
        status_filter=status
    )
    
    # 응답 구성
    session_items = [
        SessionListItem(
            session_id=s.session_id,
            persona_name=s.persona_name,
            difficulty=s.difficulty,
            status=s.status,
            created_at=s.created_at,
            message_count=s.message_count
        )
        for s in sessions
    ]
    
    return {
        "user_id": user_id,
        "total_sessions": total,
        "sessions": session_items
    }


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """세션 상세 정보 조회"""
    session = SessionService.get_session(session_id, db)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return SessionResponse.model_validate(session)


@router.get("/{session_id}/messages", response_model=ConversationHistoryResponse)
async def get_session_messages(
    session_id: str,
    limit: int = Query(default=100, ge=1, le=500, description="최대 개수"),
    offset: int = Query(default=0, ge=0, description="시작 위치"),
    db: Session = Depends(get_db)
):
    """
    세션의 대화 기록 조회
    
    - **session_id**: 세션 ID (필수)
    - **limit**: 최대 메시지 개수 (기본 100, 최대 500)
    - **offset**: 시작 위치 (페이징)
    
    Returns:
        세션의 전체 대화 기록 (시간순, role별)
    """
    
    # 1. 세션 존재 확인
    session = SessionService.get_session(session_id, db)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # 2. 메시지 조회 (✅ timestamp + role 순서로 정렬)
    messages = db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(
        Message.timestamp.asc(),
        # ✅ case 사용 (db.case → case)
        case(
            (Message.role == 'system', 1),
            (Message.role == 'user', 2),
            (Message.role == 'coach', 3),
            (Message.role == 'persona', 4),
            else_=5
        )
    ).offset(offset).limit(limit).all()
    
    # 3. 총 메시지 수
    total_messages = db.query(Message).filter(
        Message.session_id == session_id
    ).count()
    
    # 4. 응답 구성
    message_items = [
        MessageItem(
            message_id=msg.message_id,
            session_id=msg.session_id,
            role=msg.role,
            content=msg.content,
            timestamp=msg.timestamp
        )
        for msg in messages
    ]
    
    return {
        "session_id": session_id,
        "persona_name": session.persona_name,
        "role_description": session.role_description,  # ✅ 추가
        "difficulty": session.difficulty,
        "status": session.status,
        "total_messages": total_messages,
        "messages": message_items
    }


@router.patch("/{session_id}/difficulty", response_model=SessionResponse)
async def update_session_difficulty(
    session_id: str,
    update_data: SessionDifficultyUpdate,
    db: Session = Depends(get_db)
):
    """
    세션의 난이도 수정
    
    - **session_id**: 세션 ID (필수)
    - **difficulty**: 새로운 난이도 (1: 쉬움, 2: 보통, 3: 어려움)
    
    활성 상태의 세션만 수정 가능합니다.
    """
    try:
        session = SessionService.update_difficulty(
            session_id=session_id,
            new_difficulty=update_data.difficulty,
            db=db
        )
        return SessionResponse.model_validate(session)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{session_id}/end", response_model=SessionEndResponse)
async def end_session(
    session_id: str,
    end_request: SessionEndRequest,
    db: Session = Depends(get_db)
):
    """세션 종료 및 최종 피드백 생성"""
    
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
    
    # 2. 대화 내역 가져오기 (✅ Message 모델 사용)
    messages = db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.timestamp).all()
    
    if not messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot end session without any messages"
        )
    
    # 3. 피드백 생성
    feedback_data = FeedbackService.generate_feedback(session, messages)
    
    # 4. 통계 계산
    duration = (datetime.utcnow() - session.created_at).total_seconds() / 60
    
    # 5. 세션 종료
    session.status = "completed"
    session.ended_at = datetime.utcnow()
    session.user_rating = end_request.user_rating
    
    # 6. 피드백 저장
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
