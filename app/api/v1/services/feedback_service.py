from typing import Dict, Any

from app.api.v1.services.agent_service import AgentService


class FeedbackService:
    """피드백 생성 서비스"""
    
    @staticmethod
    async def generate_feedback(session_id: str) -> Dict[str, Any]:
        """
        피드백 생성 (AgentService를 통해 호출)
        
        Args:
            session_id: 세션 ID
            
        Returns:
            AI 서버로부터 받은 피드백 데이터
        """
        
        print(f"🎯 피드백 생성 요청 - session_id: {session_id}")
        
        try:
            # AgentService를 통해 피드백 API 호출
            feedback_data = await AgentService.get_feedback(session_id)
            
            print(f"✅ 피드백 생성 완료")
            
            return feedback_data
            
        except Exception as e:
            print(f"❌ 피드백 생성 실패 - {type(e).__name__}: {str(e)}")
            raise
    
    
    @staticmethod
    async def test_connection() -> Dict[str, Any]:
        """피드백 API 연결 테스트 (AgentService의 health check 사용)"""
        return await AgentService.test_connection()
