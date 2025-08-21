import React, { useState, useEffect } from 'react';
import { businessLifecycleStages, localResourceTypes } from '../sbaResources';
import apiClient from '../api/apiClient'; // Corrected import path
import { Card, Nav, Row, Col, Container, Badge } from 'react-bootstrap';

const SBAContent = ({ onProgramSelect, onResourceSelect }) => {
  const [activeTab, setActiveTab] = useState('programs');
  const [programs, setPrograms] = useState([]);

  useEffect(() => {
    // Load SBA programs from backend endpoint on mount
    async function fetchPrograms() {
      try {
        const response = await apiClient.get('programs'); // Use apiClient.get
        setPrograms(response.data);
      } catch (err) {
        setPrograms([]);
        // Optionally log or show error
      }
    }
    fetchPrograms();
  }, []);

  return (
    <Card className="sba-content-explorer">
      <Card.Header>
        <Nav variant="tabs" className="navigation-tabs">
          <Nav.Item>
            <Nav.Link 
              active={activeTab === 'programs'}
              onClick={() => setActiveTab('programs')}
            >
              SBA Programs
            </Nav.Link>
          </Nav.Item>
          <Nav.Item>
            <Nav.Link 
              active={activeTab === 'lifecycle'}
              onClick={() => setActiveTab('lifecycle')}
            >
              Business Lifecycle
            </Nav.Link>
          </Nav.Item>
          <Nav.Item>
            <Nav.Link 
              active={activeTab === 'local'}
              onClick={() => setActiveTab('local')}
            >
              Local Resources
            </Nav.Link>
          </Nav.Item>
        </Nav>
      </Card.Header>
      
      <Card.Body className="content-explorer-body">
        {activeTab === 'programs' && (
          <Container fluid>
            <Row xs={1} md={2} lg={3} className="g-3">
              {programs.map(program => (
                <Col key={program.id}>
                  <Card 
                    className="program-card h-100" 
                    onClick={() => onProgramSelect && onProgramSelect(program.id)}
                  >
                    <Card.Body className="d-flex">
                      <div className="program-icon me-3">{program.icon || '💼'}</div>
                      <div className="program-content">
                        <Card.Title as="h5">{program.name}</Card.Title>
                        <Card.Text className="small text-muted">{program.description}</Card.Text>
                      </div>
                    </Card.Body>
                  </Card>
                </Col>
              ))}
            </Row>
          </Container>
        )}
        
        {activeTab === 'lifecycle' && (
          <Container fluid>
            <Row xs={1} md={2} lg={3} className="g-3">
              {businessLifecycleStages.map(stage => (
                <Col key={stage.id}>
                  <Card 
                    className="lifecycle-card h-100" 
                    onClick={() => onResourceSelect && onResourceSelect(`${stage.id} stage`)}
                  >
                    <Card.Body className="d-flex">
                      <div className="lifecycle-icon me-3">{stage.icon}</div>
                      <div className="lifecycle-content">
                        <Card.Title as="h5">{stage.name}</Card.Title>
                        <Card.Text className="small text-muted">{stage.description}</Card.Text>
                        <Badge bg="info" pill className="mt-2">{stage.phase}</Badge>
                      </div>
                    </Card.Body>
                  </Card>
                </Col>
              ))}
            </Row>
          </Container>
        )}
        
        {activeTab === 'local' && (
          <Container fluid>
            <Row xs={1} md={2} lg={3} className="g-3">
              {localResourceTypes.map(resource => (
                <Col key={resource.id}>
                  <Card 
                    className="resource-card h-100" 
                    onClick={() => onResourceSelect && onResourceSelect(`${resource.id} resources`)}
                  >
                    <Card.Body className="d-flex">
                      <div className="resource-icon me-3">{resource.icon}</div>
                      <div className="resource-content">
                        <Card.Title as="h5">{resource.name}</Card.Title>
                        <Card.Text className="small text-muted">{resource.description}</Card.Text>
                      </div>
                    </Card.Body>
                  </Card>
                </Col>
              ))}
            </Row>
          </Container>
        )}
      </Card.Body>
    </Card>
  );
};

export default SBAContent;
