import React from 'react';
import { useNavigate } from 'react-router-dom';
import type { Chat } from '../../types';
import './Sidebar.css';

interface SidebarProps {
  chatHistories: Chat[];
  currentChatId: string | null;
  onSelectChat: (sessionId: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  chatHistories,
  currentChatId,
  onSelectChat,
}) => {
  const navigate = useNavigate();

  const handleLogoClick = () => {
    navigate('/');
  };

  const sortedChats = [...chatHistories].sort((a, b) => {
    if (!a.timestamp || !b.timestamp) return 0;
    return b.timestamp.getTime() - a.timestamp.getTime();
  });

  return (
    <div className="sidebar">
      <div className="logo-section">
        <div className="logo" onClick={handleLogoClick} style={{ cursor: 'pointer' }}>
          <span className="logo-icon">🧠</span>
          <span className="logo-text">Mind GYM</span>
        </div>
      </div>

      {/* ✅ chat-history를 두 부분으로 분리 */}
      <div className="chat-history">
        {/* ✅ 고정되는 제목 */}
        <div className="chat-history-title">최근 대화</div>
        
        {/* ✅ 스크롤되는 목록 */}
        <div className="chat-history-list">
          {sortedChats.length === 0 ? (
            <div className="empty-state">대화 기록이 없습니다</div>
          ) : (
            sortedChats.map((chat) => (
              <button
                key={chat.id}
                className={`chat-history-item ${chat.id === currentChatId ? 'active' : ''}`}
                onClick={() => onSelectChat(chat.id)}
              >
                {chat.title}
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
