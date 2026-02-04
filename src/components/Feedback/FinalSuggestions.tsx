import React from 'react';
import type { FinalFeedback } from '../../types/feedback';
import './FinalSuggestions.css';

interface FinalSuggestionsProps {
  finalFeedback: FinalFeedback;
}

export const FinalSuggestions: React.FC<FinalSuggestionsProps> = ({
  finalFeedback,
}) => {
  return (
    <div className="final-suggestions">
      <h2>🎯 최종 피드백</h2>
      <p className="suggestions-subtitle">
        이번 대화를 통해 개선할 수 있는 영역입니다
      </p>

      <div className="suggestions-list">
        {finalFeedback.suggestions.map((suggestion, index) => (
          <div key={suggestion.task} className="suggestion-card">
            <div className="suggestion-number">{index + 1}</div>
            <div className="suggestion-content">
              <h3 className="suggestion-title">{suggestion.description}</h3>
              <p className="suggestion-task">{suggestion.task}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
