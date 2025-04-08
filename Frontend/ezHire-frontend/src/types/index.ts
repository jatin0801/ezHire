// src/types/index.ts

export interface Message {
    id: string;
    text: string;
    sender: string;
    timestamp: number;
    action_tool?: string;
  }
  
  export interface Room {
    id: string;
    name: string;
  }
  
  export interface User {
    id: string;
    username: string;
  }
  
  export interface SequenceStepData {
    channel?: string;
    subject_line?: string;
    timing?: string;
    message_content?: string;
  }
  
  export interface SequenceSteps {
    [key: string]: SequenceStepData;
  }

  export interface Campaign {
    id: number;
    name: string;
    description?: string;
    target_role?: string;
    industry?: string;
    user_id: number;
    created_at?: string;
    updated_at?: string;
  }