import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, AlertCircle, RefreshCw } from 'lucide-react';
import { formatMagazineHtml } from '../utils/magazineProse';
import '../styles/modern-chat.css';

const sbaTips = [
  'SBA offers resources for business planning, launching, managing, and growing your business.',
  'Did you know? SBA offers disaster assistance loans to help businesses recover from declared disasters.',
  "SBA's 7(a) loan program is their primary program for providing financial assistance to small businesses.",
  'The SBA Microloan program provides loans up to $50,000 to help small businesses start up and expand.',
  "SBA's 8(a) Business Development program helps socially and economically disadvantaged entrepreneurs.",
  'SCORE is an SBA resource partner offering free business mentoring and low-cost training.',
  "SBA's Small Business Development Centers (SBDCs) provide free business consulting and training.",
  'The SBA Veterans Business Outreach Center program helps veterans start and grow small businesses.',
  "SBA's Women's Business Centers provide training and counseling for women entrepreneurs.",
  "SBA's Lender Match tool connects small businesses with approved SBA lenders.",
];

const ModernConciergeChat = ({ onSend, messages = [], loading, userName }) => {
  const [input, setInput] = useState('');
  const [tipIndex, setTipIndex] = useState(0);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const safeMessages = Array.isArray(messages) ? messages : [];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [safeMessages, loading]);

  useEffect(() => {
    const timer = setInterval(() => {
      setTipIndex((prev) => (prev + 1) % sbaTips.length);
    }, 7000);
    return () => clearInterval(timer);
  }, []);

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
        setInput('');
      } catch (err) {
        console.error('Error in chat submission:', err);
        setError(err.message || 'Failed to send message. Please try again.');
      } finally {
        setIsSending(false);
      }
    } else {
      console.error('onSend prop is not a function:', typeof onSend);
      setError('Chat system is not properly configured. Please refresh the page.');
      setInput('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const renderMessageBody = (content, role) => {
    if (content == null) return null;
    if (typeof content !== 'string') {
      return <div className="magazine-prose"><p className="mag-p">{String(content)}</p></div>;
    }
    // User messages: keep simple line breaks if short; still itemize if lists present
    const html = formatMagazineHtml(content);
    return (
      <div
        className={`magazine-body ${role === 'user' ? 'is-user' : 'is-assistant'}`}
        dangerouslySetInnerHTML={{ __html: html }}
      />
    );
  };

  return (
    <div className="modern-chat-container magazine-chat">
      <div className="chat-header-modern">
        <div className="chat-avatar">
          <Bot size={32} />
        </div>
        <div className="chat-title">
          <h1>PocketPro SBA Assistant</h1>
          <p>
            Clear, magazine-style answers
            {userName ? ` for ${userName}` : ''} — lists, steps, and plain English
          </p>
        </div>
      </div>

      <div className="chat-messages-modern" role="log" aria-live="polite" aria-relevant="additions">
        {safeMessages.length === 0 && !loading && (
          <div className="welcome-message">
            <div className="welcome-icon">
              <Bot size={48} />
            </div>
            <h2>Welcome — let&apos;s talk SBA clearly</h2>
            <p>
              Ask about loans, certifications, disaster aid, or next steps.
              Answers open as readable articles with itemized lists you can scan.
            </p>
            <ul className="mag-list mag-list-ul welcome-starters">
              <li className="mag-li">
                <span className="mag-li-text">What is an SBA 7(a) loan?</span>
              </li>
              <li className="mag-li">
                <span className="mag-li-text">How do I find a local lender?</span>
              </li>
              <li className="mag-li">
                <span className="mag-li-text">Steps to start a small business</span>
              </li>
            </ul>
          </div>
        )}

        {safeMessages.map((message, index) => {
          const role = message.role === 'user' ? 'user' : 'assistant';
          const ts = message.timestamp
            ? new Date(message.timestamp).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              })
            : new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

          return (
            <div key={message.id || index} className={`message-modern ${role}`}>
              <div className="message-avatar" aria-hidden="true">
                {role === 'user' ? <User size={20} /> : <Bot size={20} />}
              </div>
              <div className="message-content-modern">
                <div className="message-bubble magazine-card">
                  {renderMessageBody(message.content, role)}
                </div>
                <div className="message-time">
                  {role === 'user' ? 'You' : 'Assistant'} · {ts}
                </div>
              </div>
            </div>
          );
        })}

        {loading && (
          <div className="message-modern assistant">
            <div className="message-avatar">
              <Bot size={20} />
            </div>
            <div className="message-content-modern">
              <div className="message-bubble typing" aria-label="Assistant is thinking">
                <div className="typing-indicator">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="error-message-modern" role="alert">
            <AlertCircle size={16} />
            <span>{error}</span>
            <button
              type="button"
              className="retry-button"
              onClick={() => setError(null)}
              aria-label="Dismiss error"
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
              rows={1}
              disabled={isSending || loading}
              aria-label="Message input"
            />
            <button
              type="submit"
              className="send-button-modern"
              disabled={!input.trim() || isSending || loading}
              aria-label="Send"
            >
              <Send size={20} />
            </button>
          </div>
        </form>

        <div className="input-hints">
          <span>Press Enter to send · Shift+Enter for a new line</span>
        </div>
      </div>
    </div>
  );
};

export default ModernConciergeChat;
