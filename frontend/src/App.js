import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const chatBoxRef = useRef(null);

  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    // Load greeting when app starts
    fetchGreeting();
  }, []);

  const fetchGreeting = async () => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
      const response = await fetch(`${backendUrl}/api/greeting`);
      const data = await response.json();
      
      if (data.success) {
        addMessage(data.text, false, 'greeting');
      } else {
        addMessage('👋 Welcome to PocketPro:SBA Edition! How can I assist you today?', false, 'greeting');
      }
    } catch (error) {
      addMessage('👋 Welcome to PocketPro:SBA Edition! System starting up... How can I assist you today?', false, 'greeting');
    } finally {
      setIsLoading(false);
    }
  };

  const addMessage = (content, isUser = false, type = 'message') => {
    setMessages(prev => [...prev, { content, isUser, type }]);
  };

  const handleSend = async () => {
    if (!input.trim()) return;
    addMessage(input, true);

    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
      const response = await fetch(`${backendUrl}/api/decompose`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input }),
      });
      const data = await response.json();
      
      const responseText = data.response?.text || 'No response';
      addMessage(responseText, false);
      
      // Show sources if available
      if (data.response?.sources && data.response.sources.length > 0) {
        const sourcesText = `📚 Sources: ${data.response.sources.map(s => s.title || s.filename || 'Document').join(', ')}`;
        addMessage(sourcesText, false, 'sources');
      }
    } catch (error) {
      addMessage('❌ Error: Unable to get response from server. Please try again.', false, 'error');
    }
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatMessage = (content) => {
    // Convert markdown-style formatting to HTML
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br/>')
      .replace(/^(#{1,6})\s+(.*?)$/gm, (match, hashes, text) => {
        const level = hashes.length;
        return `<h${level}>${text}</h${level}>`;
      });
  };

  if (isLoading) {
    return (
      <div className="app-container loading">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Starting PocketPro:SBA Edition...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <div className="chat-header">
        <h1>🚀 PocketPro:SBA Edition</h1>
        <p>Your AI-powered document assistant</p>
      </div>
      <div className="chat-container" ref={chatBoxRef}>
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`message ${msg.isUser ? 'message-user' : 'message-assistant'} ${msg.type === 'greeting' ? 'message-greeting' : ''} ${msg.type === 'sources' ? 'message-sources' : ''} ${msg.type === 'error' ? 'message-error' : ''}`}
          >
            <div 
              dangerouslySetInnerHTML={{ 
                __html: formatMessage(msg.content) 
              }} 
            />
          </div>
        ))}
      </div>
      <div className="input-container">
        <textarea
          className="input-box"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask me about your documents, request task breakdowns, or just say hello..."
          disabled={isLoading}
        />
        <button className="send-button" onClick={handleSend} disabled={isLoading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}

export default App;
