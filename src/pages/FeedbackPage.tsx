import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AppLayout } from '../components/Layout/AppLayout';
import { sessionService } from '../services/sessionService';
import { userService } from '../services/userService';
import type { Chat } from '../types';
import type { SessionFeedback, CoachIntervention } from '../types/feedback';

export const FeedbackPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [feedback, setFeedback] = useState<SessionFeedback | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [chatHistories, setChatHistories] = useState<Chat[]>([]);

  const userId = userService.getUserId() || '';

  // 세션 목록 로드
  useEffect(() => {
    const loadSessions = async () => {
      try {
        const response = await sessionService.getUserSessions(userId);
        const chats: Chat[] = response.sessions.map(session => ({
          id: session.session_id,
          title: `${session.persona_name} 연습`,
          timestamp: new Date(session.created_at),
          messageCount: session.message_count,
          roleDescription: session.role_description,
        }));
        setChatHistories(chats);
      } catch (error) {
        console.error('Failed to load sessions:', error);
      }
    };

    loadSessions();
  }, [userId]);

  // 피드백 로드
  useEffect(() => {
    const loadFeedback = async () => {
      if (!sessionId) {
        navigate('/');
        return;
      }

      try {
        const messagesData = await sessionService.getSessionMessages(sessionId);
        const messages = messagesData.messages || [];
        
        const totalTurns = messages.filter(msg => msg.role === 'user').length;
        const coachMessages = messages.filter(msg => msg.role === 'coach');
        const coachInterventions = coachMessages.length;
        const interventionRate = totalTurns > 0 ? (coachInterventions / totalTurns) * 100 : 0;

        const interventions: CoachIntervention[] = [];
        
        for (let i = 0; i < messages.length; i++) {
          const msg = messages[i];
          
          if (msg.role === 'coach') {
            const prevMsg = i > 0 ? messages[i - 1] : null;
            
            if (prevMsg && prevMsg.role === 'user') {
              interventions.push({
                message_id: msg.message_id || `msg_${i}`,
                user_message: prevMsg.content,
                coach_feedback: msg.content,
                signals: [],
                timestamp: msg.timestamp || new Date().toISOString(),
              });
            }
          }
        }

        const mockFinalFeedback = {
          suggestions: [
            {
              task: 'empathy_training',
              description: '고객의 감정에 먼저 공감하는 연습하기',
            },
            {
              task: 'specific_solutions',
              description: '구체적이고 명확한 해결책 제시하기',
            },
            {
              task: 'proper_closing',
              description: '대화를 적절하게 마무리하는 방법 익히기',
            },
            {
              task: 'active_listening',
              description: '고객의 말을 경청하고 확인하는 습관 들이기',
            },
          ],
        };

        const feedbackData: SessionFeedback = {
          session_id: sessionId,
          persona_name: messagesData.persona_name,
          total_turns: totalTurns,
          coach_interventions: coachInterventions,
          intervention_rate: interventionRate,
          interventions: interventions,
          final_feedback: mockFinalFeedback,
        };

        setFeedback(feedbackData);
        setIsLoading(false);

      } catch (error) {
        console.error('Failed to load feedback:', error);
        setIsLoading(false);
      }
    };

    loadFeedback();
  }, [sessionId, navigate]);

  // 사이드바에서 세션 선택 시 - 피드백 페이지로 이동
  const handleSelectChat = (selectedSessionId: string) => {
    navigate(`/feedback/${selectedSessionId}`);
  };

  return (
    <AppLayout
      messages={[]}
      chatHistories={chatHistories}
      currentChatId={sessionId || null}
      isWaitingForResponse={false}
      inputValue=""
      onInputChange={() => {}}
      onSendMessage={() => {}}
      onNewChat={() => navigate('/')}
      onSelectChat={handleSelectChat}
      onSettings={() => {}}
      onSelectScenario={() => {}}
      onCustomCreate={() => {}}
      showScenarioSetup={false}
      personaName={feedback?.persona_name || ''}
      isLoading={isLoading}
      showFeedback={true} // ✅ 피드백 모드
      feedbackData={feedback} // ✅ 피드백 데이터
    />
  );
};
