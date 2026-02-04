import React from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { ChatContainer } from '../Chat/ChatContainer';
import { MessageInput } from '../Input/MessageInput';
import type { Message, Chat } from '../../types';

interface AppLayoutProps {
  messages: Message[];
  chatHistories: Chat[];
  currentChatId: number | null;
  isWaitingForResponse: boolean;
  inputValue: string;
  onInputChange: (value: string) => void;
  onSendMessage: () => void;
  onNewChat: () => void;
  onSelectChat: (chatId: number) => void;
  onSettings: () => void;
  onSelectScenario: (persona: string, situation: string) => void;
  onCustomCreate: () => void;
  showScenarioSetup?: boolean;
  personaName?: string;
  // ✅ 설정 관련 props 추가
  difficulty?: number;
  useSupervisor?: boolean;
  onDifficultyChange?: (level: number) => void;
  onSupervisorToggle?: (enabled: boolean) => void;
  onEndChat?: () => void;
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
  // ✅ 설정 관련 props 기본값
  difficulty = 2,
  useSupervisor = true,
  onDifficultyChange = () => {},
  onSupervisorToggle = () => {},
  onEndChat = () => {},
}) => {
  const hasMessages = messages.length > 0;

  // ✅ 타이틀 결정
  const headerTitle = personaName ? `${personaName}와의 대화` : 'AI Chatbot';

  return (
    <div className="app-container">
      <Sidebar
        chatHistories={chatHistories}
        currentChatId={currentChatId}
        onSelectChat={onSelectChat}
      />
      <div className="main-content">
        {/* ✅ Header에 설정 props 전달 */}
        <Header
          title={headerTitle}
          onEndChat={onEndChat}
          difficulty={difficulty}
          useSupervisor={useSupervisor}
          onDifficultyChange={onDifficultyChange}
          onSupervisorToggle={onSupervisorToggle}
        />
        <ChatContainer
          messages={messages}
          isWaitingForResponse={isWaitingForResponse}
          onSelectScenario={onSelectScenario}
          onCustomCreate={onCustomCreate}
          showScenarioSetup={showScenarioSetup}
          personaName={personaName}
        />
        {/* ✅ 시나리오 화면이 아니고 메시지가 있을 때만 입력창 표시 */}
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
