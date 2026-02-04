export type Role = 'user' | 'assistant' | 'coach' | 'system';

export interface Message {
  id?: number;
  content: string;
  role: Role;
  timestamp: string;
}

// ✅ Chat 타입 수정
export interface Chat {
  id: string; // ✅ number → string (session_id 사용)
  title: string;
  messages?: Message[]; // ✅ optional로 변경
  messageCount?: number; // ✅ 추가
  timestamp?: Date; // ✅ 추가
}

export interface ChatState {
  messages: Message[];
  currentChatId: number | null;
  isWaitingForResponse: boolean;
}
