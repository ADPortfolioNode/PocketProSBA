import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, AlertCircle, RefreshCw } from 'lucide-react';

const sbaTips = [
  "SBA offers resources for business planning, launching, managing, and growing your business.",
  "Did you know? SBA offers disaster assistance loans to help businesses recover from declared disasters.",
  "SBA's 7(a) loan program is their primary program for providing financial assistance to small businesses.",
  "The SBA Microloan program provides loans up to $50,000 to help small businesses start up and expand.",
  "SBA's 8(a) Business Development program helps socially and economically disadvantaged entrepreneurs.",
  "SCORE is an SBA resource partner offering free business mentoring and low-cost training.",
  "SBA's Small Business Development Centers (SBDCs) provide free business consulting and training.",
  "The SBA Veterans Business Outreach Center program helps veterans start and grow small businesses.",
  "SBA's Women's Business Centers provide training and counseling for women entrepreneurs.",
  "SBA's Lender Match tool connects small businesses with approved SBA lenders."
];

const ModernConciergeChat = ({ onSend, messages = [], loading, userName }) => {
  const [input, setInput] = useState("");
  const [tipIndex, setTipIndex] = useState(0);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const safeMessages = Array.isArray(messages) ? messages : [];

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [safeMessages]);

  // Rotate tips every 7 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      setTipIndex((prev) => (prev + 1) % sbaTips.length);
    }, 7000);
    return () => clearInterval(timer);
  }, []);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    if (typeof onSend === 'function') {
      setIsSending(true);
      setError(null);
      
      try {
        await onSend(input.trim());
        setInput("");
      } catch (error) {
        console.error('Error in chat submission:', error);
        setError(error.message || 'Failed to send message. Please try again.');
      } finally {
        setIsSending(false);
      }
    } else {
      console.error('onSend prop is not a function:', typeof onSend);
      setError('Chat system is not properly configured. Please refresh the page.');
      setInput("");
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const formatMessageContent = (content) => {
    if (typeof content !== 'string') return content;
    
    // Basic markdown-like formatting
    return content
      .split('\n')
      .map((line, index) => (
        <span key={index}>
          {line}
          {index < content.split('\n').length - 1 && <br />}
        </span>
      ));
  };

  return (
    <div className="modern-chat-container">
      <div className="chat-header-modern">
        <div className="chat-avatar">
          <Bot size={32} />
        </div>
        <div className="chat-title">
          <h1>PocketPro SBA Assistant</h1>
          <p>Your AI-powered guide to SBA programs and resources</p>
        </div>
      </div>

      <div className="chat-messages-modern">
        {safeMessages.length === 0 && !loading && (
          <div className="welcome-message">
            <div className="welcome-icon">
              <Bot size={48} />
            </div>
            <h2>Welcome to your SBA Concierge!</h2>
            <p>I'm here to help you navigate SBA programs, loans, and resources. Ask me anything about starting, managing, or growing your small business.</p>
          </div>
        )}

        {safeMessages.map((message, index) => (
          <div
            key={index}
            className={`message-modern ${message.role}`}
          >
            <div className="message-avatar">
              {message.role === 'user' ? <User size={20} /> : <Bot size={20} />}
            </div>
            <div className="message-content-modern">
              <div className="message-bubble">
                {formatMessageContent(message.content)}
              </div>
              <div className="message-time">
                {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="message-modern assistant">
            <div className="message-avatar">
              <Bot size={20} />
            </div>
            <div className="message-content-modern">
              <div className="message-bubble typing">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="error-message-modern">
            <AlertCircle size={16} />
            <span>{error}</span>
            <button 
              className="retry-button"
              onClick={() => setError(null)}
            >
              <RefreshCw size={14} />
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-modern">
        <div className="sba-tip-modern">
          <strong>SBA Tip:</strong> {sbaTips[tipIndex]}
        </div>
        
        <form onSubmit={handleSubmit} className="input-form-modern">
          <div className="input-container">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about SBA loans, grants, or business advice..."
              className="modern-textarea"
              rows="1"
              disabled={isSending || loading}
            />
            <button
              type="submit"
              className="send-button-modern"
              disabled={!input.trim() || isSending || loading}
            >
              <Send size={20} />
            </button>
          </div>
        </form>
        
        <div className="input-hints">
          <span>Press Enter to send • Shift+Enter for new line</span>
        </div>
      </div>
    </div>
  );
};

export default ModernConciergeChat;
