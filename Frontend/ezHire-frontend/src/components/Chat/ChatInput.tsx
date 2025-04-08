// src/components/Chat/ChatInput.tsx
import React from 'react';

interface Props {
  onSendMessage: (message: string) => void;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

const ChatInput: React.FC<Props> = ({ onSendMessage, value, onChange }) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (value.trim()) {
      onSendMessage(value);
    }
  };

  return (
    <form className="chat-input" onSubmit={handleSubmit}>
      <input
        type="text"
        value={value}
        onChange={onChange}
        placeholder="Type a message..."
      />
      <button type="submit">Send</button>
    </form>
  );
};

export default ChatInput;
