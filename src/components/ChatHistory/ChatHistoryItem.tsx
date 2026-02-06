import React from 'react';
import type { Chat } from '../../types';

interface ChatHistoryItemProps {
  chat: Chat;
  isActive: boolean;
  onClick: (chatId: string) => void;
}

export const ChatHistoryItem: React.FC<ChatHistoryItemProps> = ({
  chat,
  isActive,
  onClick
}) => {
  return (
    <button
      className={`chat-history-item ${isActive ? 'active' : ''}`}
      onClick={() => onClick(chat.id)}
    >
      {chat.title}
    </button>
  );
};
