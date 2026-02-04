from pydantic import BaseModel, Field
from typing import Optional


class AgentRequest(BaseModel):
    """에이전트 메시지 요청"""
    session_id: str = Field(..., description="세션 ID")
    message: str = Field(..., description="사용자 메시지", alias="user_text")
    
    use_supervisor: bool = Field(default=False, description="Supervisor 검수 사용 여부")
    
    class Config:
        populate_by_name = True


class AgentResponse(BaseModel):
    """에이전트 응답"""
    response: str = Field(..., description="AI 에이전트 응답")
    success: bool = Field(default=True, description="성공 여부")
    
    coach: Optional[dict] = Field(default=None, description="코치 피드백")
    supervisor: Optional[dict] = Field(default=None, description="Supervisor 검수 결과")


class SessionStartRequest(BaseModel):
    """세션 시작 요청"""
    session_id: str = Field(..., description="세션 ID")
    
    use_supervisor: bool = Field(default=False, description="Supervisor 검수 사용 여부")
