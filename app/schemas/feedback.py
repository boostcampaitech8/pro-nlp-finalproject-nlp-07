from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class UserProfile(BaseModel):
    """사용자 프로필"""
    traits: List[str] = Field(default_factory=list, description="사용자 특성")
    tendencies: List[str] = Field(default_factory=list, description="사용자 경향")
    risk_signals: List[str] = Field(default_factory=list, description="위험 신호")


class SituationResponseEvaluation(BaseModel):
    """상황 대응 평가"""
    score: int = Field(..., ge=1, le=5, description="점수 (1-5)")
    good_points: List[str] = Field(default_factory=list, description="잘한 점")
    improve_points: List[str] = Field(default_factory=list, description="개선할 점")
    notes: Optional[str] = Field(default="", description="추가 노트")


class SentenceExpressionEvaluation(BaseModel):
    """문장 표현 평가"""
    good_points: List[str] = Field(default_factory=list, description="잘한 점")
    improve_points: List[str] = Field(default_factory=list, description="개선할 점")
    rewrite_examples: List[str] = Field(default_factory=list, description="재작성 예시")


class NextActionGuide(BaseModel):
    """다음 액션 가이드"""
    copyable_lines: List[str] = Field(default_factory=list, description="복사 가능한 문장")
    next_drills: List[str] = Field(default_factory=list, description="다음 연습 항목")
    homework: List[str] = Field(default_factory=list, description="숙제")


class FeedbackDetail(BaseModel):
    """피드백 상세"""
    user_tendency_summary: str = Field(..., description="사용자 경향 요약")
    situation_response_evaluation: SituationResponseEvaluation
    sentence_expression_evaluation: SentenceExpressionEvaluation
    next_action_guide: NextActionGuide


class FinalFeedback(BaseModel):
    """최종 피드백"""
    user_profile: UserProfile
    conversation_summary: str = Field(..., description="대화 요약")
    feedback: FeedbackDetail


class FeedbackResponse(BaseModel):
    """피드백 응답"""
    session_id: str
    final_feedback: FinalFeedback
    generated_at: datetime
    
    class Config:
        from_attributes = True
