import React from 'react';
import { FeedbackStats } from '../Feedback/FeedbackStats';
import { CoachInterventions } from '../Feedback/CoachInterventions';
import { FinalSuggestions } from '../Feedback/FinalSuggestions';
import type { SessionFeedback } from '../../types/feedback';
import './FeedbackView.css';

interface FeedbackViewProps {
  feedbackData: SessionFeedback;
}

export const FeedbackView: React.FC<FeedbackViewProps> = ({ feedbackData }) => {
  return (
    <div className="feedback-view">
      <div className="feedback-view-header">
        <h1>✨ 대화 피드백</h1>
        <p>수고하셨습니다! 이번 대화를 분석한 결과입니다.</p>
      </div>

      <FeedbackStats
        personaName={feedbackData.persona_name}
        totalTurns={feedbackData.total_turns}
        coachInterventions={feedbackData.coach_interventions}
        interventionRate={feedbackData.intervention_rate}
      />

      <CoachInterventions interventions={feedbackData.interventions} />

      <FinalSuggestions finalFeedback={feedbackData.final_feedback} />
    </div>
  );
};
