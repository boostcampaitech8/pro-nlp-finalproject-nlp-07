import React, { useState } from 'react';

interface CustomScenarioModalProps {
  onSubmit: (persona: string, situation: string) => void;
  onClose: () => void;
}

export const CustomScenarioModal: React.FC<CustomScenarioModalProps> = ({ 
  onSubmit, 
  onClose 
}) => {
  const [persona, setPersona] = useState('');
  const [situation, setSituation] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (persona.trim() && situation.trim()) {
      onSubmit(persona.trim(), situation.trim());
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose} onKeyDown={handleKeyDown}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>✏️ 직접 시나리오 만들기</h2>
          <button className="modal-close-btn" onClick={onClose} type="button">
            ✕
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label htmlFor="persona">상대방</label>
            <input
              id="persona"
              type="text"
              className="form-control"
              value={persona}
              onChange={(e) => setPersona(e.target.value)}
              placeholder="예: 까다로운 상사, 화난 고객, 동료"
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="situation">상황</label>
            <textarea
              id="situation"
              className="form-control"
              value={situation}
              onChange={(e) => setSituation(e.target.value)}
              placeholder="예: 프로젝트 지연 사과, 제품 불만 처리, 업무 협조 요청"
              rows={4}
            />
          </div>

          <div className="modal-actions">
            <button 
              type="button" 
              className="btn btn--secondary" 
              onClick={onClose}
            >
              취소
            </button>
            <button 
              type="submit" 
              className="btn btn--primary"
              disabled={!persona.trim() || !situation.trim()}
            >
              대화 시작
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
