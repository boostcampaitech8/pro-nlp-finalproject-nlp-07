from pydantic import BaseModel, Field
from typing import Optional, List


class AgentRequest(BaseModel):
    """에이전트 메시지 요청"""
    session_id: str = Field(..., description="세션 ID")
    user_id: str = Field(..., description="사용자 ID")  # ✅ 추가
    message: str = Field(..., description="사용자 메시지", alias="user_text")
    use_supervisor: bool = Field(default=False, description="Supervisor 검수 사용 여부")
    
    class Config:
        populate_by_name = True


class CoachDetail(BaseModel):
    """코치 피드백 상세"""
    intervene: bool = Field(..., description="개입 여부")
    rewrite: Optional[str] = Field(None, description="추천 답변")
    signals: List[str] = Field(default_factory=list, description="피드백 신호")


class AgentResponse(BaseModel):
    """에이전트 응답"""
    response: str = Field(..., description="AI 에이전트 응답")
    success: bool = Field(default=True, description="성공 여부")
    coach: Optional[CoachDetail] = Field(default=None, description="코치 피드백 상세")


class SessionStartRequest(BaseModel):
    """세션 시작 요청"""
    session_id: str = Field(..., description="세션 ID")
    user_id: str = Field(..., description="사용자 ID")  # ✅ 추가
    use_supervisor: bool = Field(default=False, description="Supervisor 검수 사용 여부")
