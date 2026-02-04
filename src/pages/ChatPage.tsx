import React, { useState, useEffect, useRef, useCallback } from 'react';
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

// ✅ Debounce 함수
function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

export const ChatPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { persona, situation } = (location.state as LocationState) || {};

  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [personaName, setPersonaName] = useState<string>('상대방');
  
  const [difficulty, setDifficulty] = useState(2);
  const [useSupervisor, setUseSupervisor] = useState(false); // ✅ 기본값 false
  
  const chatState = useChat();
  const hasInitialized = useRef(false);

  // ✅ Debounced 난이도 업데이트 함수
  const debouncedUpdateDifficulty = useCallback(
    debounce(async (sessionId: string, level: number) => {
      try {
        await sessionService.updateDifficulty(sessionId, level);
        console.log('✅ Difficulty updated in DB:', level);
      } catch (error) {
        console.error('❌ Failed to update difficulty:', error);
      }
    }, 1000), // 1초 대기
    []
  );

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
      // ✅ useSupervisor 파라미터 전달
      console.log('Sending message with use_supervisor:', useSupervisor);
      const result = await chatService.sendMessage(sessionId, messageText, useSupervisor);
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

  // ✅ 난이도 변경 - Debounce로 DB 업데이트
  const handleDifficultyChange = (level: number) => {
    setDifficulty(level);
    console.log('🎯 Difficulty UI changed to:', level);
    
    if (sessionId) {
      debouncedUpdateDifficulty(sessionId, level);
    }
  };

  // ✅ 정밀 모드 토글 - 로컬 상태만 변경
  const handleSupervisorToggle = (enabled: boolean) => {
    setUseSupervisor(enabled);
    console.log('🔧 Supervisor toggled:', enabled);
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
      difficulty={difficulty}
      useSupervisor={useSupervisor}
      onDifficultyChange={handleDifficultyChange}
      onSupervisorToggle={handleSupervisorToggle}
      onEndChat={handleEndChat}
    />
  );
};
