import { useEffect, useRef } from 'react';

export const useAutoScroll = (dependency: any) => {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ref.current) {
      setTimeout(() => {
        ref.current?.scrollTo({
          top: ref.current.scrollHeight,
          behavior: 'smooth'
        });
      }, 0);
    }
  }, [dependency]);

  return ref;
};
