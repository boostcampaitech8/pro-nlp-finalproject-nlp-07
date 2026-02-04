import React, { useState, useRef, useEffect } from 'react';
import { IconButton } from '../Common/IconButton';
import './Header.css';

interface HeaderProps {
  title: string;
  onEndChat: () => void;
  difficulty: number;
  useSupervisor: boolean;
  onDifficultyChange: (level: number) => void;
  onSupervisorToggle: (enabled: boolean) => void;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  onEndChat,
  difficulty,
  useSupervisor,
  onDifficultyChange,
  onSupervisorToggle,
}) => {
  const [showSettings, setShowSettings] = useState(false);
  const settingsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (settingsRef.current && !settingsRef.current.contains(event.target as Node)) {
        setShowSettings(false);
      }
    };

    if (showSettings) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showSettings]);

  const difficultyLabels = ['쉬움', '보통', '어려움'];

  return (
    <div className="header">
      <h1 className="header-title">{title}</h1>
      <div className="header-actions">
        {/* ✅ 대화 종료 버튼 */}
        <button className="end-chat-btn" onClick={onEndChat} title="대화 종료">
          <span className="end-chat-icon">🚪</span>
          <span className="end-chat-text">대화 종료</span>
        </button>
        
        {/* ✅ 설정 버튼 + 드롭다운 */}
        <div className="settings-wrapper" ref={settingsRef}>
          <IconButton 
            icon="⚙️" 
            title="설정" 
            onClick={() => setShowSettings(!showSettings)} 
          />
          
          {showSettings && (
            <div className="settings-dropdown">
              <div className="settings-section">
                <div className="settings-label">난이도</div>
                <div className="difficulty-selector">
                  {[1, 2, 3].map((level) => (
                    <button
                      key={level}
                      className={`difficulty-button ${difficulty === level ? 'active' : ''}`}
                      onClick={() => {
                        onDifficultyChange(level);
                      }}
                    >
                      {difficultyLabels[level - 1]}
                    </button>
                  ))}
                </div>
              </div>

              <div className="settings-divider"></div>

              <div className="settings-section">
                <div className="settings-row">
                  <div className="settings-label">
                    정밀 모드
                    {/* ✅ 설명 변경 */}
                    <span className="settings-description">더 정확한 코칭</span>
                  </div>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={useSupervisor}
                      onChange={(e) => onSupervisorToggle(e.target.checked)}
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
