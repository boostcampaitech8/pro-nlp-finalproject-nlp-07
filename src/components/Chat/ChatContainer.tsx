import React, { useRef, useEffect } from 'react';
import { MessageBubble } from './MessageBubble';
import { ScenarioSetup } from './ScenarioSetup';
import { TypingIndicator } from './TypingIndicator';
import { FeedbackView } from './FeedbackView';
import type { Message } from '../../types';
import type { SessionFeedback } from '../../types/feedback';
import './ChatContainer.css';

interface ChatContainerProps {
  messages: Message[];
  isWaitingForResponse: boolean;
  onSelectScenario: (persona: string, situation: string) => void;
  onCustomCreate: () => void;
  showScenarioSetup?: boolean;
  personaName?: string;
  showFeedback?: boolean;
  feedbackData?: SessionFeedback | null;
  // ❌ isLoading prop 제거됨
}

export const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  isWaitingForResponse,
  onSelectScenario,
  onCustomCreate,
  showScenarioSetup = false,
  personaName,
  showFeedback = false,
  feedbackData = null,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isWaitingForResponse]);

  // ✅ 시나리오 설정 화면
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

  // ✅ 피드백 화면
  if (showFeedback && feedbackData) {
    return (
      <div className="chat-container">
        <FeedbackView feedbackData={feedbackData} />
      </div>
    );
  }

  // ✅ 메시지가 없을 때 시나리오 설정 화면
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

  // ✅ 일반 채팅 화면
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
