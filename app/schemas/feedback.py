from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


class FeedbackDetail(BaseModel):
    """피드백 상세"""
    overall_score: int = Field(..., ge=0, le=100, description="종합 점수 (0-100)")
    strengths: List[str] = Field(..., description="강점 목록")
    improvements: List[str] = Field(..., description="개선점 목록")
    summary: str = Field(..., description="종합 요약")
    generated_at: datetime
    
    class Config:
        from_attributes = True


class FeedbackResponse(BaseModel):
    """피드백 조회 응답"""
    session_id: str
    feedback: FeedbackDetail
