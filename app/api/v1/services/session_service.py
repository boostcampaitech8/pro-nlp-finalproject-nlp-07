from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
import uuid

from app.models.session import ChatSession
from app.schemas.session import SessionCreate


class SessionService:
    """세션 관리 서비스"""
    
    @staticmethod
    def create_session(session_data: SessionCreate, db: Session) -> ChatSession:
        """새로운 세션 생성"""
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        
        existing_sessions = db.query(ChatSession).filter(
            ChatSession.user_id == session_data.user_id
        ).count()
        
        if existing_sessions == 0:
            print(f"🆕 신규 사용자: {session_data.user_id}")
        else:
            print(f"🔄 기존 사용자 ({existing_sessions}번째 세션): {session_data.user_id}")
        
        new_session = ChatSession(
            session_id=session_id,
            user_id=session_data.user_id,
            status="active",
            persona_name=session_data.persona_name,
            role_description=session_data.role_description,
            difficulty=session_data.difficulty,
            created_at=datetime.utcnow(),
            message_count=0,
            extra_data=session_data.metadata or {}
        )
        
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        return new_session
    
    @staticmethod
    def get_session(session_id: str, db: Session) -> ChatSession:
        """세션 조회"""
        return db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
    
    # ✅ 추가: 사용자별 세션 목록 조회
    @staticmethod
    def get_user_sessions(
        user_id: str, 
        db: Session,
        limit: int = 20,
        offset: int = 0,
        status_filter: str = None
    ) -> List[ChatSession]:
        """사용자의 세션 목록 조회"""
        query = db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        )
        
        if status_filter:
            query = query.filter(ChatSession.status == status_filter)
        
        query = query.order_by(ChatSession.created_at.desc())
        query = query.offset(offset).limit(limit)
        
        return query.all()
    
    # ✅ 추가: 사용자 세션 총 개수
    @staticmethod
    def count_user_sessions(
        user_id: str, 
        db: Session,
        status_filter: str = None
    ) -> int:
        """사용자의 총 세션 수 조회"""
        query = db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        )
        
        if status_filter:
            query = query.filter(ChatSession.status == status_filter)
        
        return query.count()
    
    @staticmethod
    def validate_session(session_id: str, db: Session) -> ChatSession:
        """세션 유효성 검증"""
        session = SessionService.get_session(session_id, db)
        
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        if session.status != "active":
            raise ValueError(f"Session is not active: {session.status}")
        
        return session
    
    # ✅ 신규: 세션 소유권 검증
    @staticmethod
    def validate_session_ownership(
        session_id: str, 
        user_id: str, 
        db: Session
    ) -> ChatSession:
        """
        세션 소유권 검증 (session_id + user_id)
        
        Args:
            session_id: 세션 ID
            user_id: 사용자 ID
            db: DB 세션
            
        Returns:
            ChatSession 객체
            
        Raises:
            ValueError: 세션이 없거나 소유자가 다른 경우
        """
        session = SessionService.get_session(session_id, db)
        
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        if session.user_id != user_id:
            raise ValueError(f"Unauthorized: User {user_id} does not own session {session_id}")
        
        return session
    
    @staticmethod
    def increment_message_count(session: ChatSession, db: Session):
        """메시지 카운트 증가"""
        session.message_count += 1
        session.updated_at = datetime.utcnow()
        db.commit()
    
    @staticmethod
    def update_difficulty(
        session_id: str, 
        new_difficulty: int, 
        db: Session
    ) -> ChatSession:
        """세션의 난이도 수정"""
        session = SessionService.validate_session(session_id, db)
        
        old_difficulty = session.difficulty
        session.difficulty = new_difficulty
        session.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(session)
        
        print(f"🔧 난이도 변경: {old_difficulty} → {new_difficulty} (세션: {session_id})")
        
        return session
