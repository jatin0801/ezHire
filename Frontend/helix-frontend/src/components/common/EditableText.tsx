// src/components/common/EditableText.tsx
import React, { useState, useEffect, useRef } from 'react';

interface Props {
  text: string;
  onSave: (text: string) => void;
  placeholder?: string;
}

const EditableText: React.FC<Props> = ({ text, onSave, placeholder = "Click to edit" }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [value, setValue] = useState(text);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isEditing]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSave();
    } else if (e.key === 'Escape') {
      setIsEditing(false);
      setValue(text);
    }
  };

  const handleSave = () => {
    setIsEditing(false);
    onSave(value);
  };

  return (
    <div className="editable-text">
      {isEditing ? (
        <textarea
          ref={inputRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onBlur={handleSave}
          onKeyDown={handleKeyDown}
          className="editable-input"
        />
      ) : (
        <div 
          onClick={() => setIsEditing(true)} 
          className="editable-display"
        >
          {text || placeholder}
        </div>
      )}
    </div>
  );
};

export default EditableText;
