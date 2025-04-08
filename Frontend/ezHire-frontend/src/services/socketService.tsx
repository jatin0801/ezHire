// src/services/socketService.ts
import { io, Socket } from 'socket.io-client';
import { Message } from '../types';

class SocketService {
  private socket: Socket | null = null;
  private readonly serverUrl = 'http://localhost:3000'; // Your backend server URL

  connect(username: string): Promise<void> {
    return new Promise((resolve, reject) => {
      this.socket = io(this.serverUrl, {
        query: { username }
      });

      this.socket.on('connect', () => {
        resolve();
      });

      this.socket.on('connect_error', (error) => {
        reject(error);
      });
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  joinRoom(roomId: string): void {
    if (this.socket) {
      this.socket.emit('join_room', roomId);
    }
  }

  leaveRoom(roomId: string): void {
    if (this.socket) {
      this.socket.emit('leave_room', roomId);
    }
  }

  sendMessage(roomId: string, message: string): void {
    if (this.socket) {
      this.socket.emit('send_message', { roomId, message });
    }
  }

  sendMessageToAPI(userId: number, conversationId: number, campaignId: number, message: string): void {
    if (this.socket) {
      this.socket.emit('process_message', {
        user_id: userId,
        conversation_id: conversationId,
        campaign_id: campaignId,
        message: message
      });
    }
  }

  onAPIResponseReceived(callback: (response: any) => void): void {
    if (this.socket) {
      this.socket.on('api_response', callback);
    }
  }

  onMessageReceived(callback: (message: Message) => void): void {
    if (this.socket) {
      this.socket.on('receive_message', callback);
    }
  }
}

export default new SocketService();
