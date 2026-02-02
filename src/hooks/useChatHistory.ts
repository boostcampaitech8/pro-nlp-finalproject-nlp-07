import { useState, useCallback } from 'react';
import type { Chat } from '../types';

export const useChatHistory = () => {
  const [chatHistories, setChatHistories] = useState<Chat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<number | null>(null);

  const addToHistory = useCallback((chat: Chat) => {
    setChatHistories(prev => [...prev, chat]);
    setCurrentChatId(chat.id);
  }, []);

  const removeFromHistory = useCallback((chatId: number) => {
    setChatHistories(prev => prev.filter(chat => chat.id !== chatId));
    if (currentChatId === chatId) {
      setCurrentChatId(null);
    }
  }, [currentChatId]);

  return {
    chatHistories,
    currentChatId,
    addToHistory,
    removeFromHistory,
    setCurrentChatId
  };
};
