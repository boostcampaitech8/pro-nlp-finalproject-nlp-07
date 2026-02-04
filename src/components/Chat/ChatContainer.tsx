import React, { useRef, useEffect } from 'react';
import { MessageBubble } from './MessageBubble';
import { ScenarioSetup } from './ScenarioSetup';
import { TypingIndicator } from './TypingIndicator';
import { FeedbackView } from './FeedbackView'; // ✅ 다시 추가
import type { Message } from '../../types';
import type { SessionFeedback } from '../../types/feedback'; // ✅ 다시 추가
import './ChatContainer.css';

interface ChatContainerProps {
  messages: Message[];
  isWaitingForResponse: boolean;
  onSelectScenario: (persona: string, situation: string) => void;
  onCustomCreate: () => void;
  showScenarioSetup?: boolean;
  personaName?: string;
  isLoading?: boolean;
  showFeedback?: boolean; // ✅ 다시 추가
  feedbackData?: SessionFeedback | null; // ✅ 다시 추가
}

export const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  isWaitingForResponse,
  onSelectScenario,
  onCustomCreate,
  showScenarioSetup = false,
  personaName,
  isLoading = false,
  showFeedback = false, // ✅ 다시 추가
  feedbackData = null, // ✅ 다시 추가
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

  // ✅ 피드백 표시
  if (showFeedback && feedbackData) {
    return (
      <div className="chat-container">
        <FeedbackView feedbackData={feedbackData} />
      </div>
    );
  }

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
