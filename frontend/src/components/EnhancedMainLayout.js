import React, { useState } from 'react';
import { Container, Row, Col, Card, Button, Navbar, Nav } from 'react-bootstrap';
import '../styles/mobile-card-layout.css';

const EnhancedMainLayout = ({ children, title = "PocketPro SBA" }) => {
  const [activeTab, setActiveTab] = useState('chat');

  return (
    <div className="enhanced-main-layout">
      <Navbar bg="light" expand="lg" className="shadow-lg">
        <Container>
          <Navbar.Brand href="/" className="navbar-brand">
            <i className="bi bi-lightning-charge-fill me-2"></i>
            {title}
          </Navbar.Brand>
          <Navbar.Toggle aria-controls="basic-navbar-nav" />
          <Navbar.Collapse id="basic-navbar-nav">
            <Nav className="ms-auto">
              <Nav.Link href="/chat" className="nav-link">
                <i className="bi bi-chat-dots me-1"></i>
                Chat
              </Nav.Link>
              <Nav.Link href="/resources" className="nav-link">
                <i className="bi bi-book me-1"></i>
                Resources
              </Nav.Link>
              <Nav.Link href="/profile" className="nav-link">
                <i className="bi bi-person me-1"></i>
                Profile
              </Nav.Link>
            </Nav>
          </Navbar.Collapse>
        </Container>
      </Navbar>

      <main className="main-content">
        <Container fluid>
          <Row>
            <Col>
              <div className="flex-container">
                <Card className="shadow-lg">
                  <Card.Header className="gradient-overlay">
                    <h5 className="mb-0 text-white">{title}</h5>
                  </Card.Header>
                  <Card.Body>
                    {children}
                  </Card.Body>
                </Card>
              </div>
            </Col>
          </Row>
        </Container>
      </main>
    </div>
  );
};

export default EnhancedMainLayout;
