import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AppLayout } from '../components/Layout/AppLayout';
import { sessionService } from '../services/sessionService';
import { userService } from '../services/userService';
import type { Chat } from '../types';
import type { SessionFeedback } from '../types/feedback';

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

  // ✅ 피드백 로드 - AI 오류 대비
  useEffect(() => {
    const loadFeedback = async () => {
      if (!sessionId) {
        navigate('/');
        return;
      }

      try {
        // 1. 세션 메시지 데이터 로드 (통계용)
        const messagesData = await sessionService.getSessionMessages(sessionId);
        const messages = messagesData.messages || [];
        
        const totalTurns = messages.filter(msg => msg.role === 'user').length;
        const coachMessages = messages.filter(msg => msg.role === 'coach');
        const coachInterventions = coachMessages.length;
        const interventionRate = totalTurns > 0 ? (coachInterventions / totalTurns) * 100 : 0;

        // 2. 코치 개입 내역 구성
        const interventions = [];
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

        // ✅ 3. AI 피드백 가져오기 시도
        let finalFeedback = null;
        try {
          const feedbackResponse = await sessionService.getFeedback(sessionId);
          finalFeedback = feedbackResponse.final_feedback;
          console.log('✅ AI Feedback loaded:', feedbackResponse);
        } catch (error) {
          console.warn('⚠️ AI feedback not available, showing basic feedback only:', error);
          
          // ✅ AI 피드백이 없을 때 기본 구조 생성
          finalFeedback = {
            conversation_summary: `${messagesData.persona_name}와 ${totalTurns}번의 대화를 진행했습니다.`,
            user_profile: {
              tendencies: [],
              risk_signals: [],
              traits: [],
            },
            feedback: {
              user_tendency_summary: '대화 내용을 바탕으로 자세한 분석이 준비 중입니다.',
              situation_response_evaluation: {
                score: 0,
                good_points: [],
                improve_points: [],
                notes: 'AI 분석이 완료되지 않았습니다. 코치 개입 내역을 참고해주세요.',
              },
              sentence_expression_evaluation: {
                good_points: [],
                improve_points: [],
                rewrite_examples: [],
              },
              next_action_guide: {
                copyable_lines: [],
                next_drills: [],
                homework: [],
              },
            },
          };
        }

        // ✅ 4. 통합 피드백 데이터 구성
        const feedbackData: SessionFeedback = {
          session_id: sessionId,
          persona_name: messagesData.persona_name,
          total_turns: totalTurns,
          coach_interventions: coachInterventions,
          intervention_rate: interventionRate,
          interventions: interventions,
          final_feedback: finalFeedback,
          generated_at: new Date().toISOString(),
        };

        setFeedback(feedbackData);
        setIsLoading(false);

      } catch (error) {
        console.error('Failed to load feedback:', error);
        alert('피드백을 불러오는데 실패했습니다.');
        navigate('/');
      }
    };

    loadFeedback();
  }, [sessionId, navigate]);

  const handleSelectChat = (selectedSessionId: string) => {
    navigate(`/chat/${selectedSessionId}`);
    window.location.reload();
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
      showFeedback={true}
      feedbackData={feedback}
      loadingMessage="피드백을 불러오고 있습니다"
    />
  );
};
