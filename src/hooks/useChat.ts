import { useState, useCallback } from 'react';
import type { Message, Chat, Role } from '../types';

export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [chatHistories, setChatHistories] = useState<Chat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<number | null>(null);
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);

  const formatTimestamp = useCallback(() => {
    return new Date().toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit'
    });
  }, []);

  const addMessage = useCallback((content: string, role: Role) => {
    const timestamp = formatTimestamp();
    const message: Message = { content, role, timestamp };
    
    setMessages(prev => [...prev, message]);
    
    if (currentChatId) {
      setChatHistories(prev => 
        prev.map(chat => 
          chat.id === currentChatId
            ? { ...chat, messages: [...chat.messages, message] }
            : chat
        )
      );
    }
    
    return message;
  }, [currentChatId, formatTimestamp]);

  const createChat = useCallback((title: string) => {
    const chatId = Date.now();
    const newChat: Chat = { id: chatId, title, messages: [] };
    
    setChatHistories(prev => [...prev, newChat]);
    setCurrentChatId(chatId);
    setMessages([]);
    
    return newChat;
  }, []);

  const loadChat = useCallback((chatId: number) => {
    const chat = chatHistories.find(c => c.id === chatId);
    if (chat) {
      setCurrentChatId(chatId);
      setMessages([...chat.messages]);
    }
  }, [chatHistories]);

  const resetChat = useCallback(() => {
    setMessages([]);
    setCurrentChatId(null);
  }, []);

  return {
    messages,
    chatHistories,
    currentChatId,
    isWaitingForResponse,
    addMessage,
    createChat,
    loadChat,
    resetChat,
    setWaitingForResponse: setIsWaitingForResponse
  };
};
