import React from 'react';

export const TypingIndicator: React.FC = () => {
  return (
    <div className="message assistant">
      <div className="typing-indicator">
        <div className="typing-dot"></div>
        <div className="typing-dot"></div>
        <div className="typing-dot"></div>
      </div>
    </div>
  );
};
