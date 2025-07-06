import React from 'react';
import { ProgressBar, Row, Col, Card } from 'react-bootstrap';

const RAGWorkflowVisualization = ({ activeStep }) => {
  // Define the steps in the RAG workflow with icons
  const workflowSteps = [
    { 
      id: 'upload', 
      name: 'Document Upload', 
      description: 'Upload and process documents',
      icon: '📄'
    },
    { 
      id: 'index', 
      name: 'Indexing', 
      description: 'Create vector embeddings',
      icon: '🔍'
    },
    { 
      id: 'query', 
      name: 'Query', 
      description: 'Ask questions about your documents',
      icon: '❓'
    },
    { 
      id: 'retrieve', 
      name: 'Retrieval', 
      description: 'Find relevant context',
      icon: '📚'
    },
    { 
      id: 'generate', 
      name: 'Generation', 
      description: 'Generate AI response',
      icon: '🤖'
    }
  ];

  // Determine progress percentage based on active step
  const getProgressPercentage = () => {
    const stepIndex = workflowSteps.findIndex(step => step.id === activeStep);
    if (stepIndex === -1) return 0;
    return ((stepIndex + 1) / workflowSteps.length) * 100;
  };

  return (
    <Card className="rag-workflow-visualization">
      <Card.Body>
        <ProgressBar 
          now={getProgressPercentage()} 
          className="mb-4" 
          variant="primary" 
          animated
        />
        
        <Row xs={1} md={5} className="workflow-steps g-2">
          {workflowSteps.map(step => (
            <Col key={step.id}>
              <div 
                className={`workflow-step text-center p-2 rounded ${step.id === activeStep ? 'active bg-light' : ''}`}
                style={{ opacity: step.id === activeStep ? 1 : 0.6 }}
              >
                <div className="workflow-step-icon mb-2">{step.icon}</div>
                <h6 className="mb-1">{step.name}</h6>
                <p className="small text-muted mb-0">{step.description}</p>
              </div>
            </Col>
          ))}
        </Row>
      </Card.Body>
    </Card>
  );
};

export default RAGWorkflowVisualization;
