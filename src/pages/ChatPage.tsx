import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { AppLayout } from '../components/Layout/AppLayout';
import { LoadingScreen } from '../components/Common/LoadingScreen';
import { useChat } from '../hooks/useChat';
import { chatService } from '../services/chatService';
import { sessionService } from '../services/sessionService';
import { userService } from '../services/userService';
import type { Chat } from '../types';

interface LocationState {
  persona?: string;
  situation?: string;
}

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
  const [useSupervisor, setUseSupervisor] = useState(false);
  
  const [chatHistories, setChatHistories] = useState<Chat[]>([]);
  
  const chatState = useChat();
  const hasInitialized = useRef(false);

  const userId = userService.getUserId() || '';

  const debouncedUpdateDifficulty = useCallback(
    debounce(async (sessionId: string, level: number) => {
      try {
        await sessionService.updateDifficulty(sessionId, level);
        console.log('✅ Difficulty updated in DB:', level);
      } catch (error) {
        console.error('❌ Failed to update difficulty:', error);
      }
    }, 1000),
    []
  );

  // 세션 목록 로드
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

        setChatHistories(chats);
      } catch (error) {
        console.error('Failed to load sessions:', error);
      }
    };

    loadSessions();
  }, [userId]);

  // ✅ 채팅 초기화 - 메시지 조회 먼저, 없으면 start
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

        // ✅ 1. 무조건 메시지 조회부터 시도
        try {
          const messagesData = await sessionService.getSessionMessages(sessionId);
          console.log('📂 Messages loaded:', messagesData);

          // ✅ 메시지가 있으면 표시
          if (messagesData.messages && messagesData.messages.length > 0) {
            setPersonaName(messagesData.persona_name);
            setDifficulty(messagesData.difficulty);

            const title = `${messagesData.persona_name} 연습`;
            chatState.createChat(title);

            // 메시지 변환 및 추가
            messagesData.messages.forEach((msg) => {
              if (msg.role === 'system' && msg.content === '[세션 시작]') {
                const scenarioInfo = `📌 연습 시나리오\n상대방: ${messagesData.persona_name}\n상황: ${messagesData.role_description}`;
                chatState.addMessage(scenarioInfo, 'system');
              } else if (msg.role === 'persona') {
                chatState.addMessage(msg.content, 'assistant');
              } else if (msg.role === 'user') {
                chatState.addMessage(msg.content, 'user');
              } else if (msg.role === 'coach') {
                chatState.addMessage(msg.content, 'coach');
              }
            });

            setIsLoading(false);
            return; // ✅ 메시지 있으면 여기서 종료
          }
        } catch (error) {
          console.log('⚠️ No messages found, will start new session');
        }

        // ✅ 2. 메시지가 없으면 start 호출
        if (!persona || !situation) {
          throw new Error('No scenario information for new session');
        }

        console.log('📌 Starting new session');
        
        setPersonaName(persona);
        const title = `${persona} 연습`;
        chatState.createChat(title);

        const scenarioInfo = `📌 연습 시나리오\n상대방: ${persona}\n상황: ${situation}`;
        chatState.addMessage(scenarioInfo, 'system');

        const agentResponse = await sessionService.startAgent(sessionId);
        console.log('Agent started:', agentResponse);

        chatState.addMessage(agentResponse.opening_message, 'assistant');

      } catch (error) {
        console.error('Failed to initialize chat:', error);
        chatState.addMessage(
          '대화를 불러오는데 실패했습니다. 홈으로 돌아가 다시 시도해주세요.',
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

  const handleDifficultyChange = (level: number) => {
    setDifficulty(level);
    console.log('🎯 Difficulty UI changed to:', level);
    
    if (sessionId) {
      debouncedUpdateDifficulty(sessionId, level);
    }
  };

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

  const handleSelectChat = (selectedSessionId: string) => {
    navigate(`/chat/${selectedSessionId}`);
    window.location.reload();
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
      chatHistories={chatHistories}
      currentChatId={sessionId || null}
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
