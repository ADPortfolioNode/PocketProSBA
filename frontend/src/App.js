import React, { useState, useEffect, useRef } from 'react';
import { Container, Row, Col, Form, Button, Card, Badge, Alert, Spinner } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';

// API endpoint
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('idle');
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);
  const [systemInfo, setSystemInfo] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(null);
  const chatBoxRef = useRef(null);
  
  // Add a message to the chat
  const addMessage = (content, isUser = false, type = 'text') => {
    const newMessage = {
      id: Date.now(),
      role: isUser ? 'user' : 'assistant',
      content,
      type,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, newMessage]);
  };
  
  // Handle batch document upload
  const handleBatchUpload = async (files) => {
    try {
      setUploadProgress({ 
        filename: `${files.length} files`, 
        progress: 0 
      });
      
      // Process each file
      let successCount = 0;
      
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const reader = new FileReader();
        
        // Update progress
        setUploadProgress({
          filename: `${file.name} (${i+1}/${files.length})`,
          progress: Math.round((i / files.length) * 100)
        });
      }
    } catch (error) {
      setUploadProgress({ 
        filename: `${files.length} files`, 
        progress: 0
      });
      
      setTimeout(() => setUploadProgress(null), 5000);
      addMessage(`❌ Batch upload failed: ${error.message}`, false, 'error');
    }
  };

  // Fetch system info
  useEffect(() => {
    fetchSystemInfo();
  }, []);

  // Scroll to bottom of chat box when messages change
  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [messages]);

  // Fetch system info
  const fetchSystemInfo = async () => {
    try {
      const response = await fetch(`${API_URL}/api/info`);
      const data = await response.json();
      setSystemInfo(data);
    } catch (err) {
      console.error('Error fetching system info:', err);
      setError('Failed to fetch system information');
    }
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Add user message to chat
    setMessages(prevMessages => [
      ...prevMessages,
      { role: 'user', content: input, timestamp: new Date().toISOString() }
    ]);

    // Clear input and show loading state
    setInput('');
    setLoading(true);
    setStatus('processing');

    try {
      // Send message to API
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          session_id: localStorage.getItem('session_id') || crypto.randomUUID()
        }),
      });

      // Handle API response
      if (response.ok) {
        const data = await response.json();
        
        setMessages(prevMessages => [
          ...prevMessages,
          {
            role: 'assistant',
            content: data.response,
            sources: data.sources,
            timestamp: data.timestamp
          }
        ]);
        setStatus('idle');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to send message');
      }
    } catch (err) {
      console.error('Error sending message:', err);
      setMessages(prevMessages => [
        ...prevMessages,
        {
          role: 'assistant',
          content: `Error: ${err.message}. Please try again later.`,
          error: true,
          timestamp: new Date().toISOString()
        }
      ]);
      setStatus('error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <div className="chat-container">
        <header className="app-header">
          <h1>PocketPro SBA Assistant</h1>
          <span className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}>
            {connected ? 'Connected' : 'Connecting...'}
          </span>
        </header>
        
        <main className="chat-main">
          <div className="chat-messages" ref={chatBoxRef}>
            {messages.map((message, index) => (
              <div key={index} className={`message ${message.role}`}>
                <div className="message-content">{message.content}</div>
                <div className="message-timestamp">{new Date(message.timestamp).toLocaleTimeString()}</div>
              </div>
            ))}
            
            {loading && (
              <div className="message assistant">
                <div className="message-content">
                  <Spinner animation="border" variant="light" size="sm" />
                  <span className="ml-2">Thinking...</span>
                </div>
              </div>
            )}
          </div>
          
          <div className="input-area">
            <Form onSubmit={handleSubmit}>
              <Form.Group className="mb-0">
                <Form.Control
                  type="text"
                  placeholder="Ask about SBA resources..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={loading}
                />
              </Form.Group>
              <Button variant="primary" type="submit" disabled={loading || !input.trim()}>
                Send
              </Button>
            </Form>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
