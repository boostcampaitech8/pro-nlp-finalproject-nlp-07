import React from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { ChatContainer } from '../Chat/ChatContainer';
import { MessageInput } from '../Input/MessageInput';
import type { Message, Chat } from '../../types';

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
  isLoading?: boolean; // ✅ 로딩 prop 추가
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
  isLoading = false, // ✅ 기본값 false
}) => {
  const hasMessages = messages.length > 0;
  const headerTitle = personaName ? `${personaName}와의 대화` : 'AI Chatbot';

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
          showActions={!showScenarioSetup}
        />
        <ChatContainer
          messages={messages}
          isWaitingForResponse={isWaitingForResponse}
          onSelectScenario={onSelectScenario}
          onCustomCreate={onCustomCreate}
          showScenarioSetup={showScenarioSetup}
          personaName={personaName}
          isLoading={isLoading} // ✅ 로딩 전달
        />
        {!showScenarioSetup && hasMessages && (
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
