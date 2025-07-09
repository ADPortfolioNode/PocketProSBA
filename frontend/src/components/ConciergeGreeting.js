import React, { useState, useEffect } from "react";
import { Form, Button, Spinner } from "react-bootstrap";

/**
 * ConciergeGreeting Component
 * 
 * Displays a personalized greeting with a form to collect the user's name
 * for a more personalized experience during the session.
 * 
 * Props:
 * - onNameSubmit: Function to handle the submitted name
 */
const ConciergeGreeting = ({ onNameSubmit }) => {
  const [userName, setUserName] = useState("");
  const [submitDisabled, setSubmitDisabled] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [tipIndex, setTipIndex] = useState(0);
  
  const sbaTips = [
    "SBA offers resources for business planning, launching, managing, and growing your business.",
    "Did you know? SBA offers disaster assistance loans to help businesses recover from declared disasters.",
    "SBA's 7(a) loan program is their primary program for providing financial assistance to small businesses.",
    "The SBA Microloan program provides loans up to $50,000 to help small businesses start up and expand.",
    "SBA's 8(a) Business Development program helps socially and economically disadvantaged entrepreneurs.",
    "SCORE is an SBA resource partner offering free business mentoring and low-cost training."
  ];
  
  // Enable submit button only when name has content
  useEffect(() => {
    setSubmitDisabled(!userName.trim());
  }, [userName]);
  
  // Rotate tips every 5 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      setTipIndex((prevIndex) => (prevIndex + 1) % sbaTips.length);
    }, 5000);
    
    return () => clearInterval(timer);
  }, [sbaTips.length]);
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (userName.trim()) {
      setIsSubmitting(true);
      
      // Small delay to show the loading state
      setTimeout(() => {
        onNameSubmit(userName.trim());
        setIsSubmitting(false);
      }, 800);
    }
  };
  
  return (
    <div className="concierge-greeting">
      <div className="greeting-header">
        <h5>Welcome to PocketPro SBA Assistant</h5>
        <p>I'm your virtual concierge for SBA programs and resources!</p>
      </div>
      
      <div className="greeting-body">
        <p>To provide you with a personalized experience, I'd like to know your name.</p>
        
        <Form onSubmit={handleSubmit} className="name-form">
          <Form.Group controlId="userName">
            <Form.Label>What's your name?</Form.Label>
            <Form.Control
              type="text"
              placeholder="Enter your name"
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
              autoFocus
            />
          </Form.Group>
          
          <div className="sba-tip mt-3 mb-3">
            <small>
              <strong>SBA Tip:</strong> {sbaTips[tipIndex]}
            </small>
          </div>
          
          <Button 
            variant="primary" 
            type="submit" 
            className="mt-3"
            disabled={submitDisabled || isSubmitting}
          >
            {isSubmitting ? (
              <>
                <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" className="me-2" />
                Connecting...
              </>
            ) : (
              "Start Session"
            )}
          </Button>
        </Form>
      </div>
    </div>
  );
};

export default ConciergeGreeting;
