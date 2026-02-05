import React from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { ChatContainer } from '../Chat/ChatContainer';
import { MessageInput } from '../Input/MessageInput';
import { LoadingScreen } from '../Common/LoadingScreen';
import type { Message, Chat } from '../../types';
import type { SessionFeedback } from '../../types/feedback';
import './AppLayout.css';

interface AppLayoutProps {
  messages: Message[];
  chatHistories: Chat[];
  currentChatId: string | null;
  isWaitingForResponse: boolean;
  inputValue: string;
  onInputChange: (value: string) => void;
  onSendMessage: () => void;
  onNewChat: () => void;
  onSelectChat: (sessionId: string) => void;
  onSettings: () => void;
  onSelectScenario: (persona: string, situation: string) => void;
  onCustomCreate: () => void;
  showScenarioSetup?: boolean;
  personaName?: string;
  difficulty?: number;
  useSupervisor?: boolean;
  onDifficultyChange?: (level: number) => void;
  onSupervisorToggle?: (enabled: boolean) => void;
  onEndChat?: () => void;
  isLoading?: boolean;
  showFeedback?: boolean;
  feedbackData?: SessionFeedback | null;
  isEndingSession?: boolean;
  loadingMessage?: string;
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  messages,
  chatHistories,
  currentChatId,
  isWaitingForResponse,
  inputValue,
  onInputChange,
  onSendMessage,
  onSelectChat,
  onSelectScenario,
  onCustomCreate,
  showScenarioSetup = false,
  personaName,
  difficulty = 2,
  useSupervisor = true,
  onDifficultyChange = () => {},
  onSupervisorToggle = () => {},
  onEndChat = () => {},
  isLoading = false,
  showFeedback = false,
  feedbackData = null,
  isEndingSession = false,
  loadingMessage,
}) => {
  const hasMessages = messages.length > 0;
  
  const headerTitle = showFeedback 
    ? '대화 피드백'
    : personaName 
    ? `${personaName}와의 대화` 
    : 'AI Chatbot';

  const showLoadingOverlay = isLoading || isEndingSession;
  
  const getLoadingMessage = (): string => {
    if (loadingMessage) {
      return loadingMessage;
    }
    
    if (isEndingSession) {
      return '피드백을 생성하고 있습니다';
    }
    
    if (isLoading) {
      return '대화를 불러오고 있습니다';
    }
    
    return '로딩 중입니다';
  };

  return (
    <div className="app-container">
      <Sidebar
        chatHistories={chatHistories}
        currentChatId={currentChatId}
        onSelectChat={onSelectChat}
      />
      <div className="main-content">
        {/* ✅ 헤더는 로딩 오버레이 밖에 */}
        <Header
          title={showScenarioSetup ? '' : headerTitle}
          onEndChat={onEndChat}
          difficulty={difficulty}
          useSupervisor={useSupervisor}
          onDifficultyChange={onDifficultyChange}
          onSupervisorToggle={onSupervisorToggle}
          showActions={!showScenarioSetup && !showFeedback}
        />
        
        <div className={`chat-area-wrapper ${showLoadingOverlay ? 'loading-active' : ''}`}>
          {showLoadingOverlay && (
            <LoadingScreen message={getLoadingMessage()} />
          )}
          
          <ChatContainer
            messages={messages}
            isWaitingForResponse={isWaitingForResponse}
            onSelectScenario={onSelectScenario}
            onCustomCreate={onCustomCreate}
            showScenarioSetup={showScenarioSetup}
            personaName={personaName}
            showFeedback={showFeedback}
            feedbackData={feedbackData}
          />
          
          {!showScenarioSetup && !showFeedback && hasMessages && !showLoadingOverlay && (
            <MessageInput
              value={inputValue}
              onChange={onInputChange}
              onSend={onSendMessage}
              disabled={isWaitingForResponse}
            />
          )}
        </div>
      </div>
    </div>
  );
};
