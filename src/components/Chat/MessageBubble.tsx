import React from 'react';
import type { Message } from '../../types';

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const isCoach = message.role === 'coach';
  const isSystem = message.role === 'system';

  // 시스템 메시지는 별도 스타일
  if (isSystem) {
    return (
      <div className="system-message">
        <div className="system-message-content">
          {message.content.split('\n').map((line, i) => (
            <div key={i}>{line}</div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={`message-bubble ${
      isUser ? 'user' : 
      isCoach ? 'coach' : 
      'assistant'
    }`}>
      {isCoach && <div className="coach-badge">💡 코치</div>}
      <div className="message-content">{message.content}</div>
    </div>
  );
};
