import React from 'react';

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

  return (
    <div className="rag-workflow">
      <h3>RAG Workflow Visualization</h3>
      <p className="workflow-description">
        Retrieval-Augmented Generation (RAG) combines document retrieval with AI text generation for accurate, contextual responses
      </p>
      <div className="workflow-visualization">
        {workflowSteps.map((step, index) => (
          <React.Fragment key={step.id}>
            <div 
              className={`workflow-step ${activeStep === step.id ? 'active' : ''} ${
                // If no active step is set, don't highlight any specific step
                !activeStep ? '' : 
                // Steps before the active step are considered "completed"
                workflowSteps.findIndex(s => s.id === activeStep) > index ? 'completed' : ''
              }`}
            >
              <div className="step-icon">{step.icon}</div>
              <div className="step-number">{index + 1}</div>
              <div className="step-content">
                <h4>{step.name}</h4>
                <p>{step.description}</p>
              </div>
              {activeStep === step.id && (
                <div className="step-indicator">Current</div>
              )}
            </div>
            {index < workflowSteps.length - 1 && (
              <div className={`workflow-connector ${
                !activeStep ? '' :
                workflowSteps.findIndex(s => s.id === activeStep) > index ? 'completed' : ''
              }`}></div>
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

export default RAGWorkflowVisualization;
