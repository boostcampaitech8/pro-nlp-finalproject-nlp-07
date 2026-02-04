import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { AppLayout } from '../components/Layout/AppLayout';
import { LoadingScreen } from '../components/Common/LoadingScreen';
import { useChat } from '../hooks/useChat';
import { chatService } from '../services/chatService';
import { sessionService } from '../services/sessionService';

interface LocationState {
  persona?: string;
  situation?: string;
}

export const ChatPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { persona, situation } = (location.state as LocationState) || {};

  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [personaName, setPersonaName] = useState<string>('상대방');
  
  // ✅ 설정 상태 유지
  const [difficulty, setDifficulty] = useState(2);
  const [useSupervisor, setUseSupervisor] = useState(true);
  
  const chatState = useChat();
  const hasInitialized = useRef(false);

  useEffect(() => {
    if (hasInitialized.current) {
      return;
    }

    const initChat = async () => {
      if (!sessionId) {
        console.error('No session ID found');
        navigate('/');
        return;
      }

      hasInitialized.current = true;

      try {
        console.log('Initializing chat with session:', sessionId);

        if (persona) {
          setPersonaName(persona);
        }

        const title = persona ? `${persona} 연습` : '새 대화';
        chatState.createChat(title);

        if (persona && situation) {
          const scenarioInfo = `📌 연습 시나리오\n상대방: ${persona}\n상황: ${situation}`;
          chatState.addMessage(scenarioInfo, 'system');
        }

        console.log('Starting agent...');
        const agentResponse = await sessionService.startAgent(sessionId);
        console.log('Agent started:', agentResponse);

        chatState.addMessage(agentResponse.opening_message, 'assistant');
      } catch (error) {
        console.error('Failed to initialize chat:', error);
        chatState.addMessage(
          '대화 시작에 실패했습니다. 홈으로 돌아가 다시 시도해주세요.',
          'system'
        );
        hasInitialized.current = false;
      } finally {
        setIsLoading(false);
      }
    };

    initChat();
  }, [sessionId]);

  const handleSendMessage = async () => {
    const messageText = inputValue.trim();
    if (!messageText || chatState.isWaitingForResponse || !sessionId) return;

    chatState.addMessage(messageText, 'user');
    setInputValue('');
    chatState.setWaitingForResponse(true);

    try {
      const result = await chatService.sendMessage(sessionId, messageText);
      console.log('Received response:', result);

      chatState.addMessage(result.response, 'assistant');

      if (result.coachFeedback) {
        chatState.addMessage(result.coachFeedback, 'coach');
      }
    } catch (error) {
      console.error('Failed to get response:', error);
      chatState.addMessage(
        '죄송합니다. 응답을 받는 중 오류가 발생했습니다. 다시 시도해주세요.',
        'system'
      );
    } finally {
      chatState.setWaitingForResponse(false);
    }
  };

  const handleDifficultyChange = async (level: number) => {
    setDifficulty(level);
    console.log('Difficulty changed to:', level);
    // TODO: API 호출
  };

  const handleSupervisorToggle = async (enabled: boolean) => {
    setUseSupervisor(enabled);
    console.log('Supervisor toggled:', enabled);
    // TODO: API 호출
  };

  const handleEndChat = () => {
    if (window.confirm('대화를 종료하고 홈으로 돌아가시겠습니까?')) {
      navigate('/');
    }
  };

  const handleNewChat = () => {
    navigate('/');
  };

  const handleSelectChat = (chatId: number) => {
    chatState.loadChat(chatId);
  };

  const handleSettings = () => {
    console.log('Settings clicked');
  };

  if (isLoading) {
    return <LoadingScreen message="대화 불러오는 중..." />;
  }

  return (
    <AppLayout
      messages={chatState.messages}
      chatHistories={chatState.chatHistories}
      currentChatId={chatState.currentChatId}
      isWaitingForResponse={chatState.isWaitingForResponse}
      inputValue={inputValue}
      onInputChange={setInputValue}
      onSendMessage={handleSendMessage}
      onNewChat={handleNewChat}
      onSelectChat={handleSelectChat}
      onSettings={handleSettings}
      onSelectScenario={() => {}}
      onCustomCreate={() => {}}
      showScenarioSetup={false}
      personaName={personaName}
      // ✅ 설정 props 전달 (AppLayout에서 사용할 수 있도록)
      difficulty={difficulty}
      useSupervisor={useSupervisor}
      onDifficultyChange={handleDifficultyChange}
      onSupervisorToggle={handleSupervisorToggle}
      onEndChat={handleEndChat}
    />
  );
};
