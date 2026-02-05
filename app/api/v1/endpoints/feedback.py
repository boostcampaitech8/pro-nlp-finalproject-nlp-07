from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.feedback import SessionFeedback
from app.schemas.feedback import (
    FeedbackResponse,
    FinalFeedback,
    UserProfile,
    FeedbackDetail,
    SituationResponseEvaluation,
    SentenceExpressionEvaluation,
    NextActionGuide
)
from app.api.v1.services.feedback_service import FeedbackService


router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.get("/{session_id}", response_model=FeedbackResponse)
async def get_session_feedback(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    세션 피드백 조회
    
    - **session_id**: 세션 ID
    
    Returns:
        세션의 피드백 내용 (raw_response 제외)
    """
    
    # 1. DB에서 피드백 조회
    feedback = db.query(SessionFeedback).filter(
        SessionFeedback.session_id == session_id
    ).first()
    
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found for this session"
        )
    
    # 2. 응답 구성 (raw_response 제외)
    return FeedbackResponse(
        session_id=feedback.session_id,
        final_feedback=FinalFeedback(
            user_profile=UserProfile(
                traits=feedback.user_traits or [],
                tendencies=feedback.user_tendencies or [],
                risk_signals=feedback.user_risk_signals or []
            ),
            conversation_summary=feedback.conversation_summary or "",
            feedback=FeedbackDetail(
                user_tendency_summary=feedback.user_tendency_summary or "",
                situation_response_evaluation=SituationResponseEvaluation(
                    score=feedback.situation_score or 0,
                    good_points=feedback.situation_good_points or [],
                    improve_points=feedback.situation_improve_points or [],
                    notes=feedback.situation_notes or ""
                ),
                sentence_expression_evaluation=SentenceExpressionEvaluation(
                    good_points=feedback.expression_good_points or [],
                    improve_points=feedback.expression_improve_points or [],
                    rewrite_examples=feedback.expression_rewrite_examples or []
                ),
                next_action_guide=NextActionGuide(
                    copyable_lines=feedback.next_copyable_lines or [],
                    next_drills=feedback.next_drills or [],
                    homework=feedback.next_homework or []
                )
            )
        ),
        generated_at=feedback.generated_at
    )


@router.get("/test/connection")
async def test_feedback_api():
    """피드백 API 연결 테스트"""
    result = await FeedbackService.test_connection()
    
    if result["status"] == "connected":
        return {
            "message": "✅ Feedback API 연결 성공",
            **result
        }
    else:
        return {
            "message": "❌ Feedback API 연결 실패",
            **result
        }
