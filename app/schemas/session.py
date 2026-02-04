from pydantic import BaseModel, validator, Field
from typing import Optional, Dict, Any
from datetime import datetime
import re


class SessionCreate(BaseModel):
    """세션 생성 요청"""
    user_id: str = Field(..., description="사용자 익명 ID")
    
    persona_name: str = Field(..., description="페르소나 이름")
    role_description: str = Field(..., description="역할 설명")
    difficulty: int = Field(default=2, ge=1, le=3, description="난이도 (1-3)")  # ✅ 1~3
    
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('user_id')
    def validate_user_id(cls, v):
        pattern = r'^anon_[a-f0-9-]{36}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid user ID format. Must be anon_<UUID>')
        return v


class SessionResponse(BaseModel):
    """세션 생성/조회 응답"""
    session_id: str
    user_id: str
    status: str
    
    persona_name: str
    role_description: str
    difficulty: int
    
    created_at: datetime
    message_count: int = 0
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True
    
    @classmethod
    def model_validate(cls, obj, **kwargs):
        """ORM 객체를 Pydantic 모델로 변환"""
        if hasattr(obj, '__dict__'):
            data = {
                'session_id': obj.session_id,
                'user_id': obj.user_id,
                'status': obj.status,
                'persona_name': obj.persona_name,
                'role_description': obj.role_description,
                'difficulty': obj.difficulty,
                'created_at': obj.created_at,
                'message_count': obj.message_count,
                'metadata': obj.extra_data if hasattr(obj, 'extra_data') else None
            }
            return cls(**data)
        return super().model_validate(obj, **kwargs)


class SessionDifficultyUpdate(BaseModel):
    """세션 난이도 수정 요청"""
    difficulty: int = Field(..., ge=1, le=3, description="난이도 (1-3)")  # ✅ 1~3


class SessionEndRequest(BaseModel):
    """세션 종료 요청"""
    user_rating: Optional[int] = Field(None, ge=1, le=5, description="사용자 평점 (1-5)")


class SessionStatistics(BaseModel):
    """세션 통계"""
    total_messages: int
    duration_minutes: int
    average_response_time_seconds: float = 0.0


class FeedbackDetailInline(BaseModel):
    """피드백 상세 (인라인)"""
    overall_score: int = Field(..., ge=0, le=100, description="종합 점수 (0-100)")
    strengths: list[str] = Field(..., description="강점 목록")
    improvements: list[str] = Field(..., description="개선점 목록")
    summary: str = Field(..., description="종합 요약")
    generated_at: datetime


class SessionEndResponse(BaseModel):
    """세션 종료 응답"""
    session_id: str
    status: str
    ended_at: datetime
    feedback: FeedbackDetailInline
    statistics: SessionStatistics
