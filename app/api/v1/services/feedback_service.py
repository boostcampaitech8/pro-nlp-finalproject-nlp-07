from typing import List, Dict, Any
from app.models.message import Message  # ✅ 변경
from app.models.session import ChatSession


class FeedbackService:
    """피드백 생성 서비스"""
    
    @staticmethod
    def generate_feedback(
        session: ChatSession, 
        messages: List[Message]  # ✅ 변경
    ) -> Dict[str, Any]:
        """
        세션 종료 시 종합 피드백 생성
        
        Args:
            session: ChatSession 객체
            messages: 메시지 리스트
            
        Returns:
            피드백 데이터 딕셔너리
        """
        
        # 간단한 피드백 생성 로직 (실제로는 더 복잡할 수 있음)
        total_messages = len(messages)
        
        # user 메시지만 카운트
        user_messages = [msg for msg in messages if msg.role == "user"]
        user_message_count = len(user_messages)
        
        # coach 개입 횟수
        coach_interventions = [msg for msg in messages if msg.role == "coach"]
        coach_count = len(coach_interventions)
        
        # 점수 계산 (예시)
        base_score = 70
        if user_message_count > 5:
            base_score += 10
        if coach_count < 3:
            base_score += 10
        
        score = min(base_score, 100)
        
        # 강점
        strengths = []
        if user_message_count > 10:
            strengths.append("적극적으로 대화에 참여했습니다.")
        if coach_count < 2:
            strengths.append("대체로 적절한 의사소통을 했습니다.")
        
        if not strengths:
            strengths.append("대화를 완료했습니다.")
        
        # 개선점
        improvements = []
        if coach_count > 5:
            improvements.append("코치의 피드백을 더 적극적으로 반영해보세요.")
        if user_message_count < 5:
            improvements.append("더 긴 대화를 통해 연습해보세요.")
        
        if not improvements:
            improvements.append("계속해서 연습하면 더 나아질 것입니다.")
        
        # 요약
        summary = f"{session.persona_name}과의 대화를 완료했습니다. "
        summary += f"총 {user_message_count}개의 메시지를 주고받았으며, "
        summary += f"코치가 {coach_count}번 개입했습니다. "
        
        if score >= 80:
            summary += "전반적으로 좋은 대화였습니다."
        elif score >= 60:
            summary += "괜찮은 대화였으나 개선의 여지가 있습니다."
        else:
            summary += "더 많은 연습이 필요합니다."
        
        return {
            "score": score,
            "strengths": strengths,
            "improvements": improvements,
            "summary": summary
        }
