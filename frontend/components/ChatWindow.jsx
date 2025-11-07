import React, { useState, useEffect, useRef } from 'react';
import './ChatWindow.css';

const ChatWindow = ({ exchangeId, isOpen, onClose, currentUser }) => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [participants, setParticipants] = useState([]);
  const messagesEndRef = useRef(null);
  const websocketRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Connect to WebSocket when chat opens
  useEffect(() => {
    if (isOpen && exchangeId && currentUser) {
      connectWebSocket();
    }

    return () => {
      disconnectWebSocket();
    };
  }, [isOpen, exchangeId, currentUser]);

  const connectWebSocket = () => {
    try {
      // Get JWT token for authentication
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('No authentication token found');
        return;
      }

      // Connect to WebSocket
      const wsUrl = `ws://localhost:8000/ws/chat/exchange/${exchangeId}?token=${token}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('Chat WebSocket connected');
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };

      ws.onclose = () => {
        console.log('Chat WebSocket disconnected');
        setIsConnected(false);
      };

      ws.onerror = (error) => {
        console.error('Chat WebSocket error:', error);
        setIsConnected(false);
      };

      websocketRef.current = ws;
    } catch (error) {
      console.error('Failed to connect to chat:', error);
    }
  };

  const disconnectWebSocket = () => {
    if (websocketRef.current) {
      websocketRef.current.close();
      websocketRef.current = null;
    }
    setIsConnected(false);
  };

  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'message':
        setMessages(prev => [...prev, data]);
        break;
      case 'history':
        setMessages(data.messages);
        break;
      case 'participants_online':
        setParticipants(data.participants);
        break;
      case 'typing_start':
        if (data.user_id !== currentUser?.id) {
          setIsTyping(true);
        }
        break;
      case 'typing_stop':
        if (data.user_id !== currentUser?.id) {
          setIsTyping(false);
        }
        break;
      case 'error':
        console.error('Chat error:', data.message);
        break;
      default:
        console.log('Unknown message type:', data.type);
    }
  };

  const sendMessage = () => {
    if (!newMessage.trim() || !websocketRef.current || !isConnected) {
      return;
    }

    const messageData = {
      type: 'message',
      text: newMessage.trim(),
      message_type: 'text'
    };

    websocketRef.current.send(JSON.stringify(messageData));
    setNewMessage('');
    stopTyping();
  };

  const handleTyping = () => {
    if (!websocketRef.current || !isConnected) return;

    // Send typing start
    websocketRef.current.send(JSON.stringify({ type: 'typing_start' }));

    // Clear existing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // Set timeout to stop typing indicator
    typingTimeoutRef.current = setTimeout(() => {
      stopTyping();
    }, 1000);
  };

  const stopTyping = () => {
    if (websocketRef.current && isConnected) {
      websocketRef.current.send(JSON.stringify({ type: 'typing_stop' }));
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="chat-window">
      <div className="chat-header">
        <h3>Обмен #{exchangeId}</h3>
        <div className="chat-status">
          <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}></span>
          <span>{isConnected ? 'Подключен' : 'Отключен'}</span>
          <span className="participants-count">
            Участников: {participants.length}
          </span>
        </div>
        <button className="close-button" onClick={onClose}>×</button>
      </div>

      <div className="messages-container">
        {messages.map((msg, index) => (
          <div
            key={msg.id || index}
            className={`message ${msg.sender_id === currentUser?.id ? 'own' : 'other'}`}
          >
            <div className="message-header">
              <span className="sender-name">{msg.sender_name}</span>
              <span className="message-time">
                {msg.created_at ? new Date(msg.created_at).toLocaleTimeString() : ''}
              </span>
            </div>
            <div className="message-content">{msg.message_text}</div>
          </div>
        ))}

        {isTyping && (
          <div className="typing-indicator">
            <span>Кто-то печатает...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="message-input-container">
        <textarea
          className="message-input"
          value={newMessage}
          onChange={(e) => {
            setNewMessage(e.target.value);
            handleTyping();
          }}
          onKeyPress={handleKeyPress}
          placeholder="Введите сообщение..."
          rows="2"
        />
        <button
          className="send-button"
          onClick={sendMessage}
          disabled={!newMessage.trim() || !isConnected}
        >
          Отправить
        </button>
      </div>
    </div>
  );
};

export default ChatWindow;
