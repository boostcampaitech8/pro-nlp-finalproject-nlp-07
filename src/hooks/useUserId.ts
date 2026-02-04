import { useState, useEffect } from 'react';
import { userService } from '../services/userService';

export const useUserId = () => {
  const [userId, setUserId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const initUserId = async () => {
      try {
        setIsLoading(true);
        const id = await userService.initializeUserId();
        setUserId(id);
      } catch (err) {
        setError(err as Error);
        console.error('Failed to initialize user ID:', err);
      } finally {
        setIsLoading(false);
      }
    };

    initUserId();
  }, []);

  return { userId, isLoading, error };
};
