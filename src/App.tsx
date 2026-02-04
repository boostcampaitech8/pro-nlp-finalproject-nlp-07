import React, { useState, useEffect } from 'react';
import { AppLayout } from './components/Layout/AppLayout';
import { useChat } from './hooks/useChat';
import { chatService } from './services/chatService';
import { userService } from './services/userService';
import { sessionService } from './services/sessionService'; // ✅ 추가
import { TITLE_MAX_LENGTH } from './constants/messages';
import './App.css';

const App: React.FC = () => {
  const [inputValue, setInputValue] = useState('');
  const [showCustomModal, setShowCustomModal] = useState(false);
  const [userId, setUserId] = useState<string | null>(null);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null); // ✅ 추가
  const [isInitializing, setIsInitializing] = useState(true);
  const [isCreatingSession, setIsCreatingSession] = useState(false); // ✅ 추가
  const chatState = useChat();

  // 앱 시작 시 user_id 초기화
  useEffect(() => {
    let isMounted = true;

    const initializeUser = async () => {
      try {
        const id = await userService.initializeUserId();
        if (isMounted) {
          setUserId(id);
        }
      } catch (error) {
        console.error('Failed to initialize user:', error);
      } finally {
        if (isMounted) {
          setIsInitializing(false);
        }
      }
    };

    initializeUser();

    return () => {
      isMounted = false;
    };
  }, []);

  // ✅ 시나리오 선택 핸들러 (수정)
  const handleSelectScenario = async (persona: string, situation: string) => {
    if (!userId) {
      console.error('User ID not available');
      return;
    }

    setIsCreatingSession(true);

    try {
      // 1. 세션 생성
      console.log('Creating session...', { persona, situation });
      const sessionResponse = await sessionService.createSession(
        userId,
        persona,
        situation
      );
      
      console.log('Session created:', sessionResponse);
      setCurrentSessionId(sessionResponse.session_id);

      // 2. 채팅 생성 (UI)
      const title = `${persona} 연습`;
      chatState.createChat(title);

      // 3. 시스템 메시지 추가
      const scenarioInfo = `📌 연습 시나리오\n상대방: ${persona}\n상황: ${situation}`;
      chatState.addMessage(scenarioInfo, 'system');

      // 4. AI 에이전트 시작
      console.log('Starting agent...');
      const agentResponse = await sessionService.startAgent(sessionResponse.session_id);
      
      console.log('Agent started:', agentResponse);

      // 5. AI의 첫 메시지 추가
      chatState.addMessage(agentResponse.opening_message, 'assistant');

    } catch (error) {
      console.error('Failed to create session or start agent:', error);
      chatState.addMessage(
        '세션 생성에 실패했습니다. 다시 시도해주세요.',
        'system'
      );
    } finally {
      setIsCreatingSession(false);
    }
  };

  const handleCustomCreate = () => {
    setShowCustomModal(true);
  };

  const handleCustomSubmit = (persona: string, situation: string) => {
    handleSelectScenario(persona, situation);
    setShowCustomModal(false);
  };

  const handleSendMessage = async () => {
    const messageText = inputValue.trim();
    if (!messageText || chatState.isWaitingForResponse || !currentSessionId) return; // ✅ currentSessionId 체크

    if (!chatState.currentChatId) {
      const title = messageText.length > TITLE_MAX_LENGTH
        ? messageText.substring(0, TITLE_MAX_LENGTH) + '...'
        : messageText;
      chatState.createChat(title);
    }

    chatState.addMessage(messageText, 'user');
    setInputValue('');
    chatState.setWaitingForResponse(true);

    try {
      // TODO: chatService.sendMessage에 session_id 전달
      const result = await chatService.sendMessage(messageText);

      chatState.addMessage(result.response, 'assistant');

      if (result.coachFeedback) {
        chatState.addMessage(result.coachFeedback, 'coach');
      }
    } catch (error) {
      console.error('Failed to get response:', error);
      chatState.addMessage('죄송합니다. 오류가 발생했습니다.', 'assistant');
    } finally {
      chatState.setWaitingForResponse(false);
    }
  };

  const handleNewChat = () => {
    chatState.resetChat();
    setInputValue('');
    setCurrentSessionId(null); // ✅ 세션 초기화
  };

  const handleSelectChat = (chatId: number) => {
    chatState.loadChat(chatId);
  };

  const handleSettings = () => {
    console.log('Settings clicked');
  };

  // ✅ 로딩 컴포넌트
  const LoadingScreen: React.FC<{ message: string }> = ({ message }) => (
    <div className="loading-screen">
      <div className="loading-content">
        <div className="loading-dots">
          <div className="dot"></div>
          <div className="dot"></div>
          <div className="dot"></div>
          <div className="dot"></div>
          <div className="dot"></div>
        </div>
        <div className="loading-text">{message}</div>
      </div>
    </div>
  );

  if (isInitializing) {
    return <LoadingScreen message="초기화 중..." />;
  }

  if (isCreatingSession) {
    return <LoadingScreen message="대화 준비 중..." />;
  }

  return (
    <>
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
        onSelectScenario={handleSelectScenario}
        onCustomCreate={handleCustomCreate}
      />

      {showCustomModal && (
        <CustomScenarioModal
          onSubmit={handleCustomSubmit}
          onClose={() => setShowCustomModal(false)}
        />
      )}
    </>
  );
};

// CustomScenarioModal 컴포넌트 (기존과 동일)
interface CustomScenarioModalProps {
  onSubmit: (persona: string, situation: string) => void;
  onClose: () => void;
}

const CustomScenarioModal: React.FC<CustomScenarioModalProps> = ({ onSubmit, onClose }) => {
  const [persona, setPersona] = useState('');
  const [situation, setSituation] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (persona.trim() && situation.trim()) {
      onSubmit(persona.trim(), situation.trim());
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>✏️ 직접 시나리오 만들기</h2>
          <button className="modal-close-btn" onClick={onClose}>✕</button>
        </div>
        
        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label htmlFor="persona">상대방</label>
            <input
              id="persona"
              type="text"
              className="form-control"
              value={persona}
              onChange={(e) => setPersona(e.target.value)}
              placeholder="예: 까다로운 상사, 화난 고객, 동료"
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="situation">상황</label>
            <textarea
              id="situation"
              className="form-control"
              value={situation}
              onChange={(e) => setSituation(e.target.value)}
              placeholder="예: 프로젝트 지연 사과, 제품 불만 처리, 업무 협조 요청"
              rows={4}
            />
          </div>

          <div className="modal-actions">
            <button type="button" className="btn btn--secondary" onClick={onClose}>
              취소
            </button>
            <button 
              type="submit" 
              className="btn btn--primary"
              disabled={!persona.trim() || !situation.trim()}
            >
              대화 시작
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default App;
