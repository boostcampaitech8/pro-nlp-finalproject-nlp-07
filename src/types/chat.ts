import type { Message, Chat } from './index';

export interface ChatContextType {
  messages: Message[];
  currentChatId: number | null;
  chatHistories: Chat[];
  isWaitingForResponse: boolean;
  addMessage: (content: string, role: 'user' | 'assistant' | 'coach' | 'system') => void;
  createChat: (title: string) => Chat;
  loadChat: (chatId: number) => void;
  resetChat: () => void;
  setWaitingForResponse: (waiting: boolean) => void;
}
