import { userService } from './userService';

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

interface UpdateDifficultyRequest {
  difficulty: number;
}

interface SessionListItem {
  session_id: string;
  persona_name: string;
  difficulty: number;
  status: string;
  created_at: string;
  message_count: number;
}

interface UserSessionsResponse {
  user_id: string;
  total_sessions: number;
  sessions: SessionListItem[];
}

interface SessionMessage {
  message_id: string;
  session_id: string;
  role: 'system' | 'persona' | 'user' | 'coach';
  content: string;
  timestamp: string;
  metadata?: {
    signals?: string[];
    [key: string]: any;
  };
}

interface SessionMessagesResponse {
  session_id: string;
  persona_name: string;
  role_description: string;
  difficulty: number;
  status: string;
  total_messages: number;
  messages: SessionMessage[];
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
    const userId = userService.getUserId();
    
    const response = await fetch('/api/v1/agent/start', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        use_supervisor: false,
        user_id: userId,
      } as StartAgentRequest),
    });

    if (!response.ok) {
      throw new Error(`Failed to start agent: ${response.statusText}`);
    }

    return await response.json();
  },

  /**
   * 난이도 업데이트
   */
  async updateDifficulty(sessionId: string, difficulty: number): Promise<void> {
    const userId = userService.getUserId();
    
    const response = await fetch(`/api/v1/sessions/${sessionId}/difficulty?user_id=${userId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        difficulty,
      } as UpdateDifficultyRequest),
    });

    if (!response.ok) {
      throw new Error(`Failed to update difficulty: ${response.statusText}`);
    }

    return await response.json();
  },

  /**
   * 사용자 세션 목록 조회
   */
  async getUserSessions(userId: string): Promise<UserSessionsResponse> {
    const response = await fetch(`/api/v1/sessions/user/${userId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get user sessions: ${response.statusText}`);
    }

    return await response.json();
  },

  /**
   * 세션의 모든 메시지 조회
   */
  async getSessionMessages(sessionId: string): Promise<SessionMessagesResponse> {
    const userId = userService.getUserId();
    
    const response = await fetch(`/api/v1/sessions/${sessionId}/messages?user_id=${userId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get session messages: ${response.statusText}`);
    }

    return await response.json();
  },

  /**
   * 세션 종료 및 평가
   */
  async endSession(sessionId: string, userRating: number): Promise<{
    session_id: string;
    status: string;
    ended_at: string;
    message: string;
    feedback_generated: boolean;
  }> {
    try {
      const userId = userService.getUserId();
      
      const response = await fetch(`/api/v1/sessions/${sessionId}/end`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_rating: userRating,
          user_id: userId,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to end session: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error ending session:', error);
      throw error;
    }
  },

  /**
   * 세션 피드백 조회
   */
  async getFeedback(sessionId: string): Promise<{
    session_id: string;
    final_feedback: any;
    generated_at: string;
  }> {
    try {
      const userId = userService.getUserId();
      
      const response = await fetch(`/api/v1/feedback/${sessionId}?user_id=${userId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to get feedback: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error getting feedback:', error);
      throw error;
    }
  },

  /**
   * 세션 정보 조회
   */
  async getSession(sessionId: string) {
    const userId = userService.getUserId();
    
    const response = await fetch(`/api/v1/sessions/${sessionId}?user_id=${userId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to get session');
    }

    return response.json();
  },

  /**
   * 세션 삭제
   */
  async deleteSession(sessionId: string) {
    const userId = userService.getUserId();
    
    const response = await fetch(`/api/v1/sessions/${sessionId}?user_id=${userId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to delete session');
    }

    if (response.status === 204) {
      return { success: true, message: 'Session deleted successfully' };
    }

    return response.json();
  }
};
