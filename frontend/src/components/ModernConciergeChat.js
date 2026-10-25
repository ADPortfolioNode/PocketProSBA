import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, AlertCircle, RefreshCw, ArrowUpRight } from 'lucide-react';
import { formatMagazineHtml } from '../utils/magazineProse';
import { friendlyError } from '../utils/friendlyError';
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

const STARTERS = [
  {
    question: 'What is an SBA 7(a) loan?',
    description: 'Learn about uses, terms, and eligibility.',
  },
  {
    question: 'How do I find a local lender?',
    description: 'Get ready to connect with a lender.',
  },
  {
    question: 'Steps to start a small business',
    description: 'Plan your next steps from idea to launch.',
  },
];

const ModernConciergeChat = ({ onSend, messages = [], loading, userName, initialDraft }) => {
  const [input, setInput] = useState(initialDraft || '');
  const [tipIndex, setTipIndex] = useState(0);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState(null);
  const messagesContainerRef = useRef(null);
  const inputRef = useRef(null);

  const safeMessages = Array.isArray(messages) ? messages : [];

  const thinking = !!loading || isSending;

  // Keep follow-up messages in the conversation scroller, not the whole page.
  useEffect(() => {
    if (safeMessages.length === 0 && !thinking) return;
    const messagesContainer = messagesContainerRef.current;
    if (messagesContainer) messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }, [safeMessages.length, thinking]);

  useEffect(() => {
    if (initialDraft) setInput(initialDraft);
  }, [initialDraft]);

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
        // The draft stays in the input so "Try again" resends it.
        setError(friendlyError(err, "Your message didn't go through. Please try again."));
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
          <span className="chat-eyebrow">YOUR SBA CONCIERGE</span>
          <h1>PocketPro SBA Assistant</h1>
          <p>Straightforward guidance on loans, programs, and your next steps{userName ? `, ${userName}` : ''}.</p>
        </div>
        <a href="/browse" className="chat-resources-link">
          Browse SBA resources <ArrowUpRight size={16} aria-hidden="true" />
        </a>
      </div>

      <div
        ref={messagesContainerRef}
        className="chat-messages-modern"
        role="log"
        aria-label="Conversation"
        aria-live="polite"
        aria-relevant="additions"
        aria-busy={thinking}
      >
        {safeMessages.length === 0 && !thinking && (
          <div className="welcome-message">
            <div className="welcome-icon">
              <Bot size={28} />
            </div>
            <p className="welcome-kicker">Small business support, made simpler</p>
            <h2>Welcome — what can we help you with?</h2>
            <p>
              Ask a question or choose a place to start. We&apos;ll help you find
              useful guidance and official SBA resources.
            </p>
            <ul className="mag-list mag-list-ul welcome-starters">
              {STARTERS.map(({ question, description }) => (
                <li className="mag-li" key={question}>
                  <button
                    type="button"
                    className="mag-li-text welcome-starter-btn"
                    onClick={() => {
                      setInput(question);
                      inputRef.current?.focus();
                    }}
                  >
                    <span className="starter-question">{question}</span>
                    <span className="starter-description">{description}</span>
                    <ArrowUpRight size={16} aria-hidden="true" />
                  </button>
                </li>
              ))}
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

        {thinking && (
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
            {input.trim() && typeof onSend === 'function' && (
              <button
                type="button"
                className="retry-button retry-button-text"
                onClick={handleSubmit}
                disabled={isSending}
              >
                <RefreshCw size={14} /> Try again
              </button>
            )}
            <button
              type="button"
              className="retry-button"
              onClick={() => setError(null)}
              aria-label="Dismiss error"
            >
              ×
            </button>
          </div>
        )}

      </div>

      <div className="chat-input-modern">
        <div className="composer-inner">
          <div className="sba-tip-modern" title={sbaTips[tipIndex]}>
            <strong>SBA tip</strong>
            <span>{sbaTips[tipIndex]}</span>
          </div>

          <form onSubmit={handleSubmit} className="input-form-modern">
            <label className="visually-hidden" htmlFor="chat-message">
              Message to PocketPro SBA Assistant
            </label>
            <div className="input-container">
              <textarea
                id="chat-message"
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about SBA loans, grants, or business advice..."
                className="modern-textarea"
                rows={1}
                disabled={thinking}
                aria-label="Message input"
              />
              <button
                type="submit"
                className="send-button-modern"
                disabled={!input.trim() || thinking}
                aria-label="Send"
              >
                <Send size={19} aria-hidden="true" />
              </button>
            </div>
          </form>

          <div className="input-hints">
            <span>Enter to send</span>
            <span className="input-hint-separator" aria-hidden="true">·</span>
            <span>Shift + Enter for a new line</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModernConciergeChat;
