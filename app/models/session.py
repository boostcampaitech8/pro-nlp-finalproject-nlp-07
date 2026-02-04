from sqlalchemy import Column, String, Integer, DateTime, JSON
from sqlalchemy.sql import func
from app.db.database import Base


class ChatSession(Base):
    """채팅 세션 모델"""
    __tablename__ = "chat_sessions"
    
    session_id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(100), index=True, nullable=False)
    status = Column(String(20), default="active")
    scenario_type = Column(String(50), default="interview")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    message_count = Column(Integer, default=0)
    end_reason = Column(String(50), nullable=True)
    user_rating = Column(Integer, nullable=True)
    
    extra_data = Column(JSON, nullable=True)  # ✅ metadata → extra_data 변경
