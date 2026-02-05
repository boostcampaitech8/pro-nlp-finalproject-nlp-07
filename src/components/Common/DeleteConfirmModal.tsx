import React from 'react';
import './DeleteConfirmModal.css';

interface DeleteConfirmModalProps {
  isOpen: boolean;
  itemName: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export const DeleteConfirmModal: React.FC<DeleteConfirmModalProps> = ({
  isOpen,
  itemName,
  onConfirm,
  onCancel,
}) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h2>대화 삭제</h2>
        <p>"{itemName}" 대화를 정말 삭제하시겠습니까?</p>
        <p className="warning-text">이 작업은 되돌릴 수 없습니다.</p>
        
        <div className="modal-actions">
          <button className="btn-cancel" onClick={onCancel}>
            취소
          </button>
          <button className="btn-delete" onClick={onConfirm}>
            삭제
          </button>
        </div>
      </div>
    </div>
  );
};
