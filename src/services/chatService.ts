interface SendMessageRequest {
  session_id: string;
  user_text: string;
  use_supervisor?: boolean;
}

interface SendMessageResponse {
  response: string;
  success: boolean;
  coach?: any;
  supervisor?: any;
}

export const chatService = {
  /**
   * 메시지 전송 및 AI 응답 받기
   * ✅ useSupervisor 파라미터 추가
   */
  async sendMessage(
    sessionId: string,
    userText: string,
    useSupervisor: boolean = false // ✅ 기본값 false로 설정
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
          use_supervisor: useSupervisor, // ✅ 파라미터 사용
        } as SendMessageRequest),
      });

      if (!response.ok) {
        throw new Error(`Failed to send message: ${response.statusText}`);
      }

      const data: SendMessageResponse = await response.json();

      console.log('Agent response:', data);

      // 코치 피드백 처리
      let coachFeedback: string | undefined;
      if (data.coach && Object.keys(data.coach).length > 0) {
        console.log('Coach feedback received:', data.coach);
        // TODO: coach 데이터 형식 확인 후 처리
        // coachFeedback = data.coach.message; // 예시
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
