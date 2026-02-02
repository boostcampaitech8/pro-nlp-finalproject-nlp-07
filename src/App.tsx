import React, { useState } from 'react';
import { AppLayout } from './components/Layout/AppLayout';
import { useChat } from './hooks/useChat';
import { chatService } from './services/chatService';
import { TITLE_MAX_LENGTH } from './constants/messages';
import './App.css';

const App: React.FC = () => {
  const [inputValue, setInputValue] = useState('');
  const [showCustomModal, setShowCustomModal] = useState(false);
  const chatState = useChat();

  // 시나리오 선택 핸들러 (프리셋)
  const handleSelectScenario = (persona: string, situation: string) => {
    const title = `${persona} 연습`;
    chatState.createChat(title);
    
    // 시스템 메시지로 시나리오 정보 표시 (선택 사항)
    const scenarioInfo = `📌 연습 시나리오\n상대방: ${persona}\n상황: ${situation}`;
    chatState.addMessage(scenarioInfo, 'system');
    
    // TODO: 백엔드에 시나리오 정보 전송
    // await chatService.setScenario(persona, situation);
  };

  // 커스텀 시나리오 생성 모달 열기
  const handleCustomCreate = () => {
    setShowCustomModal(true);
  };

  // 커스텀 시나리오 제출
  const handleCustomSubmit = (persona: string, situation: string) => {
    handleSelectScenario(persona, situation);
    setShowCustomModal(false);
  };

  const handleSendMessage = async () => {
    const messageText = inputValue.trim();
    if (!messageText || chatState.isWaitingForResponse) return;

    // 새 채팅 생성 (필요시)
    if (!chatState.currentChatId) {
      const title = messageText.length > TITLE_MAX_LENGTH
        ? messageText.substring(0, TITLE_MAX_LENGTH) + '...'
        : messageText;
      chatState.createChat(title);
    }

    // 사용자 메시지 추가
    chatState.addMessage(messageText, 'user');
    setInputValue('');

    // 로딩 상태
    chatState.setWaitingForResponse(true);

    try {
      // 실제 API 호출
      const result = await chatService.sendMessage(
        messageText,
        // chatState.currentChatId?.toString() || 'temp-session'
      );

      // Persona AI 응답 추가
      chatState.addMessage(result.response, 'assistant');

      // Coach AI 응답이 있으면 추가
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
  };

  const handleSelectChat = (chatId: number) => {
    chatState.loadChat(chatId);
  };

  const handleSettings = () => {
    console.log('Settings clicked');
  };

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

      {/* 커스텀 시나리오 생성 모달 */}
      {showCustomModal && (
        <CustomScenarioModal
          onSubmit={handleCustomSubmit}
          onClose={() => setShowCustomModal(false)}
        />
      )}
    </>
  );
};

// 커스텀 시나리오 모달 컴포넌트
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
