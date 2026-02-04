interface CreateSessionRequest {
  user_id: string;
  persona_name: string;
  role_description: string;
  difficulty?: number;
  metadata?: Record<string, any>;
}

interface SessionResponse {
  session_id: string;
  user_id: string;
  status: string;
  persona_name: string;
  role_description: string;
  difficulty: number;
  created_at: string;
  message_count: number;
  metadata?: Record<string, any>;
}

interface StartAgentRequest {
  session_id: string;
  use_supervisor?: boolean;
}

interface StartAgentResponse {
  session_id: string;
  opening_message: string;
}

export const sessionService = {
  /**
   * 새 대화 세션 생성
   */
  async createSession(
    userId: string,
    personaName: string,
    roleDescription: string
  ): Promise<SessionResponse> {
    const response = await fetch('/api/v1/sessions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        persona_name: personaName,
        role_description: roleDescription,
        difficulty: 2,
        metadata: {},
      } as CreateSessionRequest),
    });

    if (!response.ok) {
      throw new Error(`Failed to create session: ${response.statusText}`);
    }

    return await response.json();
  },

  /**
   * AI 에이전트 시작 (첫 메시지 받기)
   */
  async startAgent(sessionId: string): Promise<StartAgentResponse> {
    const response = await fetch('/api/v1/agent/start', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        use_supervisor: false,
      } as StartAgentRequest),
    });

    if (!response.ok) {
      throw new Error(`Failed to start agent: ${response.statusText}`);
    }

    return await response.json();
  },
};
