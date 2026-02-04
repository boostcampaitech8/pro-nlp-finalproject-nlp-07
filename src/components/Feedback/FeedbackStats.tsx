import React from 'react';
import './FeedbackStats.css';

interface FeedbackStatsProps {
  personaName: string;
  totalTurns: number;
  coachInterventions: number;
  interventionRate: number;
}

export const FeedbackStats: React.FC<FeedbackStatsProps> = ({
  personaName,
  totalTurns,
  coachInterventions,
  interventionRate,
}) => {
  return (
    <div className="feedback-stats">
      <div className="stats-header">
        <h2>📊 대화 통계</h2>
        <p className="stats-subtitle">{personaName}와의 연습</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">💬</div>
          <div className="stat-content">
            <div className="stat-label">총 대화 턴</div>
            <div className="stat-value">{totalTurns}회</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">💡</div>
          <div className="stat-content">
            <div className="stat-label">코치 개입</div>
            <div className="stat-value">{coachInterventions}회</div>
          </div>
        </div>

        <div className="stat-card highlight">
          <div className="stat-icon">📈</div>
          <div className="stat-content">
            <div className="stat-label">개입 비율</div>
            <div className="stat-value">{interventionRate.toFixed(1)}%</div>
          </div>
        </div>
      </div>
    </div>
  );
};
