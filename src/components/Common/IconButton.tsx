import React from 'react';

interface IconButtonProps {
  icon: string;
  title: string;
  onClick: () => void;
  className?: string;
}

export const IconButton: React.FC<IconButtonProps> = ({
  icon,
  title,
  onClick,
  className = ''
}) => {
  return (
    <button
      className={`icon-btn ${className}`}
      title={title}
      onClick={onClick}
    >
      {icon}
    </button>
  );
};
