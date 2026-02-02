import React from 'react';

interface LogoProps {
  icon?: string;
  text?: string;
}

export const Logo: React.FC<LogoProps> = ({
  icon = '🧠',
  text = 'Mind GYM'
}) => {
  return (
    <div className="logo">
      <span className="logo-icon">{icon}</span>
      <span className="logo-text">{text}</span>
    </div>
  );
};
