import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppLayout } from '../components/Layout/AppLayout';
import { CustomScenarioModal } from '../components/Common/CustomScenarioModal';
import { sessionService } from '../services/sessionService';
import { userService } from '../services/userService';
import type { Chat } from '../types';

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [chatHistories, setChatHistories] = useState<Chat[]>([]);
  // ✅ isLoading 제거
  const [isCustomModalOpen, setIsCustomModalOpen] = useState(false);

  const userId = userService.getUserId() || '';

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
          roleDescription: session.role_description,
        }));

        console.log('Loaded sessions:', chats);
        setChatHistories(chats);
      } catch (error) {
        console.error('Failed to load sessions:', error);
      }
      // ✅ finally 블록 제거
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

  const handleCustomCreate = () => {
    setIsCustomModalOpen(true);
    console.log('✅ Custom modal opened');
  };

  const handleCustomModalClose = () => {
    setIsCustomModalOpen(false);
  };

  const handleCustomScenarioSubmit = async (persona: string, situation: string) => {
    try {
      const response = await sessionService.createSession(userId, persona, situation);
      setIsCustomModalOpen(false);
      navigate(`/chat/${response.session_id}`, {
        state: { persona, situation },
      });
    } catch (error) {
      console.error('Failed to create custom session:', error);
    }
  };

  // ✅ 로딩 화면 제거 - 바로 렌더링
  return (
    <>
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
        onCustomCreate={handleCustomCreate}
        showScenarioSetup={true}
        personaName=""
      />
      
      {isCustomModalOpen && (
        <CustomScenarioModal
          onSubmit={handleCustomScenarioSubmit}
          onClose={handleCustomModalClose}
        />
      )}
    </>
  );
};
