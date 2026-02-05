import { useState } from 'react';
import type { Message, Chat } from '../types';
 
interface UseChatReturn {
  messages: Message[];
  chatHistories: Chat[];
  currentChatId: string | null;
  isWaitingForResponse: boolean;
  addMessage: (content: string, role: Message['role']) => void;
  createChat: (title: string) => void;
  loadChat: (chatId: string) => void;
  setWaitingForResponse: (waiting: boolean) => void;
}

export const useChat = (): UseChatReturn => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [chatHistories, setChatHistories] = useState<Chat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);

  const addMessage = (content: string, role: Message['role']) => {
    const newMessage: Message = {
      id: Date.now(),
      content,
      role,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, newMessage]);
  };

  const createChat = (title: string) => {
    const newChat: Chat = {
      id: `chat_${Date.now()}`,
      title,
      messages: [],
      messageCount: 0,
      timestamp: new Date(),
    };
    setChatHistories((prev) => [newChat, ...prev]);
    setCurrentChatId(newChat.id);
  };

  const loadChat = (chatId: string) => {
    const chat = chatHistories.find((c) => c.id === chatId);
    if (chat && chat.messages) {
      setMessages(chat.messages);
      setCurrentChatId(chatId);
    }
  };

  // ✅ setWaitingForResponse를 setIsWaitingForResponse로 매핑
  const setWaitingForResponse = (waiting: boolean) => {
    setIsWaitingForResponse(waiting);
  };

  return {
    messages,
    chatHistories,
    currentChatId,
    isWaitingForResponse,
    addMessage,
    createChat,
    loadChat,
    setWaitingForResponse,
  };
};
