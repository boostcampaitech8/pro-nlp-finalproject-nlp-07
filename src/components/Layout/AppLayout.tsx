import React from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { ChatContainer } from '../Chat/ChatContainer';
import { MessageInput } from '../Input/MessageInput';
import type { Message, Chat } from '../../types';
import type { SessionFeedback } from '../../types/feedback'; // ✅ 다시 추가

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
  showFeedback?: boolean; // ✅ 다시 추가
  feedbackData?: SessionFeedback | null; // ✅ 다시 추가
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
  showFeedback = false, // ✅ 다시 추가
  feedbackData = null, // ✅ 다시 추가
}) => {
  const hasMessages = messages.length > 0;
  
  // ✅ 피드백 모드일 때 타이틀 변경
  const headerTitle = showFeedback 
    ? '대화 피드백'
    : personaName 
    ? `${personaName}와의 대화` 
    : 'AI Chatbot';

  return (
    <div className="app-container">
      <Sidebar
        chatHistories={chatHistories}
        currentChatId={currentChatId}
        onSelectChat={onSelectChat}
      />
      <div className="main-content">
        <Header
          title={showScenarioSetup ? '' : headerTitle}
          onEndChat={onEndChat}
          difficulty={difficulty}
          useSupervisor={useSupervisor}
          onDifficultyChange={onDifficultyChange}
          onSupervisorToggle={onSupervisorToggle}
          showActions={!showScenarioSetup && !showFeedback} // ✅ 피드백 모드에서는 액션 숨김
        />
        <ChatContainer
          messages={messages}
          isWaitingForResponse={isWaitingForResponse}
          onSelectScenario={onSelectScenario}
          onCustomCreate={onCustomCreate}
          showScenarioSetup={showScenarioSetup}
          personaName={personaName}
          isLoading={isLoading}
          showFeedback={showFeedback} // ✅ 다시 추가
          feedbackData={feedbackData} // ✅ 다시 추가
        />
        {!showScenarioSetup && !showFeedback && hasMessages && ( // ✅ 피드백 모드에서는 입력창 숨김
          <MessageInput
            value={inputValue}
            onChange={onInputChange}
            onSend={onSendMessage}
            disabled={isWaitingForResponse}
          />
        )}
      </div>
    </div>
  );
};
