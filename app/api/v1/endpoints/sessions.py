from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import case
from datetime import datetime
from typing import Optional

from app.db.database import get_db
from app.models.session import ChatSession
from app.models.message import Message
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
            role_description=s.role_description,
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
    user_id: str = Query(..., description="사용자 ID"),
    db: Session = Depends(get_db)
):
    """
    세션 상세 정보 조회
    
    - **session_id**: 세션 ID
    - **user_id**: 사용자 ID (소유권 검증)
    """
    
    # 소유권 검증
    try:
        session = SessionService.validate_session_ownership(session_id, user_id, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    
    return SessionResponse.model_validate(session)


@router.get("/{session_id}/messages", response_model=ConversationHistoryResponse)
async def get_session_messages(
    session_id: str,
    user_id: str = Query(..., description="사용자 ID"),
    limit: int = Query(default=100, ge=1, le=500, description="최대 개수"),
    offset: int = Query(default=0, ge=0, description="시작 위치"),
    db: Session = Depends(get_db)
):
    """
    세션의 대화 기록 조회
    
    - **session_id**: 세션 ID (필수)
    - **user_id**: 사용자 ID (소유권 검증)
    - **limit**: 최대 메시지 개수 (기본 100, 최대 500)
    - **offset**: 시작 위치 (페이징)
    
    Returns:
        세션의 전체 대화 기록 (시간순, role별)
    """
    
    # 1. 소유권 검증
    try:
        session = SessionService.validate_session_ownership(session_id, user_id, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    
    # 2. 메시지 조회 (timestamp + role 순서로 정렬)
    messages = db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(
        Message.timestamp.asc(),
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
        "role_description": session.role_description,
        "difficulty": session.difficulty,
        "status": session.status,
        "total_messages": total_messages,
        "messages": message_items
    }


@router.patch("/{session_id}/difficulty", response_model=SessionResponse)
async def update_session_difficulty(
    session_id: str,
    update_data: SessionDifficultyUpdate,  # ✅ 먼저
    user_id: str = Query(..., description="사용자 ID"),  # ✅ 나중에
    db: Session = Depends(get_db)
):
    """
    세션의 난이도 수정
    
    - **session_id**: 세션 ID (필수)
    - **user_id**: 사용자 ID (소유권 검증)
    - **difficulty**: 새로운 난이도 (1: 쉬움, 2: 보통, 3: 어려움)
    
    활성 상태의 세션만 수정 가능합니다.
    """
    
    # 소유권 검증
    try:
        session = SessionService.validate_session_ownership(session_id, user_id, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    
    # 난이도 수정
    session.difficulty = update_data.difficulty
    session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    
    print(f"🔧 난이도 변경: {session_id} -> {update_data.difficulty}")
    
    return SessionResponse.model_validate(session)


@router.post("/{session_id}/end", response_model=SessionEndResponse)
async def end_session(
    session_id: str,
    end_request: SessionEndRequest,
    db: Session = Depends(get_db)
):
    """
    세션 종료 및 최종 피드백 생성
    
    - **session_id**: 세션 ID
    - **user_id**: 요청 본문에 포함 (소유권 검증)
    - **user_rating**: 사용자 평가 (1-5, 선택)
    """
    
    # 1. 소유권 검증
    try:
        session = SessionService.validate_session_ownership(
            session_id=session_id,
            user_id=end_request.user_id,
            db=db
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    
    if session.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session already ended with status: {session.status}"
        )
    
    # 2. 세션 종료 처리
    session.status = "completed"
    session.ended_at = datetime.utcnow()
    session.user_rating = end_request.user_rating
    db.commit()
    
    print(f"✅ 세션 종료 처리 완료 - session_id: {session_id}")
    
    # 3. 피드백 생성 (AI 서버 호출)
    feedback_generated = False
    error_message = None
    
    try:
        feedback_data = await FeedbackService.generate_feedback(session_id)
        
        # 4. 피드백 DB 저장
        final_feedback = feedback_data.get("final_feedback", {})
        user_profile = final_feedback.get("user_profile", {})
        feedback_detail = final_feedback.get("feedback", {})
        situation_eval = feedback_detail.get("situation_response_evaluation", {})
        expression_eval = feedback_detail.get("sentence_expression_evaluation", {})
        next_action = feedback_detail.get("next_action_guide", {})
        
        feedback = SessionFeedback(
            session_id=session_id,
            # 사용자 프로필
            user_traits=user_profile.get("traits", []),
            user_tendencies=user_profile.get("tendencies", []),
            user_risk_signals=user_profile.get("risk_signals", []),
            # 대화 요약
            conversation_summary=final_feedback.get("conversation_summary", ""),
            # 사용자 경향 요약
            user_tendency_summary=feedback_detail.get("user_tendency_summary", ""),
            # 상황 대응 평가
            situation_score=situation_eval.get("score"),
            situation_good_points=situation_eval.get("good_points", []),
            situation_improve_points=situation_eval.get("improve_points", []),
            situation_notes=situation_eval.get("notes", ""),
            # 문장 표현 평가
            expression_good_points=expression_eval.get("good_points", []),
            expression_improve_points=expression_eval.get("improve_points", []),
            expression_rewrite_examples=expression_eval.get("rewrite_examples", []),
            # 다음 액션 가이드
            next_copyable_lines=next_action.get("copyable_lines", []),
            next_drills=next_action.get("next_drills", []),
            next_homework=next_action.get("homework", []),
            # 메타데이터
            generated_at=datetime.utcnow(),
            raw_response=feedback_data
        )
        
        db.add(feedback)
        db.commit()
        
        feedback_generated = True
        print(f"✅ 피드백 DB 저장 완료 - session_id: {session_id}")
        
    except Exception as e:
        error_message = str(e)
        print(f"⚠️ 피드백 생성 실패 (세션은 종료됨)")
        print(f"   Error: {error_message}")
    
    # 5. FE로 응답
    message = "Session ended successfully" if feedback_generated else f"Session ended but feedback generation failed: {error_message}"
    
    return {
        "session_id": session_id,
        "status": session.status,
        "ended_at": session.ended_at,
        "message": message,
        "feedback_generated": feedback_generated
    }


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    user_id: str = Query(..., description="사용자 ID"),
    db: Session = Depends(get_db)
):
    """
    세션 삭제
    
    - **session_id**: 세션 ID (필수)
    - **user_id**: 사용자 ID (소유권 검증)
    
    세션과 관련된 모든 데이터(메시지, 피드백)가 함께 삭제됩니다.
    """
    
    # 1. 소유권 검증
    try:
        session = SessionService.validate_session_ownership(session_id, user_id, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    
    # 2. 관련 데이터 삭제 (CASCADE 설정되어 있으면 자동 삭제)
    db.query(Message).filter(
        Message.session_id == session_id
    ).delete()
    
    db.query(SessionFeedback).filter(
        SessionFeedback.session_id == session_id
    ).delete()
    
    # 3. 세션 삭제
    db.delete(session)
    db.commit()
    
    print(f"✅ 세션 삭제 완료 - session_id: {session_id}")
    
    return
