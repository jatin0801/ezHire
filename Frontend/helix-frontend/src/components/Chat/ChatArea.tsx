// src/components/Chat/ChatArea.tsx
import React, { useEffect, useRef } from 'react';
import { Message as MessageType } from '../../types';
import Message from './Message';

interface Props {
  messages: MessageType[];
  currentUser: string;
  onNewMessage: (message: MessageType) => void;
}

const ChatArea: React.FC<Props> = ({ messages, currentUser, onNewMessage }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = (text: string) => {
    const newMessage: MessageType = {
      id: Date.now().toString(),
      sender: currentUser,
      text,
      timestamp: Date.now()
    };
    onNewMessage(newMessage);
  };

  return (
    <div className="chat-area">
      {messages.map((message) => (
        <Message 
          key={message.id} 
          message={message} 
          isCurrentUser={message.sender === currentUser} 
        />
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default ChatArea;
