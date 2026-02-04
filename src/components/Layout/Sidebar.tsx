import React from 'react';
import { useNavigate } from 'react-router-dom'; // ✅ 추가
import type { Chat } from '../../types';

interface SidebarProps {
  chatHistories: Chat[];
  currentChatId: number | null;
  onSelectChat: (chatId: number) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  chatHistories,
  currentChatId,
  onSelectChat,
}) => {
  const navigate = useNavigate(); // ✅ 추가

  const handleLogoClick = () => {
    navigate('/'); // ✅ 홈으로 이동
  };

  return (
    <div className="sidebar">
      <div className="logo-section">
        <div className="logo" onClick={handleLogoClick} style={{ cursor: 'pointer' }}> {/* ✅ 추가 */}
          <span className="logo-icon">🧠</span>
          <span className="logo-text">Mind GYM</span>
        </div>
      </div>

      <div className="chat-history">
        <div className="chat-history-title">최근 대화</div>
        {chatHistories.map((chat) => (
          <button
            key={chat.id}
            className={`chat-history-item ${chat.id === currentChatId ? 'active' : ''}`}
            onClick={() => onSelectChat(chat.id)}
          >
            {chat.title}
          </button>
        ))}
      </div>
    </div>
  );
};
