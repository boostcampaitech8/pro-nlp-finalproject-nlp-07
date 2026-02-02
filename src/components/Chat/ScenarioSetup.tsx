// src/components/Chat/ScenarioSetup.tsx
import React from 'react';
import './ScenarioSetup.css';

interface ScenarioSetupProps {
  onSelectScenario: (persona: string, situation: string) => void;
  onCustomCreate: () => void;
}

export const ScenarioSetup: React.FC<ScenarioSetupProps> = ({
  onSelectScenario,
  onCustomCreate
}) => {
  const presetScenarios = [
    {
      id: 1,
      title: '화난 고객 응대',
      persona: '화난 고객',
      situation: '제품 불만으로 연락한 고객',
      icon: '😠'
    },
    {
      id: 2,
      title: '상사에게 보고',
      persona: '까다로운 상사',
      situation: '프로젝트 지연 사과 및 해결책 제시',
      icon: '👔'
    }
  ];

  return (
    <div className="scenario-setup">
      <div className="scenario-header">
        <div className="scenario-icon">💬</div>
        <h2>어떤 상황을 연습하고 싶으신가요?</h2>
        <p>아래 예시를 선택하거나 직접 상황을 만들어보세요</p>
      </div>

      <div className="scenario-cards">
        {presetScenarios.map(scenario => (
          <button
            key={scenario.id}
            className="scenario-card"
            onClick={() => onSelectScenario(scenario.persona, scenario.situation)}
          >
            <div className="scenario-card-icon">{scenario.icon}</div>
            <h3>{scenario.title}</h3>
            <p className="scenario-persona">상대: {scenario.persona}</p>
            <p className="scenario-situation">{scenario.situation}</p>
          </button>
        ))}
      </div>

      <button className="scenario-custom-btn" onClick={onCustomCreate}>
        <span>✏️</span>
        직접 만들기
      </button>
    </div>
  );
};
