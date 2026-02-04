from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from app.db.database import Base


class AgentMessage(Base):
    """에이전트 대화 메시지 모델"""
    __tablename__ = "agent_messages"
    
    message_id = Column(String(50), primary_key=True, index=True)
    session_id = Column(
        String(50), 
        ForeignKey("chat_sessions.session_id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    user_message = Column(Text, nullable=False)
    agent_response = Column(Text, nullable=False)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    extra_data = Column(JSON, nullable=True)  # ✅ metadata → extra_data 변경
