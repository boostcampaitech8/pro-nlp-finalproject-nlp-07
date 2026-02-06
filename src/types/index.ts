export type Role = 'user' | 'assistant' | 'coach' | 'system';

export interface Message {
  id?: number;
  content: string;
  role: Role;
  timestamp: string;
}

export interface Chat {
  id: string;
  title: string;
  timestamp: Date;
  messageCount: number;
  roleDescription?: string;
  messages?: Message[];
}

export interface ChatState {
  messages: Message[];
  currentChatId: number | null;
  isWaitingForResponse: boolean;
}
