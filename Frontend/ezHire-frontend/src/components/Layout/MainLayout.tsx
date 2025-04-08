// src/components/Layout/MainLayout.tsx
import React, { useState } from 'react';
import TopBar from './TopBar';
import Sidebar from './Sidebar';
import { Room } from '../../types';

interface Props {
  rooms: Room[];
  currentRoom: string;
  onRoomSelect: (roomId: string) => void;
  children: React.ReactNode;
}

const MainLayout: React.FC<Props> = ({ rooms, currentRoom, onRoomSelect, children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <div className="main-layout">
      <TopBar title="ezHire" onMenuClick={toggleSidebar} />
      <div className="content-area">
        <Sidebar 
          rooms={rooms} 
          currentRoom={currentRoom} 
          onRoomSelect={onRoomSelect} 
          isOpen={sidebarOpen} 
        />
        <main className="main-content">
          {children}
        </main>
      </div>
    </div>
  );
};

export default MainLayout;
