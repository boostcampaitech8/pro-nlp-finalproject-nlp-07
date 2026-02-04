interface SendMessageRequest {
  session_id: string;
  user_text: string;
  use_supervisor?: boolean;
}

// ✅ coach 응답 타입 정의
interface CoachResponse {
  intervene: boolean;
  rewrite: string;
  signals: string[];
}

interface SendMessageResponse {
  response: string;
  success: boolean;
  coach?: CoachResponse; // ✅ 타입 지정
  supervisor?: any;
}

export const chatService = {
  /**
   * 메시지 전송 및 AI 응답 받기
   */
  async sendMessage(
    sessionId: string,
    userText: string,
    useSupervisor: boolean = false
  ): Promise<{ response: string; coachFeedback?: string }> {
    try {
      const response = await fetch('/api/v1/agent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          user_text: userText,
          use_supervisor: useSupervisor,
        } as SendMessageRequest),
      });

      if (!response.ok) {
        throw new Error(`Failed to send message: ${response.statusText}`);
      }

      const data: SendMessageResponse = await response.json();

      console.log('Agent response:', data);

      // ✅ 코치 피드백 처리 - intervene이 true이고 rewrite가 있을 때만
      let coachFeedback: string | undefined;
      if (data.coach && data.coach.intervene && data.coach.rewrite) {
        console.log('Coach feedback received:', data.coach.rewrite);
        coachFeedback = data.coach.rewrite;
      }

      return {
        response: data.response,
        coachFeedback,
      };
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  },
};
