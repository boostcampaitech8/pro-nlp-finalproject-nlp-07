from sqlalchemy.orm import Session
from typing import Optional
import uuid
from datetime import datetime, timedelta

from app.models.session import ChatSession
from app.schemas.session import SessionCreate


class SessionService:
    """세션 관리 비즈니스 로직"""
    
    @staticmethod
    def create_session(
        session_data: SessionCreate,
        db: Session
    ) -> ChatSession:
        """새 세션 생성"""
        
        session_id = f"sess_{uuid.uuid4().hex[:16]}"
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        # 재방문 사용자 확인
        user_history_count = db.query(ChatSession).filter(
            ChatSession.user_id == session_data.user_id
        ).count()
        
        is_new_user = user_history_count == 0
        
        if is_new_user:
            print(f"🆕 신규 사용자: {session_data.user_id}")
        else:
            print(f"♻️ 재방문 사용자: {session_data.user_id} (기존 세션: {user_history_count}개)")
        
        # DB에 세션 저장
        new_session = ChatSession(
            session_id=session_id,
            user_id=session_data.user_id,
            status="active",
            scenario_type=session_data.scenario_type,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            extra_data=session_data.metadata  # ✅ metadata → extra_data (DB 필드명)
        )
        
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        return new_session
    
    @staticmethod
    def get_session(session_id: str, db: Session) -> Optional[ChatSession]:
        """세션 조회"""
        return db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
    
    @staticmethod
    def validate_session(session_id: str, db: Session) -> ChatSession:
        """세션 유효성 검증 (활성 세션인지)"""
        session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id,
            ChatSession.status == "active"
        ).first()
        
        if not session:
            raise ValueError("Session not found or expired")
        
        return session
    
    @staticmethod
    def increment_message_count(session: ChatSession, db: Session):
        """메시지 카운트 증가"""
        session.message_count += 1
        session.updated_at = datetime.utcnow()
        db.commit()
