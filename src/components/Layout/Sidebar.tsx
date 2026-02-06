import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { DeleteConfirmModal } from '../Common/DeleteConfirmModal';
import { sessionService } from '../../services/sessionService';
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
}) => {
  const navigate = useNavigate();
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState<Chat | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  const handleLogoClick = () => {
    navigate('/');
  };

  const handleChatClick = (sessionId: string) => {
    navigate(`/chat/${sessionId}`);
    window.location.reload();
  };

  // ✅ 메뉴 토글
  const handleMenuToggle = (e: React.MouseEvent, chatId: string) => {
    e.stopPropagation();
    setOpenMenuId(openMenuId === chatId ? null : chatId);
  };

  // ✅ 삭제 버튼 클릭
  const handleDeleteClick = (e: React.MouseEvent, chat: Chat) => {
    e.stopPropagation();
    setSessionToDelete(chat);
    setDeleteModalOpen(true);
    setOpenMenuId(null);
  };

  // ✅ 삭제 확인
  const handleConfirmDelete = async () => {
    if (!sessionToDelete) return;

    try {
      await sessionService.deleteSession(sessionToDelete.id);
      setDeleteModalOpen(false);
      setSessionToDelete(null);
      
      // 현재 보고 있는 세션을 삭제한 경우 홈으로 이동
      if (currentChatId === sessionToDelete.id) {
        navigate('/');
      } else {
        // 그 외의 경우 페이지 새로고침
        window.location.reload();
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
      alert('세션 삭제에 실패했습니다.');
    }
  };

  // ✅ 외부 클릭 시 메뉴 닫기
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpenMenuId(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const sortedChats = [...chatHistories].sort((a, b) => {
    if (!a.timestamp || !b.timestamp) return 0;
    return b.timestamp.getTime() - a.timestamp.getTime();
  });

  return (
    <>
      <div className="sidebar">
        <div className="logo-section">
          <div className="logo" onClick={handleLogoClick} style={{ cursor: 'pointer' }}>
            <span className="logo-icon">🧠</span>
            <span className="logo-text">Mind GYM</span>
          </div>
        </div>

        <div className="chat-history">
          <div className="chat-history-title">최근 대화</div>
          
          <div className="chat-history-list">
            {sortedChats.length === 0 ? (
              <div className="empty-state">대화 기록이 없습니다</div>
            ) : (
              sortedChats.map((chat) => (
                <div
                  key={chat.id}
                  className={`chat-history-item-wrapper ${chat.id === currentChatId ? 'active' : ''}`}
                >
                  <button
                    className="chat-history-item"
                    onClick={() => handleChatClick(chat.id)}
                  >
                    {chat.roleDescription || chat.title}
                  </button>
                  
                  {/* ✅ 세로 점 3개 메뉴 */}
                  <div className="chat-menu-container" ref={menuRef}>
                    <button
                      className="chat-menu-button"
                      onClick={(e) => handleMenuToggle(e, chat.id)}
                      aria-label="메뉴 열기"
                    >
                      <span className="menu-dot"></span>
                      <span className="menu-dot"></span>
                      <span className="menu-dot"></span>
                    </button>
                    
                    {openMenuId === chat.id && (
                      <div className="chat-menu-dropdown">
                        <button
                          className="menu-item delete"
                          onClick={(e) => handleDeleteClick(e, chat)}
                        >
                          🗑️ 삭제
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* ✅ 삭제 확인 모달 */}
      <DeleteConfirmModal
        isOpen={deleteModalOpen}
        itemName={sessionToDelete?.roleDescription || sessionToDelete?.title || ''}
        onConfirm={handleConfirmDelete}
        onCancel={() => {
          setDeleteModalOpen(false);
          setSessionToDelete(null);
        }}
      />
    </>
  );
};
