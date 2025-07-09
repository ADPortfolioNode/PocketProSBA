import React from 'react';
import { Navbar, Nav, Container } from 'react-bootstrap';
import ConnectionStatusIndicator from './ConnectionStatusIndicator';

const SBANavigation = ({ activeTab, onTabChange, serverConnected }) => {
  return (
    <Navbar bg="light" expand="lg" className="mb-4 main-navbar">
      <Container>
        <Navbar.Brand href="#home">PocketPro SBA Assistant</Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="me-auto">
            <Nav.Link 
              href="#chat" 
              active={activeTab === "chat"}
              onClick={(e) => {
                e.preventDefault();
                onTabChange("chat");
              }}
            >
              Chat
            </Nav.Link>
            <Nav.Link 
              href="#browse" 
              active={activeTab === "browse"}
              onClick={(e) => {
                e.preventDefault();
                onTabChange("browse");
              }}
            >
              Browse Resources
            </Nav.Link>
            <Nav.Link 
              href="#rag" 
              active={activeTab === "rag"}
              onClick={(e) => {
                e.preventDefault();
                onTabChange("rag");
              }}
            >
              RAG
            </Nav.Link>
            <Nav.Link 
              href="#documents" 
              active={activeTab === "documents"}
              onClick={(e) => {
                e.preventDefault();
                onTabChange("documents");
              }}
            >
              Document Center
            </Nav.Link>
          </Nav>
          <div className="d-flex align-items-center">
            <ConnectionStatusIndicator connected={serverConnected} />
          </div>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default SBANavigation;
