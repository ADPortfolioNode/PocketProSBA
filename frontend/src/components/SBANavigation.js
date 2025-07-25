import React from 'react';
import { Navbar, Nav, Container } from 'react-bootstrap';
import PropTypes from 'prop-types';
import ConnectionStatusIndicator from './ConnectionStatusIndicator';

const SBANavigation = ({ activeTab, onTabChange, serverConnected, apiUrl }) => {
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
            <Nav.Link 
              href="#sba" 
              active={activeTab === "sba"}
              onClick={(e) => {
                e.preventDefault();
                onTabChange("sba");
              }}
            >
              SBA Content
            </Nav.Link>
          </Nav>
          <div className="d-flex align-items-center">
            <ConnectionStatusIndicator connected={serverConnected} apiUrl={apiUrl} />
          </div>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

SBANavigation.propTypes = {
  activeTab: PropTypes.string.isRequired,
  onTabChange: PropTypes.func.isRequired,
  serverConnected: PropTypes.bool.isRequired,
  apiUrl: PropTypes.func.isRequired
};

export default SBANavigation;
