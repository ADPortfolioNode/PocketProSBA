import React, { useState, useEffect } from "react";
import { Form, Button, Spinner } from "react-bootstrap";

const sbaTips = [
  "SBA offers resources for business planning, launching, managing, and growing your business.",
  "Did you know? SBA offers disaster assistance loans to help businesses recover from declared disasters.",
  "SBA's 7(a) loan program is their primary loan program.",
  "The SBA Microloan program provides loans up to $50,000.",
  "SBA's 8(a) helps disadvantaged entrepreneurs.",
  "SCORE offers free mentoring and low-cost training."
];

const ConciergeChat = ({ onSend, messages = [], loading, userName }) => {
  const [input, setInput] = useState("");
  const [tipIndex, setTipIndex] = useState(0);
  const safeMessages = Array.isArray(messages) ? messages : [];

  useEffect(() => {
    const timer = setInterval(() => {
      setTipIndex((prev) => (prev + 1) % sbaTips.length);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    if (typeof onSend === 'function') {
      onSend(input.trim());
    } else {
      console.warn("onSend prop is not a function or is missing");
    }
    setInput("");
  };

  return (
    <div className="concierge-greeting">
      <div className="greeting-header">
        <h5>Welcome to PocketPro SBA Assistant</h5>
        <p>I’m your virtual concierge for SBA programs and resources!</p>
      </div>
      <div className="greeting-body">
        <div className="chat-history mb-3" style={{ maxHeight: 300, overflowY: 'auto', width: '100%' }}>
          {safeMessages.length === 0 && (
            <div className="no-messages text-muted text-center mb-3">
              Start the conversation below!
            </div>
          )}
          {safeMessages.map((msg, idx) => (
            <div
              key={idx}
              className={`message-bubble ${msg.role === 'user' ? 'user' : 'assistant'}`}
            >
              {msg.content}
            </div>
          ))}
          {loading && (
            <div className="message-bubble assistant">
              <Spinner size="sm" /> Thinking...
            </div>
          )}
        </div>
        <Form onSubmit={handleSubmit} className="name-form">
          <Form.Group controlId="chatInput">
            <Form.Label>
              Ask a question or say hello{userName ? `, ${userName}` : ''}:
            </Form.Label>
            <Form.Control
              type="text"
              placeholder="Type your message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              autoFocus
            />
          </Form.Group>
          <div className="sba-tip mt-3 mb-3">
            <small>
              <strong>SBA Tip:</strong> {sbaTips[tipIndex]}
            </small>
          </div>
          <Button variant="primary" type="submit" className="mt-2" disabled={loading || !input.trim()}>
            {loading && (
              <Spinner
                as="span"
                animation="border"
                size="sm"
                role="status"
                aria-hidden="true"
                className="me-2"
              />
            )}
            Send
          </Button>
        </Form>
      </div>
    </div>
  );
};

export default ConciergeChat;
