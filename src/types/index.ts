export type Role = 'user' | 'assistant' | 'coach' | 'system';

export interface Message {
  content: string;
  role: Role;
  timestamp: string;
}

export interface Chat {
  id: number;
  title: string;
  messages: Message[];
}

export interface ChatState {
  messages: Message[];
  currentChatId: number | null;
  isWaitingForResponse: boolean;
}
