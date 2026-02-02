// src/components/Chat/ChatContainer.tsx
import React from 'react';
import type { Message } from '../../types';
import { MessageBubble } from './MessageBubble';
import { ScenarioSetup } from './ScenarioSetup';
import { TypingIndicator } from './TypingIndicator';
import { useAutoScroll } from '../../hooks/useAutoScroll';

interface ChatContainerProps {
  messages: Message[];
  isWaitingForResponse: boolean;
  onSelectScenario: (persona: string, situation: string) => void;
  onCustomCreate: () => void;
}

export const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  isWaitingForResponse,
  onSelectScenario,
  onCustomCreate
}) => {
  const ref = useAutoScroll(messages.length);

  return (
    <div className="chat-container" ref={ref}>
      {messages.length === 0 ? (
        <ScenarioSetup 
          onSelectScenario={onSelectScenario}
          onCustomCreate={onCustomCreate}
        />
      ) : (
        <>
          {messages.map((msg, idx) => (
            <MessageBubble key={idx} message={msg} />
          ))}
          {isWaitingForResponse && <TypingIndicator />}
        </>
      )}
    </div>
  );
};
