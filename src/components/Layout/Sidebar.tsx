import React from 'react';
import { Logo } from '../Common/Logo';
import { ChatHistoryList } from '../ChatHistory/ChatHistoryList';
import type { Chat } from '../../types';

interface SidebarProps {
  chatHistories: Chat[];
  currentChatId: number | null;
  onSelectChat: (chatId: number) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  chatHistories,
  currentChatId,
  onSelectChat
}) => {
  return (
    <div className="sidebar">
      <div className="logo-section">
        <Logo />
      </div>
      <ChatHistoryList
        histories={chatHistories}
        currentChatId={currentChatId}
        onSelectChat={onSelectChat}
      />
    </div>
  );
};
