// src/components/Chat/Message.tsx
import React from 'react';
import { Message as MessageType } from '../../types';

interface Props {
  message: MessageType;
  isCurrentUser: boolean;
}

const Message: React.FC<Props> = ({ message, isCurrentUser }) => {

  const hasActionTool = message.action_tool !== undefined;

  return (
    <div className={`message ${isCurrentUser ? 'own-message' : ''}`}>
      <div className="message-sender">{message.sender}</div>
      {hasActionTool && (
        <div className="message-action-tool">
          {message.action_tool}
        </div>
      )}
      <div className="message-text">{message.text}</div>
      <div className="message-time">
        {new Date(message.timestamp).toLocaleTimeString()}
      </div>
    </div>
  );
};

export default Message;
