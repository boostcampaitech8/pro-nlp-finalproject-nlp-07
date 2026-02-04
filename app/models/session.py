from sqlalchemy import Column, String, DateTime, Integer, JSON
from datetime import datetime
from app.db.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    session_id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    status = Column(String(20), default="active")

    persona_name = Column(String(100), nullable=False)
    role_description = Column(String(500), nullable=False)
    difficulty = Column(Integer, default=2)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    
    message_count = Column(Integer, default=0)
    user_rating = Column(Integer, nullable=True)
    extra_data = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<ChatSession {self.session_id} - {self.persona_name}>"
