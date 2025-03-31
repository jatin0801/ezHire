// src/components/Layout/Sidebar.tsx
import React from 'react';
import { Room } from '../../types';

interface Props {
  rooms: Room[];
  currentRoom: string;
  onRoomSelect: (roomId: string) => void;
  isOpen: boolean;
}

const Sidebar: React.FC<Props> = ({ rooms, currentRoom, onRoomSelect, isOpen }) => {
  return (
    <div className={`sidebar ${isOpen ? 'open' : ''}`}>
      <h3>Chat Rooms</h3>
      <ul className="room-list">
        {rooms.map((room) => (
          <li 
            key={room.id} 
            className={currentRoom === room.id ? 'active' : ''}
            onClick={() => onRoomSelect(room.id)}
          >
            {room.name}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Sidebar;
