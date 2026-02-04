import React from 'react';
import type { CoachIntervention } from '../../types/feedback';
import './CoachInterventions.css';

interface CoachInterventionsProps {
  interventions: CoachIntervention[];
}

export const CoachInterventions: React.FC<CoachInterventionsProps> = ({
  interventions,
}) => {
  if (interventions.length === 0) {
    return (
      <div className="coach-interventions">
        <h2>💡 코치 개입 내역</h2>
        <p className="no-interventions">코치가 개입한 내역이 없습니다. 훌륭해요! 🎉</p>
      </div>
    );
  }

  return (
    <div className="coach-interventions">
      <h2>💡 코치 개입 내역</h2>
      <p className="interventions-subtitle">
        코치가 개입했던 메시지와 피드백을 확인해보세요
      </p>

      <div className="interventions-list">
        {interventions.map((intervention, index) => (
          <div key={intervention.message_id} className="intervention-card">
            <div className="intervention-header">
              <span className="intervention-number">#{index + 1}</span>
              <div className="intervention-signals">
                {intervention.signals.map((signal, i) => (
                  <span key={i} className="signal-badge">{signal}</span>
                ))}
              </div>
            </div>

            <div className="intervention-content">
              <div className="user-message-section">
                <div className="section-label">❌ 내 메시지</div>
                <div className="message-text">{intervention.user_message}</div>
              </div>

              <div className="coach-feedback-section">
                <div className="section-label">✅ 코치 조언</div>
                <div className="feedback-text">{intervention.coach_feedback}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
