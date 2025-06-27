import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const chatBoxRef = useRef(null);

  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [messages]);

  const addMessage = (content, isUser = false) => {
    setMessages(prev => [...prev, { content, isUser }]);
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
      addMessage(data.response?.text || 'No response');
    } catch (error) {
      addMessage('Error: Unable to get response from server.');
    }
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="app-container">
      <div className="chat-container" ref={chatBoxRef}>
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`message ${msg.isUser ? 'message-user' : 'message-assistant'}`}
          >
            {msg.content}
          </div>
        ))}
      </div>
      <textarea
        className="input-box"
        value={input}
        onChange={e => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type your message here..."
      />
      <button className="send-button" onClick={handleSend}>Send</button>
    </div>
  );
}

export default App;
