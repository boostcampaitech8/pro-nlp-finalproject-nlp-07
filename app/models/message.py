from sqlalchemy import Column, String, DateTime, JSON, Text
from datetime import datetime
from app.db.database import Base


class Message(Base):
    __tablename__ = "messages"
    
    message_id = Column(String(50), primary_key=True, index=True)
    session_id = Column(String(50), nullable=False, index=True)
    
    role = Column(String(20), nullable=False)  # user, coach, persona, system
    content = Column(Text, nullable=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    extra_data = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<Message {self.message_id} - {self.role}>"
