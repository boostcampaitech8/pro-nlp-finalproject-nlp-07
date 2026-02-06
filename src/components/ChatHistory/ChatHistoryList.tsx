import React from 'react';
import type { Chat } from '../../types';
import { ChatHistoryItem } from './ChatHistoryItem';

interface ChatHistoryListProps {
  histories: Chat[];
  currentChatId: string | null;
  onSelectChat: (chatId: string) => void;
}

export const ChatHistoryList: React.FC<ChatHistoryListProps> = ({
  histories,
  currentChatId,
  onSelectChat
}) => {
  return (
    <div className="chat-history">
      <div className="chat-history-title">채팅 기록</div>
      <div id="chatHistory">
        {histories.map(chat => (
          <ChatHistoryItem
            key={chat.id}
            chat={chat}
            isActive={currentChatId === chat.id}
            onClick={onSelectChat}
          />
        ))}
      </div>
    </div>
  );
};
