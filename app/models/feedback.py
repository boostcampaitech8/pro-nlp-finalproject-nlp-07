from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base


class SessionFeedback(Base):
    """세션 피드백 테이블 (AI 서버 응답 구조에 맞춤)"""
    __tablename__ = "session_feedback"
    
    # 기본 키
    session_id = Column(String(50), ForeignKey("chat_sessions.session_id"), primary_key=True)
    
    # 사용자 프로필
    user_traits = Column(JSON, nullable=True, comment="사용자 특성 리스트")
    user_tendencies = Column(JSON, nullable=True, comment="사용자 경향 리스트")
    user_risk_signals = Column(JSON, nullable=True, comment="위험 신호 리스트")
    
    # 대화 요약
    conversation_summary = Column(Text, nullable=True, comment="대화 요약")
    
    # 피드백 - 사용자 경향 요약
    user_tendency_summary = Column(Text, nullable=True, comment="사용자 경향 요약")
    
    # 피드백 - 상황 대응 평가
    situation_score = Column(Integer, nullable=True, comment="상황 대응 점수 (1-5)")
    situation_good_points = Column(JSON, nullable=True, comment="상황 대응 잘한 점")
    situation_improve_points = Column(JSON, nullable=True, comment="상황 대응 개선 사항")
    situation_notes = Column(Text, nullable=True, comment="상황 대응 추가 노트")
    
    # 피드백 - 문장 표현 평가
    expression_good_points = Column(JSON, nullable=True, comment="표현 잘한 점")
    expression_improve_points = Column(JSON, nullable=True, comment="표현 개선 사항")
    expression_rewrite_examples = Column(JSON, nullable=True, comment="표현 재작성 예시")
    
    # 피드백 - 다음 액션 가이드
    next_copyable_lines = Column(JSON, nullable=True, comment="복사 가능한 문장들")
    next_drills = Column(JSON, nullable=True, comment="다음 연습 항목")
    next_homework = Column(JSON, nullable=True, comment="숙제")
    
    # 메타데이터
    generated_at = Column(DateTime, default=datetime.utcnow, comment="피드백 생성 시각")
    raw_response = Column(JSON, nullable=True, comment="AI 서버 원본 응답 (백업)")
    
    def __repr__(self):
        return f"<SessionFeedback(session_id={self.session_id}, score={self.situation_score})>"
