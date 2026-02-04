from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.models.session import ChatSession
from app.schemas.session import SessionCreate


class SessionService:
    """세션 관리 서비스"""
    
    @staticmethod
    def create_session(session_data: SessionCreate, db: Session) -> ChatSession:
        """
        새로운 세션 생성
        
        Args:
            session_data: 세션 생성 요청 데이터
            db: 데이터베이스 세션
            
        Returns:
            생성된 ChatSession 객체
        """
        # 세션 ID 생성
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        
        # 신규/기존 사용자 확인
        existing_sessions = db.query(ChatSession).filter(
            ChatSession.user_id == session_data.user_id
        ).count()
        
        if existing_sessions == 0:
            print(f"🆕 신규 사용자: {session_data.user_id}")
        else:
            print(f"🔄 기존 사용자 ({existing_sessions}번째 세션): {session_data.user_id}")
        
        # 세션 생성
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
        """
        세션 조회
        
        Args:
            session_id: 세션 ID
            db: 데이터베이스 세션
            
        Returns:
            ChatSession 객체 또는 None
        """
        return db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
    
    @staticmethod
    def validate_session(session_id: str, db: Session) -> ChatSession:
        """
        세션 유효성 검증
        
        Args:
            session_id: 세션 ID
            db: 데이터베이스 세션
            
        Returns:
            ChatSession 객체
            
        Raises:
            ValueError: 세션이 없거나 종료된 경우
        """
        session = SessionService.get_session(session_id, db)
        
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        if session.status != "active":
            raise ValueError(f"Session is not active: {session.status}")
        
        return session
    
    @staticmethod
    def increment_message_count(session: ChatSession, db: Session):
        """
        메시지 카운트 증가
        
        Args:
            session: ChatSession 객체
            db: 데이터베이스 세션
        """
        session.message_count += 1
        session.updated_at = datetime.utcnow()
        db.commit()
