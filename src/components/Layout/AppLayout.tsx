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
}


export const AppLayout: React.FC<AppLayoutProps> = ({
  messages,
  chatHistories,
  currentChatId,
  isWaitingForResponse,
  inputValue,
  onInputChange,
  onSendMessage,
  onNewChat,
  onSelectChat,
  onSettings,
  onSelectScenario,
  onCustomCreate,
}) => {
  const hasMessages = messages.length > 0;

  return (
    <div className="app-container">
      <Sidebar
        chatHistories={chatHistories}
        currentChatId={currentChatId}
        onSelectChat={onSelectChat}
      />
      <div className="main-content">
        <Header
          title="AI Chatbot"
          onNewChat={onNewChat}
          onSettings={onSettings}
        />
        <ChatContainer
          messages={messages}
          isWaitingForResponse={isWaitingForResponse}
          onSelectScenario={onSelectScenario}
          onCustomCreate={onCustomCreate}
        />
        {/* ✅ 메시지가 있을 때만 입력창 표시 */}
        {hasMessages && (
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
