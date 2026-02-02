import React from 'react';
import { IconButton } from '../Common/IconButton';

interface HeaderProps {
  title: string;
  onNewChat: () => void;
  onSettings: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  onNewChat,
  onSettings
}) => {
  return (
    <div className="header">
      <h1 className="header-title">{title}</h1>
      <div className="header-actions">
        <IconButton icon="➕" title="새 대화" onClick={onNewChat} />
        <IconButton icon="⚙️" title="설정" onClick={onSettings} />
      </div>
    </div>
  );
};
