import React, { useRef, useEffect } from 'react';
import { MessageBubble } from './MessageBubble';
import { ScenarioSetup } from './ScenarioSetup';
import { TypingIndicator } from './TypingIndicator';
import type { Message } from '../../types';
import './ChatContainer.css';

interface ChatContainerProps {
  messages: Message[];
  isWaitingForResponse: boolean;
  onSelectScenario: (persona: string, situation: string) => void;
  onCustomCreate: () => void;
  showScenarioSetup?: boolean;
  personaName?: string;
  isLoading?: boolean; // ✅ 로딩 prop 추가
}

export const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  isWaitingForResponse,
  onSelectScenario,
  onCustomCreate,
  showScenarioSetup = false,
  personaName,
  isLoading = false, // ✅ 기본값 false
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isWaitingForResponse]);

  if (showScenarioSetup) {
    return (
      <div className="chat-container">
        <ScenarioSetup
          onSelectScenario={onSelectScenario}
          onCustomCreate={onCustomCreate}
        />
      </div>
    );
  }

  // ✅ 로딩 중일 때 로딩 표시
  if (isLoading) {
    return (
      <div className="chat-container">
        <div className="chat-loading">
          <div className="loading-spinner"></div>
          <p>대화를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div className="chat-container">
        <ScenarioSetup
          onSelectScenario={onSelectScenario}
          onCustomCreate={onCustomCreate}
        />
      </div>
    );
  }

  return (
    <div className="chat-container">
      {messages.map((message, index) => (
        <MessageBubble 
          key={index} 
          message={message} 
          personaName={personaName}
        />
      ))}
      {isWaitingForResponse && <TypingIndicator />}
      <div ref={messagesEndRef} />
    </div>
  );
};
