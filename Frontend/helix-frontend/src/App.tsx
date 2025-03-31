// src/App.tsx
import React, { useState, useEffect } from 'react';
import MainLayout from './components/Layout/MainLayout';
import ChatArea from './components/Chat/ChatArea';
import ChatInput from './components/Chat/ChatInput';
import WorkspaceArea from './components/Workspace/WorkspaceArea';
import socketService from './services/socketService';
import { Message, Room, Campaign } from './types';
import './App.css';

const App: React.FC = () => {
  const [username, setUsername] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [rooms, setRooms] = useState<Room[]>([
    { id: '1', name: 'Helix' },
    { id: '2', name: 'Selix' },
    { id: '3', name: 'General' }
  ]);
  const [currentRoom, setCurrentRoom] = useState('1');
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [sequenceData, setSequenceData] = useState<any>(null);

  // campaigns
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<number | null>(null);
  const [newCampaignName, setNewCampaignName] = useState('');
  const [newCampaignDetails, setNewCampaignDetails] = useState({
    description: '',
    target_role: '',
    industry: ''
  });
  const [showNewCampaignForm, setShowNewCampaignForm] = useState(false);

  const API_URL = 'http://127.0.0.1:5080';
  const CONVERSATION_ID = 68;

  useEffect(() => {
    fetchCampaigns();
    if (isLoggedIn) {
      socketService.connect(username)
        .then(() => {
          socketService.joinRoom(currentRoom);
          socketService.onMessageReceived((message) => {
            setMessages((prevMessages) => [...prevMessages, message]);
          });
          socketService.onAPIResponseReceived((response) => {
            const botMessage: Message = {
              id: Date.now().toString(),
              sender: 'Helix',
              text: response.output,
              timestamp: Date.now()
            };
            setMessages((prevMessages) => [...prevMessages, botMessage]);
          });
        })
        
        .catch((error) => {
          console.error('Socket connection error:', error);
        });

      return () => {
        socketService.disconnect();
      };
    }
  }, [isLoggedIn, username, currentRoom]);

  const fetchCampaigns = () => {
    fetch(`${API_URL}/campaigns?user_id=1`)
      .then(response => response.json())
      .then(data => {
        if (data.campaigns) {
          setCampaigns(data.campaigns);
        }
      })
      .catch(error => {
        console.error('Error fetching campaigns:', error);
      });
  };

  const handleCreateCampaign = () => {
    if (!newCampaignName.trim()) return;

    fetch(`${API_URL}/campaigns`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: 1,
        name: newCampaignName,
        description: newCampaignDetails.description,
        target_role: newCampaignDetails.target_role,
        industry: newCampaignDetails.industry
      }),
    })
      .then(response => response.json())
      .then(data => {
        if (data.campaign_id) {
          setSelectedCampaign(data.campaign_id);
          fetchCampaigns();
          setNewCampaignName('');
          setNewCampaignDetails({
            description: '',
            target_role: '',
            industry: ''
          });
          setShowNewCampaignForm(false);
        }
      })
      .catch(error => {
        console.error('Error creating campaign:', error);
      });
  };

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (username.trim()) {
      setIsLoggedIn(true);
    }
  };

  const handleRoomSelect = (roomId: string) => {
    socketService.leaveRoom(currentRoom);
    setCurrentRoom(roomId);
    setMessages([]);
    socketService.joinRoom(roomId);
  };

  const handleSendMessage = (message: string) => {
    if (message.trim() === '') return;
    
    const newMessage: Message = {
      id: Date.now().toString(),
      text: message,
      sender: username,
      timestamp: Date.now()
    };
    
    setMessages(prevMessages => [...prevMessages, newMessage]);
    
    socketService.sendMessage(currentRoom, message);
    
    sendMessageToAPI(message);

    setInputMessage('');
  };

  // Separate function to send message to API
  const sendMessageToAPI = (messageText: string) => {
    console.log("Sending message to API:", messageText);
    
    fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: 1,
        conversation_id: CONVERSATION_ID,
        campaign_id: selectedCampaign,
        message: messageText,
      }),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then((data) => {
        console.log("API response received:", data);
        var responseData = data.response || data;
        if (typeof responseData === 'string') {
          try {
            responseData = JSON.parse(responseData);
            console.log("Parsed response data:", responseData);
          } catch (error) {
            console.error("Failed to parse response data as JSON:", error);
          }
        }
        const botMessage: Message = {
          id: Date.now().toString(),
          sender: 'Helix',
          text: responseData.message || 'No output received',
          timestamp: Date.now(),
          action_tool: responseData.action_tool
        };
        setMessages((prevMessages) => [...prevMessages, botMessage]);
        if (
          responseData.action_tool === 'Generate_Outreach_Sequence' || 
          responseData.action_tool === 'Edit_Sequence'
        ) {
          try {
            // Try to parse the output as JSON if it's a string
            const sequenceOutput = typeof responseData.output === 'string' 
              ? JSON.parse(responseData.output) 
              : responseData.output;
            
            // Update sequence data to trigger workspace update
            setSequenceData({
              ...sequenceOutput,
              sequence_id: responseData.sequence_id,
              campaign_id: responseData.campaign_id
            });
          } catch (error) {
            console.error('Error parsing sequence data:', error);
            setSequenceData(responseData.output);
          }
        }
      })
      .catch((error) => {
        console.error('Error sending message to API:', error);
        const errorMessage: Message = {
          id: Date.now().toString(),
          sender: 'system',
          text: 'Failed to get response from API. Please try again.',
          timestamp: Date.now()
        };
        setMessages((prevMessages) => [...prevMessages, errorMessage]);
      });
  };

  const handleNewMessage = (newMessage: Message) => {
    setMessages((prevMessages) => [...prevMessages, newMessage]);
    sendMessageToAPI(newMessage.text);
  };

  if (!isLoggedIn) {
    return (
      <div className="login-container">
        <form onSubmit={handleLogin}>
          <h2>Enter your details to join</h2>
          <div className="form-group">
            <label>Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Username"
              required
            />
          </div>
          
          <div className="form-group">
            <label>Select Campaign</label>
            <select 
              value={selectedCampaign || ''} 
              onChange={(e) => setSelectedCampaign(e.target.value ? parseInt(e.target.value) : null)}
            >
              <option value="">-- Select a campaign --</option>
              {campaigns.map(campaign => (
                <option key={campaign.id} value={campaign.id}>
                  {campaign.name}
                </option>
              ))}
            </select>
            <button 
              type="button" 
              className="campaign-btn"
              onClick={() => setShowNewCampaignForm(!showNewCampaignForm)}
            >
              {showNewCampaignForm ? 'Cancel' : 'Create New Campaign'}
            </button>
          </div>
          
          {showNewCampaignForm && (
            <div className="new-campaign-form">
              <h3>Create New Campaign</h3>
              <div className="form-group">
                <label>Campaign Name</label>
                <input
                  type="text"
                  value={newCampaignName}
                  onChange={(e) => setNewCampaignName(e.target.value)}
                  placeholder="Campaign Name"
                  required
                />
              </div>
              <div className="form-group">
                <label>Description</label>
                <input
                  type="text"
                  value={newCampaignDetails.description}
                  onChange={(e) => setNewCampaignDetails({...newCampaignDetails, description: e.target.value})}
                  placeholder="Description"
                />
              </div>
              <div className="form-group">
                <label>Target Role</label>
                <input
                  type="text"
                  value={newCampaignDetails.target_role}
                  onChange={(e) => setNewCampaignDetails({...newCampaignDetails, target_role: e.target.value})}
                  placeholder="Target Role"
                />
              </div>
              <div className="form-group">
                <label>Industry</label>
                <input
                  type="text"
                  value={newCampaignDetails.industry}
                  onChange={(e) => setNewCampaignDetails({...newCampaignDetails, industry: e.target.value})}
                  placeholder="Industry"
                />
              </div>
              <button type="button" onClick={handleCreateCampaign}>Create Campaign</button>
            </div>
          )}
          
          <button type="submit" disabled={!username || !selectedCampaign}>Join Chat</button>
        </form>
      </div>
    );
  }

  return (
    <MainLayout
      rooms={rooms}
      currentRoom={currentRoom}
      onRoomSelect={handleRoomSelect}
    >
      <div className="app-container">
        <div className="workspace-section">
          <WorkspaceArea sequenceData={sequenceData} />
        </div>
        <div className="chat-section">
          <ChatArea messages={messages} currentUser={username} onNewMessage={handleNewMessage}/>
          <ChatInput 
            onSendMessage={handleSendMessage} 
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
          />
        </div>
      </div>
    </MainLayout>
  );
};

export default App;
