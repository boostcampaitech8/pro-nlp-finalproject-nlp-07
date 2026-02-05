import React, { useState } from 'react';
import './RatingModal.css';

interface RatingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (rating: number) => void;
}

export const RatingModal: React.FC<RatingModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [selectedRating, setSelectedRating] = useState<number | null>(null);
  const [hoveredRating, setHoveredRating] = useState<number | null>(null);

  if (!isOpen) return null;

  const handleSubmit = () => {
    if (selectedRating) {
      onSubmit(selectedRating);
    }
  };

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="rating-modal-overlay" onClick={handleOverlayClick}>
      <div className="rating-modal">
        <div className="rating-modal-header">
          <h2>대화 경험 평가</h2>
          <button className="rating-modal-close" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="rating-modal-content">
          <p>이번 대화 연습은 어떠셨나요?</p>
          
          <div className="rating-stars">
            {[1, 2, 3, 4, 5].map((rating) => (
              <button
                key={rating}
                className={`star-button ${
                  (hoveredRating !== null ? rating <= hoveredRating : rating <= (selectedRating || 0))
                    ? 'active'
                    : ''
                }`}
                onClick={() => setSelectedRating(rating)}
                onMouseEnter={() => setHoveredRating(rating)}
                onMouseLeave={() => setHoveredRating(null)}
              >
                ⭐
              </button>
            ))}
          </div>

          <div className="rating-label">
            {selectedRating ? `${selectedRating}점` : '별점을 선택해주세요'}
          </div>
        </div>

        <div className="rating-modal-actions">
          <button className="btn-cancel" onClick={onClose}>
            취소
          </button>
          <button
            className="btn-submit"
            onClick={handleSubmit}
            disabled={!selectedRating}
          >
            제출하고 피드백 보기
          </button>
        </div>
      </div>
    </div>
  );
};
