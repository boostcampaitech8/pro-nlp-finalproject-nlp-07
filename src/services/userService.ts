const USER_ID_KEY = 'mind_gym_user_id';

interface GenerateUserIdResponse {
  user_id: string;
  message: string;
}

// 요청 중복 방지를 위한 Promise 캐시
let initializationPromise: Promise<string> | null = null;

export const userService = {
  /**
   * localStorage에서 user_id 조회
   */
  getUserId(): string | null {
    return localStorage.getItem(USER_ID_KEY);
  },

  /**
   * localStorage에 user_id 저장
   */
  setUserId(userId: string): void {
    localStorage.setItem(USER_ID_KEY, userId);
  },

  /**
   * localStorage에서 user_id 제거
   */
  clearUserId(): void {
    localStorage.removeItem(USER_ID_KEY);
  },

  /**
   * 서버에서 새 user_id 생성
   */
  async generateUserId(): Promise<string> {
    const response = await fetch('/api/v1/users/generate-id', { // ✅ 상대 경로
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to generate user ID: ${response.statusText}`);
    }

    const data: GenerateUserIdResponse = await response.json();
    return data.user_id;
  },

  /**
   * user_id 초기화 (없으면 생성, 있으면 반환)
   */
  async initializeUserId(): Promise<string> {
    // 이미 초기화 중이면 같은 Promise 반환
    if (initializationPromise) {
      console.log('Already initializing, returning existing promise');
      return initializationPromise;
    }

    // 1. localStorage에서 조회
    const existingUserId = this.getUserId();
    
    if (existingUserId) {
      console.log('Existing user ID found:', existingUserId);
      return existingUserId;
    }

    // 2. Promise 생성 및 캐싱
    initializationPromise = (async () => {
      try {
        console.log('No user ID found, generating new one from server...');
        const newUserId = await this.generateUserId();
        this.setUserId(newUserId);
        console.log('New user ID generated and saved:', newUserId);
        return newUserId;
      } catch (error) {
        console.warn('Failed to fetch from server, generating local ID:', error);
        const localUserId = `anon_local_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        this.setUserId(localUserId);
        console.log('Local user ID generated:', localUserId);
        return localUserId;
      } finally {
        // 완료 후 캐시 초기화
        initializationPromise = null;
      }
    })();

    return initializationPromise;
  },
};
