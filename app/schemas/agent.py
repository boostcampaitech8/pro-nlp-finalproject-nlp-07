from pydantic import BaseModel, Field
from typing import Optional


class AgentRequest(BaseModel):
    """에이전트 메시지 요청"""
    session_id: str = Field(..., description="세션 ID")
    message: str = Field(..., description="사용자 메시지", alias="user_text")
    template_id: int = Field(default=1, description="템플릿 ID (1: 친한 친구, 2: 무뚝뚝한 점원)")
    use_supervisor: bool = Field(default=False, description="Supervisor 검수 사용 여부")
    
    class Config:
        populate_by_name = True  # alias와 원래 이름 둘 다 허용


class AgentResponse(BaseModel):
    """에이전트 응답"""
    response: str = Field(..., description="AI 에이전트 응답")
    success: bool = Field(default=True, description="성공 여부")
    
    # ✅ 추가 응답 필드 (선택)
    coach: Optional[dict] = Field(default=None, description="코치 피드백 (있는 경우)")
    supervisor: Optional[dict] = Field(default=None, description="Supervisor 검수 결과 (있는 경우)")
