import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppLayout } from '../components/Layout/AppLayout';
import { sessionService } from '../services/sessionService';
import { userService } from '../services/userService';
import { LoadingScreen } from '../components/Common/LoadingScreen';
import type { Chat } from '../types';

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [chatHistories, setChatHistories] = useState<Chat[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // ✅ localStorage에서 바로 가져오기 (무조건 있음)
  const userId = userService.getUserId() || '';

  // ✅ 페이지 로드 시 세션 목록 불러오기
  useEffect(() => {
    const loadSessions = async () => {
      try {
        console.log('Loading sessions for user:', userId);
        const response = await sessionService.getUserSessions(userId);
        
        const chats: Chat[] = response.sessions.map(session => ({
          id: session.session_id,
          title: `${session.persona_name} 연습`,
          timestamp: new Date(session.created_at),
          messageCount: session.message_count,
        }));

        console.log('Loaded sessions:', chats);
        setChatHistories(chats);
      } catch (error) {
        console.error('Failed to load sessions:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadSessions();
  }, [userId]);

  const handleSelectScenario = async (persona: string, situation: string) => {
    try {
      const response = await sessionService.createSession(userId, persona, situation);
      navigate(`/chat/${response.session_id}`, {
        state: { persona, situation },
      });
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const handleSelectChat = (sessionId: string) => {
    navigate(`/chat/${sessionId}`);
  };

  if (isLoading) {
    return <LoadingScreen message="대화 목록을 불러오는 중..." />;
  }

  return (
    <AppLayout
      messages={[]}
      chatHistories={chatHistories}
      currentChatId={null}
      isWaitingForResponse={false}
      inputValue=""
      onInputChange={() => {}}
      onSendMessage={() => {}}
      onNewChat={() => navigate('/')}
      onSelectChat={handleSelectChat}
      onSettings={() => {}}
      onSelectScenario={handleSelectScenario}
      onCustomCreate={() => {}}
      showScenarioSetup={true}
      personaName=""
    />
  );
};
