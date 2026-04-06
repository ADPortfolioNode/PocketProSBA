 import React from 'react';
import { Navbar, Nav, Container } from 'react-bootstrap';
import { Link, useLocation } from 'react-router-dom';
import PropTypes from 'prop-types';
import ConnectionStatusIndicator from './ConnectionStatusIndicator';

const SBANavigation = ({ serverConnected, apiUrl }) => {
  const location = useLocation();
  const currentPath = location.pathname.toLowerCase();

  return (
    <Navbar bg="light" expand="lg" className="mb-4 main-navbar">
      <Container>
        <Navbar.Brand as={Link} to="/">Home</Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="me-auto">
            <Nav.Link
              as={Link}
              to="/chat"
              active={currentPath === '/chat'}
              data-testid="nav-chat"
            >
              Chat
            </Nav.Link>
            <Nav.Link
              as={Link}
              to="/browse"
              active={currentPath === '/browse'}
              data-testid="nav-browse"
            >
              Browse Resources
            </Nav.Link>
            <Nav.Link
              as={Link}
              to="/rag"
              active={currentPath === '/rag'}
              data-testid="nav-rag"
            >
              RAG
            </Nav.Link>
            <Nav.Link
              as={Link}
              to="/documents"
              active={currentPath === '/documents'}
              data-testid="nav-documents"
            >
              Document Center
            </Nav.Link>
            <Nav.Link
              as={Link}
              to="/sba"
              active={currentPath === '/sba'}
              data-testid="nav-sba"
            >
              SBA Content
            </Nav.Link>
            <Nav.Link
              as={Link}
              to="/orchestrator"
              active={currentPath === '/orchestrator'}
              data-testid="nav-orchestrator"
            >
              🤖 Task Orchestrator
            </Nav.Link>
            <Nav.Link
              href="#team"
              active={activeTab === "team"}
              onClick={(e) => {
                e.preventDefault();
                onTabChange("team");
              }}
              data-testid="nav-team"
            >
              🎯 Team Workflow
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
  serverConnected: PropTypes.bool.isRequired,
  apiUrl: PropTypes.oneOfType([PropTypes.func, PropTypes.string]).isRequired
};

export default SBANavigation;
