import React from 'react';
import type { Message } from '../../types';
import './MessageBubble.css';

interface MessageBubbleProps {
  message: Message;
  personaName?: string;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ 
  message, 
  personaName = '상대방' 
}) => {
  const isUser = message.role === 'user';
  const isCoach = message.role === 'coach';
  const isSystem = message.role === 'system';
  const isAssistant = message.role === 'assistant';

  // 코치 메시지는 시스템 스타일로 표시
  if (isCoach) {
    return (
      <div className="system-message coach">
        <div className="system-message-content">
          <div>💡 코치의 조언</div>
          {message.content.split('\n').map((line, i) => (
            <div key={i}>{line}</div>
          ))}
        </div>
      </div>
    );
  }

  // 시스템 메시지
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

  // 일반 메시지
  return (
    <div className={`message-bubble ${isUser ? 'user' : 'assistant'}`}>
      {/* ✅ 사용자도 라벨 표시 */}
      {isUser && (
        <div className="user-badge">나</div>
      )}
      {/* 페르소나 라벨 */}
      {isAssistant && (
        <div className="persona-badge">{personaName}</div>
      )}
      <div className="message-content">{message.content}</div>
    </div>
  );
};
