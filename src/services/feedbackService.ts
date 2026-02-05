import { userService } from './userService';
import type { SessionFeedback } from '../types/feedback';

export const feedbackService = {
  /**
   * 세션 피드백 조회
   */
  async getSessionFeedback(sessionId: string): Promise<SessionFeedback> {
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
};
