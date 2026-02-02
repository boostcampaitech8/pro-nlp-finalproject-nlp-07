// src/services/chatService.ts

interface ChatResponse {
  response: string;
  success: boolean;
  error?: string;
  coachFeedback?: string;
}

export const chatService = {
  // API 엔드포인트 URL
  CHAT_ENDPOINT: '/api/v1/agent',

  // 채팅 메시지 전송
  async sendMessage(message: string): Promise<ChatResponse> {
    try {
      const response = await fetch(this.CHAT_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          "message": message
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      return {
        response: data.response || data.message,
        success: true
      };
    } catch (error) {
      console.error('Chat API Error:', error);
      return {
        response: '죄송합니다. 응답을 가져오는데 실패했습니다.',
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
};
