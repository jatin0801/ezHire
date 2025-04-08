// src/components/Layout/TopBar.tsx
import React from 'react';

interface Props {
  title: string;
  onMenuClick: () => void;
}

const TopBar: React.FC<Props> = ({ title, onMenuClick }) => {
  return (
    <div className="top-bar">
      <button className="menu-button" onClick={onMenuClick}>
        ☰
      </button>
      <h2 className="title">{title}</h2>
    </div>
  );
};

export default TopBar;
