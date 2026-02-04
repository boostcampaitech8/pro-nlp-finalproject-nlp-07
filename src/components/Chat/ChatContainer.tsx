import React, { useEffect, useRef } from 'react';
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
}


export const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  isWaitingForResponse,
  onSelectScenario,
  onCustomCreate,
  showScenarioSetup = false,
  personaName,
}) => {
  // ✅ 오토스크롤을 위한 ref
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // ✅ 메시지가 변경될 때마다 스크롤
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
      {/* ✅ 스크롤 타겟 */}
      <div ref={messagesEndRef} />
    </div>
  );
};
