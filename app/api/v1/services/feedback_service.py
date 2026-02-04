from typing import List, Dict
from app.models.agent import AgentMessage
from app.models.session import ChatSession


class FeedbackService:
    """피드백 생성 비즈니스 로직 (DB 저장 X)"""
    
    @staticmethod
    def generate_feedback(
        session: ChatSession,
        messages: List[AgentMessage]
    ) -> Dict:
        """
        최종 피드백 생성 (비즈니스 로직만)
        
        Args:
            session: 세션 객체
            messages: 대화 메시지 리스트
            
        Returns:
            피드백 데이터 딕셔너리
            {
                "score": 85,
                "strengths": ["...", "..."],
                "improvements": ["...", "..."],
                "summary": "..."
            }
        """
        message_count = len(messages)
        
        # 기본 점수 계산 (메시지 수 기반)
        base_score = 60
        message_bonus = min(30, message_count * 2)
        overall_score = base_score + message_bonus
        
        # 강점 분석
        strengths = [
            "명확한 의사소통",
            f"{message_count}개의 메시지로 충분한 대화 진행"
        ]
        
        if message_count >= 10:
            strengths.append("적극적인 대화 참여")
        
        if session.scenario_type == "interview":
            strengths.append("면접 상황에 적합한 태도")
        
        # 개선점 분석
        improvements = []
        
        if message_count < 5:
            improvements.append("좀 더 많은 대화가 필요합니다")
        
        improvements.extend([
            "구체적인 예시 추가",
            "전문 용어 활용 증가"
        ])
        
        # 요약 생성
        summary = (
            f"{session.scenario_type} 시나리오에서 전반적으로 좋은 대화를 나누었습니다. "
            f"총 {message_count}개의 메시지를 주고받았으며, "
            f"의사소통 능력이 우수합니다."
        )
        
        if message_count < 5:
            summary += " 다음에는 좀 더 긴 대화를 시도해보세요."
        
        return {
            "score": overall_score,
            "strengths": strengths,
            "improvements": improvements,
            "summary": summary
        }
    
    @staticmethod
    async def generate_ai_feedback(
        session: ChatSession,
        messages: List[AgentMessage]
    ) -> Dict:
        """
        AI 기반 피드백 생성 (향후 구현)
        
        TODO: 실제 AI 서비스 연동
        - 외부 Agent API 호출
        - 대화 분석
        - 맞춤형 피드백 생성
        
        Args:
            session: 세션 객체
            messages: 대화 메시지 리스트
            
        Returns:
            피드백 데이터 딕셔너리
        """
        # TODO: 외부 Agent API의 피드백 엔드포인트 호출
        # import httpx
        # from app.core.config import AGENT_API_HOST
        # from app.api.v1.services.agent_service import AgentService
        # 
        # api_url = AgentService.get_endpoint_url("feedback")
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         api_url,
        #         json={
        #             "session_id": session.session_id,
        #             "messages": [{"user": m.user_message, "agent": m.agent_response} for m in messages]
        #         }
        #     )
        #     return response.json()
        
        # 임시로 기본 피드백 반환
        return FeedbackService.generate_feedback(session, messages)
