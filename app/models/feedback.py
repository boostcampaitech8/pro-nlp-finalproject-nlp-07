from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from app.db.database import Base


class SessionFeedback(Base):
    """세션 피드백 모델"""
    __tablename__ = "session_feedback"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        String(50), 
        ForeignKey("chat_sessions.session_id", ondelete="CASCADE"),
        unique=True, 
        index=True,
        nullable=False
    )
    
    overall_score = Column(Integer, nullable=False)
    strengths = Column(JSON, nullable=False)  # List[str]
    improvements = Column(JSON, nullable=False)  # List[str]
    summary = Column(Text, nullable=False)
    
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
