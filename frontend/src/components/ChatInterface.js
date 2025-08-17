import React, { useState } from 'react';
import { Container, Row, Col, Card, Form, Button } from 'react-bootstrap';
import '../styles/mobile-card-layout.css';

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');

  const handleSend = () => {
    if (inputText.trim()) {
      setMessages([...messages, { text: inputText, sender: 'user' }]);
      setInputText('');
      // Simulate response
      setTimeout(() => {
        setMessages(prev => [...prev, { text: 'Response from assistant', sender: 'assistant' }]);
      }, 1000);
    }
  };

  return (
    <div className="chat-container">
      <Container fluid>
        <Row>
          <Col>
            <div className="chat-messages">
              {messages.map((message, index) => (
                <Card key={index} className={`message-card ${message.sender}`}>
                  <Card.Body>
                    <p className="mb-0">{message.text}</p>
                  </Card.Body>
                </Card>
              ))}
            </div>
            <div className="chat-input-container">
              <Form onSubmit={(e) => { e.preventDefault(); handleSend(); }}>
                <Row>
                  <Col>
                    <Form.Control
                      type="text"
                      value={inputText}
                      onChange={(e) => setInputText(e.target.value)}
                      placeholder="Type your message..."
                      className="shadow-sm"
                    />
                  </Col>
                  <Col xs="auto">
                    <Button type="submit" className="shadow-md">
                      Send
                    </Button>
                  </Col>
                </Row>
              </Form>
            </div>
          </Col>
        </Row>
      </Container>
    </div>
  );
};

export default ChatInterface;
