import React from 'react';
import type { SessionFeedback } from '../../types/feedback';
import './FeedbackView.css';

interface FeedbackViewProps {
  feedbackData: SessionFeedback;
}

export const FeedbackView: React.FC<FeedbackViewProps> = ({ feedbackData }) => {
  // ✅ 텍스트 복사 함수
  const handleCopyText = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('클립보드에 복사되었습니다!');
  };

  // ✅ AI 피드백 존재 여부 확인
  const hasAIFeedback = 
    feedbackData.final_feedback.user_profile.tendencies.length > 0 ||
    feedbackData.final_feedback.user_profile.risk_signals.length > 0 ||
    feedbackData.final_feedback.user_profile.traits.length > 0 ||
    feedbackData.final_feedback.feedback.situation_response_evaluation.score > 0 ||
    feedbackData.final_feedback.feedback.sentence_expression_evaluation.good_points.length > 0 ||
    feedbackData.final_feedback.feedback.next_action_guide.copyable_lines.length > 0;

  return (
    <div className="feedback-view">
      <div className="feedback-view-header">
        <h1>✨ 대화 피드백</h1>
        <p>수고하셨습니다! 이번 대화를 분석한 결과입니다.</p>
      </div>

      {/* ✅ 대화 통계 - 항상 표시 (DB 데이터) */}
      <div className="feedback-section full-width">
        <div className="stats-header">
          <h2>📊 대화 통계</h2>
          <p className="stats-subtitle">{feedbackData.persona_name}와의 연습</p>
        </div>

        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">💬</div>
            <div className="stat-content">
              <div className="stat-label">총 대화 턴</div>
              <div className="stat-value">{feedbackData.total_turns}회</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">💡</div>
            <div className="stat-content">
              <div className="stat-label">코치 개입</div>
              <div className="stat-value">{feedbackData.coach_interventions}회</div>
            </div>
          </div>

          <div className="stat-card highlight">
            <div className="stat-icon">📈</div>
            <div className="stat-content">
              <div className="stat-label">개입 비율</div>
              <div className="stat-value">{feedbackData.intervention_rate.toFixed(1)}%</div>
            </div>
          </div>
        </div>
      </div>

      {/* ✅ AI 피드백이 있을 때만 표시 */}
      {hasAIFeedback ? (
        <div className="feedback-grid">
          {/* 왼쪽 열: 사용자 프로필 & 대화 분석 */}
          <div className="feedback-section">
            <h2>👤 대화 분석</h2>
            
            <div className="conversation-summary">
              <h3>대화 요약</h3>
              <p>{feedbackData.final_feedback.conversation_summary}</p>
            </div>

            <div className="profile-badges">
              {feedbackData.final_feedback.user_profile.tendencies.length > 0 && (
                <div className="badge-group">
                  <h4>🔍 감지된 성향</h4>
                  <div className="badges">
                    {feedbackData.final_feedback.user_profile.tendencies.map((tendency, i) => (
                      <span key={i} className="badge badge-tendency">{tendency}</span>
                    ))}
                  </div>
                </div>
              )}

              {feedbackData.final_feedback.user_profile.risk_signals.length > 0 && (
                <div className="badge-group">
                  <h4>⚠️ 주의 신호</h4>
                  <div className="badges">
                    {feedbackData.final_feedback.user_profile.risk_signals.map((signal, i) => (
                      <span key={i} className="badge badge-risk">{signal}</span>
                    ))}
                  </div>
                </div>
              )}

              {feedbackData.final_feedback.user_profile.traits.length > 0 && (
                <div className="badge-group">
                  <h4>✨ 긍정 특성</h4>
                  <div className="badges">
                    {feedbackData.final_feedback.user_profile.traits.map((trait, i) => (
                      <span key={i} className="badge badge-trait">{trait}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="tendency-summary">
              <h3>💭 종합 의견</h3>
              <p>{feedbackData.final_feedback.feedback.user_tendency_summary}</p>
            </div>
          </div>

          {/* 오른쪽 열: 상황 대응 평가 */}
          <div className="feedback-section">
            <h2>📋 상황 대응 평가</h2>
            
            {feedbackData.final_feedback.feedback.situation_response_evaluation.score > 0 && (
              <div className="score-display">
                <div className="score-circle">
                  <div className="score-value">
                    {feedbackData.final_feedback.feedback.situation_response_evaluation.score}
                  </div>
                  <div className="score-max">/5</div>
                </div>
              </div>
            )}

            {feedbackData.final_feedback.feedback.situation_response_evaluation.good_points.length > 0 && (
              <div className="eval-section good">
                <h3>✅ 잘한 점</h3>
                <ul>
                  {feedbackData.final_feedback.feedback.situation_response_evaluation.good_points.map((point, i) => (
                    <li key={i}>{point}</li>
                  ))}
                </ul>
              </div>
            )}

            {feedbackData.final_feedback.feedback.situation_response_evaluation.improve_points.length > 0 && (
              <div className="eval-section improve">
                <h3>📌 개선할 점</h3>
                <ul>
                  {feedbackData.final_feedback.feedback.situation_response_evaluation.improve_points.map((point, i) => (
                    <li key={i}>{point}</li>
                  ))}
                </ul>
              </div>
            )}

            {feedbackData.final_feedback.feedback.situation_response_evaluation.notes && (
              <div className="eval-notes">
                <p>{feedbackData.final_feedback.feedback.situation_response_evaluation.notes}</p>
              </div>
            )}
          </div>

          {/* 왼쪽 열: 문장 표현 평가 */}
          <div className="feedback-section">
            <h2>💬 문장 표현 평가</h2>

            {feedbackData.final_feedback.feedback.sentence_expression_evaluation.good_points.length > 0 && (
              <div className="eval-section good">
                <h3>✅ 잘한 표현</h3>
                <ul>
                  {feedbackData.final_feedback.feedback.sentence_expression_evaluation.good_points.map((point, i) => (
                    <li key={i}>{point}</li>
                  ))}
                </ul>
              </div>
            )}

            {feedbackData.final_feedback.feedback.sentence_expression_evaluation.improve_points.length > 0 && (
              <div className="eval-section improve">
                <h3>📌 개선할 표현</h3>
                <ul>
                  {feedbackData.final_feedback.feedback.sentence_expression_evaluation.improve_points.map((point, i) => (
                    <li key={i}>{point}</li>
                  ))}
                </ul>
              </div>
            )}

            {feedbackData.final_feedback.feedback.sentence_expression_evaluation.rewrite_examples.length > 0 && (
              <div className="rewrite-examples">
                <h3>✏️ 문장 개선 예시</h3>
                {feedbackData.final_feedback.feedback.sentence_expression_evaluation.rewrite_examples.map((example, i) => (
                  <div key={i} className="example-card">
                    <p>{example.replace(/\(T\d+\)$/g, '').trim()}</p>
                    <button
                      className="btn-copy"
                      onClick={() => handleCopyText(example.replace(/\(T\d+\)$/g, '').trim())}
                    >
                      📋 복사
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 오른쪽 열: 다음 액션 가이드 */}
          <div className="feedback-section">
            <h2>🎯 다음 단계</h2>

            {feedbackData.final_feedback.feedback.next_action_guide.copyable_lines.length > 0 && (
              <div className="copyable-lines">
                <h3>💡 바로 사용 가능한 문장</h3>
                <p className="section-desc">실제 상황에서 바로 사용할 수 있는 표현들입니다</p>
                {feedbackData.final_feedback.feedback.next_action_guide.copyable_lines.map((line, i) => (
                  <div key={i} className="copyable-card">
                    <p>{line}</p>
                    <button
                      className="btn-copy"
                      onClick={() => handleCopyText(line)}
                    >
                      📋 복사
                    </button>
                  </div>
                ))}
              </div>
            )}

            {feedbackData.final_feedback.feedback.next_action_guide.next_drills.length > 0 && (
              <div className="next-drills">
                <h3>🏋️ 추천 연습</h3>
                <ul>
                  {feedbackData.final_feedback.feedback.next_action_guide.next_drills.map((drill, i) => (
                    <li key={i}>{drill}</li>
                  ))}
                </ul>
              </div>
            )}

            {feedbackData.final_feedback.feedback.next_action_guide.homework.length > 0 && (
              <div className="homework">
                <h3>📝 과제</h3>
                <ul>
                  {feedbackData.final_feedback.feedback.next_action_guide.homework.map((task, i) => (
                    <li key={i}>{task}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* ✅ AI 피드백이 없을 때 안내 메시지 */
        <div className="feedback-section full-width">
          <div className="ai-feedback-pending">
            <h2>⚠️ AI 분석 준비 중</h2>
            <p>상세한 대화 분석이 아직 완료되지 않았습니다.</p>
            <p>아래 코치 개입 내역을 통해 대화 중 받은 피드백을 확인하실 수 있습니다.</p>
          </div>
        </div>
      )}

      {/* ✅ 코치 개입 내역 - 항상 표시 (DB 데이터) */}
      {feedbackData.interventions.length > 0 && (
        <div className="feedback-section full-width">
          <h2>💡 코치 개입 내역</h2>
          <p className="interventions-subtitle">
            코치가 개입했던 메시지와 피드백을 확인해보세요
          </p>

          <div className="interventions-list">
            {feedbackData.interventions.map((intervention, index) => (
              <div key={intervention.message_id} className="intervention-card">
                <div className="intervention-header">
                  <span className="intervention-number">#{index + 1}</span>
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
      )}
    </div>
  );
};
