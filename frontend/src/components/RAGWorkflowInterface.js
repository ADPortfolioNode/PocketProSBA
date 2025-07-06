import React, { useState } from 'react';
import RAGWorkflowVisualization from './RAGWorkflowVisualization';
import { Card, Row, Col, Button, Form, ListGroup, Badge, Accordion, Alert, ProgressBar } from 'react-bootstrap';

const RAGWorkflowInterface = ({ 
  onSearch, 
  onUpload, 
  onQuery, 
  documents,
  searchResults,
  ragResponse
}) => {
  const [currentStep, setCurrentStep] = useState('upload');
  const [queryText, setQueryText] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [activeDocument, setActiveDocument] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(null);
  
  const handleStepChange = (step) => {
    setCurrentStep(step);
  };
  
  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };
  
  const handleUpload = () => {
    if (selectedFile) {
      setUploadProgress(0);
      const fakeProgress = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(fakeProgress);
            return prev;
          }
          return prev + 10;
        });
      }, 300);
      
      onUpload(selectedFile).catch(err => {
        console.error('Upload error in RAGWorkflowInterface:', err);
        setCurrentStep('upload'); // Go back to upload step on error
      });
    }
  };
  
  const handleSearch = (e) => {
    e.preventDefault();
    if (queryText.trim()) {
      onSearch(queryText);
      setCurrentStep('retrieve'); // Move to the retrieval step
    }
  };
  
  const handleRAGQuery = (e) => {
    e.preventDefault();
    if (queryText.trim()) {
      onQuery(queryText);
      setCurrentStep('generate'); // Move to the generation step
    }
  };
  
  const renderStepContent = () => {
    switch(currentStep) {
      case 'upload':
        return (
          <Card className="mb-3">
            <Card.Header>
              <h5 className="mb-0">Upload Documents</h5>
            </Card.Header>
            <Card.Body>
              <p className="mb-3">
                Upload PDF, DOCX, or TXT files to enable the assistant to search and answer questions based on your documents.
              </p>
              
              <Form.Group controlId="fileUpload" className="mb-3">
                <Form.Label>Select a document to upload</Form.Label>
                <Form.Control 
                  type="file" 
                  onChange={handleFileSelect}
                  accept=".pdf,.docx,.txt"
                />
                <Form.Text className="text-muted">
                  Supported file types: PDF, DOCX, and TXT
                </Form.Text>
              </Form.Group>
              
              {documents.length > 0 && (
                <div className="mt-3 mb-3">
                  <h6>Previously Uploaded Documents</h6>
                  <ListGroup>
                    {documents.map((doc, index) => (
                      <ListGroup.Item key={index} className="d-flex justify-content-between align-items-center">
                        <div>
                          <strong>{doc.filename}</strong>
                          <Badge bg="info" className="ms-2">{doc.pages} pages</Badge>
                        </div>
                        <Button 
                          variant="outline-primary" 
                          size="sm"
                          onClick={() => setActiveDocument(doc)}
                        >
                          View
                        </Button>
                      </ListGroup.Item>
                    ))}
                  </ListGroup>
                </div>
              )}
              
              {uploadProgress !== null && (
                <ProgressBar animated now={uploadProgress} className="mt-3" />
              )}
              
              <div className="d-flex justify-content-between mt-4">
                <Button 
                  variant="outline-secondary" 
                  disabled
                >
                  Previous
                </Button>
                <Button 
                  variant="primary" 
                  onClick={handleUpload}
                  disabled={!selectedFile}
                >
                  Upload & Continue
                </Button>
              </div>
            </Card.Body>
          </Card>
        );
        
      case 'index':
        return (
          <Card className="mb-3">
            <Card.Header>
              <h5 className="mb-0">Document Indexing</h5>
            </Card.Header>
            <Card.Body>
              <Alert variant="success">
                <Alert.Heading>Document Processing Complete!</Alert.Heading>
                <p>
                  Your document has been successfully uploaded and processed. The document has been chunked and indexed for semantic search.
                </p>
              </Alert>
              
              <Accordion className="mb-4">
                <Accordion.Item eventKey="0">
                  <Accordion.Header>What happens during indexing?</Accordion.Header>
                  <Accordion.Body>
                    <p>During the indexing process, the document is:</p>
                    <ol>
                      <li>Split into smaller chunks for efficient processing</li>
                      <li>Converted into vector embeddings using advanced AI models</li>
                      <li>Stored in a vector database for fast semantic retrieval</li>
                      <li>Optimized for natural language queries</li>
                    </ol>
                  </Accordion.Body>
                </Accordion.Item>
              </Accordion>
              
              <div className="d-flex justify-content-between mt-4">
                <Button 
                  variant="outline-secondary" 
                  onClick={() => handleStepChange('upload')}
                >
                  Back to Upload
                </Button>
                <Button 
                  variant="primary" 
                  onClick={() => handleStepChange('query')}
                >
                  Continue to Query
                </Button>
              </div>
            </Card.Body>
          </Card>
        );
        
      case 'query':
        return (
          <Card className="mb-3">
            <Card.Header>
              <h5 className="mb-0">Ask Questions About Your Documents</h5>
            </Card.Header>
            <Card.Body>
              <p className="mb-3">
                Ask any question about the content of your uploaded documents. The system will retrieve the most relevant information and generate an answer.
              </p>
              
              <Form onSubmit={handleRAGQuery} className="mb-4">
                <Form.Group controlId="queryInput" className="mb-3">
                  <Form.Label>Your Question</Form.Label>
                  <Form.Control
                    as="textarea"
                    rows={3}
                    placeholder="e.g., What types of SBA loans are available for small businesses?"
                    value={queryText}
                    onChange={(e) => setQueryText(e.target.value)}
                  />
                </Form.Group>
                
                <div className="d-grid gap-2">
                  <Button 
                    variant="primary" 
                    type="submit"
                    disabled={!queryText.trim()}
                  >
                    Search & Generate Answer
                  </Button>
                </div>
              </Form>
              
              <div className="d-flex justify-content-between mt-4">
                <Button 
                  variant="outline-secondary" 
                  onClick={() => handleStepChange('index')}
                >
                  Previous
                </Button>
                <Button 
                  variant="outline-primary" 
                  onClick={() => handleStepChange('retrieve')}
                  disabled={!queryText.trim()}
                >
                  Skip to Retrieval
                </Button>
              </div>
            </Card.Body>
          </Card>
        );
        
      case 'retrieve':
        return (
          <Card className="mb-3">
            <Card.Header>
              <h5 className="mb-0">Retrieved Context</h5>
            </Card.Header>
            <Card.Body>
              <p className="mb-3">
                These are the most relevant passages retrieved from your documents based on your query.
              </p>
              
              {searchResults.length > 0 ? (
                <ListGroup className="mb-4">
                  {searchResults.map((result, index) => (
                    <ListGroup.Item key={index}>
                      <h6>Source: {result.source || "Document " + (index + 1)}</h6>
                      <p>{result.content}</p>
                      <div className="d-flex justify-content-between align-items-center">
                        <Badge bg="info">Relevance: {(result.score * 100).toFixed(1)}%</Badge>
                        <small className="text-muted">Chunk {result.chunk_id || index}</small>
                      </div>
                    </ListGroup.Item>
                  ))}
                </ListGroup>
              ) : (
                <Alert variant="warning">
                  No relevant contexts found. Try refining your query or uploading more documents.
                </Alert>
              )}
              
              <div className="d-flex justify-content-between mt-4">
                <Button 
                  variant="outline-secondary" 
                  onClick={() => handleStepChange('query')}
                >
                  Back to Query
                </Button>
                <Button 
                  variant="primary" 
                  onClick={() => handleStepChange('generate')}
                  disabled={searchResults.length === 0}
                >
                  Generate Answer
                </Button>
              </div>
            </Card.Body>
          </Card>
        );
        
      case 'generate':
        return (
          <Card className="mb-3">
            <Card.Header>
              <h5 className="mb-0">Generated Response</h5>
            </Card.Header>
            <Card.Body>
              <p className="mb-3">
                Based on the retrieved context, here is the AI-generated answer to your query.
              </p>
              
              {ragResponse ? (
                <Card className="mb-4 bg-light">
                  <Card.Body>
                    <Card.Title className="text-primary">Query</Card.Title>
                    <Card.Text className="mb-3">{queryText}</Card.Text>
                    
                    <Card.Title className="text-primary">Response</Card.Title>
                    <Card.Text style={{ whiteSpace: 'pre-line' }}>{ragResponse.content}</Card.Text>
                  </Card.Body>
                </Card>
              ) : (
                <Alert variant="info">
                  No response generated yet. Submit a query to see results.
                </Alert>
              )}
              
              <div className="d-flex justify-content-between mt-4">
                <Button 
                  variant="outline-secondary" 
                  onClick={() => handleStepChange('retrieve')}
                >
                  Back to Retrieved Context
                </Button>
                <Button 
                  variant="primary" 
                  onClick={() => {
                    setQueryText('');
                    handleStepChange('query');
                  }}
                >
                  Ask Another Question
                </Button>
              </div>
            </Card.Body>
          </Card>
        );
        
      default:
        return null;
    }
  };
  
  return (
    <div className="rag-workflow-container">
      <h3 className="mb-4 text-center">RAG Workflow Interface</h3>
      
      <Row className="mb-4">
        <Col>
          <RAGWorkflowVisualization activeStep={currentStep} />
        </Col>
      </Row>
      
      <Row>
        <Col>
          {renderStepContent()}
        </Col>
      </Row>
    </div>
  );
};

export default RAGWorkflowInterface;
