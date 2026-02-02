from pydantic import BaseModel
from datetime import datetime

class ChatMessageCreate(BaseModel):
    message: str

class ChatResponse(BaseModel):
    message: str

class ChatMessageResponse(BaseModel):
    id: int
    user_message: str
    bot_response: str
    created_at: datetime
    
    class Config:
        from_attributes = True
