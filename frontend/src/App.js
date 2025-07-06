import React, { useState, useEffect, useRef } from 'react';
// Bootstrap components
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import Card from 'react-bootstrap/Card';
import Badge from 'react-bootstrap/Badge';
import Alert from 'react-bootstrap/Alert';
import Spinner from 'react-bootstrap/Spinner';
import Nav from 'react-bootstrap/Nav';
import Navbar from 'react-bootstrap/Navbar';
import Tab from 'react-bootstrap/Tab';
import Offcanvas from 'react-bootstrap/Offcanvas';
import ListGroup from 'react-bootstrap/ListGroup';
import InputGroup from 'react-bootstrap/InputGroup';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';

// Import components
import SBANavigation from './components/SBANavigation';
import RAGWorkflowInterface from './components/RAGWorkflowInterface';
import SBAContentExplorer from './components/SBAContentExplorer';
import ServerStatusMonitor from './components/ServerStatusMonitor';
import ErrorBoundary from './components/ErrorBoundary';
import APIErrorHandler from './components/APIErrorHandler';
import ConnectionStatusIndicator from './components/ConnectionStatusIndicator';
import LoadingIndicator from './components/LoadingIndicator';

// API endpoint
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('idle');
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);
  const [systemInfo, setSystemInfo] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(null);
  const [activeTab, setActiveTab] = useState('chat');
  const [searchResults, setSearchResults] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [showSidebar, setShowSidebar] = useState(false);
  const [screenSize, setScreenSize] = useState('');
  const chatBoxRef = useRef(null);
  
  // Add a message to the chat
  const addMessage = (content, isUser = false, type = 'text') => {
    const newMessage = {
      id: Date.now(),
      role: isUser ? 'user' : 'assistant',
      content,
      type,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, newMessage]);
  };
  
  // Handle responsive layout
  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      if (width < 576) {
        setScreenSize('xs');
      } else if (width >= 576 && width < 768) {
        setScreenSize('sm');
      } else if (width >= 768 && width < 992) {
        setScreenSize('md');
      } else if (width >= 992 && width < 1200) {
        setScreenSize('lg');
      } else {
        setScreenSize('xl');
      }
    };
    
    handleResize(); // Initial check
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Scroll to bottom of chat when new messages are added
  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [messages]);

  // Check server connection
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await fetch(`${API_URL}/api/health`);
        if (response.ok) {
          const data = await response.json();
          setConnected(true);
          setSystemInfo(data);
        } else {
          setConnected(false);
          setError('Server connection issue. Check the backend service.');
        }
      } catch (err) {
        setConnected(false);
        setError('Cannot connect to server. Is the backend running?');
      }
    };

    checkConnection();
    const interval = setInterval(checkConnection, 30000);
    return () => clearInterval(interval);
  }, []);

  // Handle chat submission
  const handleSubmit = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!input.trim() || loading) return;
    
    addMessage(input, true);
    setInput('');
    setLoading(true);
    setStatus('sending');
    
    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message: input,
          session_id: localStorage.getItem('session_id') || crypto.randomUUID()
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`);
      }
      
      const data = await response.json();
      
      // Handle different response formats
      const responseText = data.response || data.answer || data.message || 'No response from server';
      const sources = data.sources || data.context || [];
      
      setMessages(prevMessages => [
        ...prevMessages,
        {
          role: 'assistant',
          content: responseText,
          sources: sources,
          timestamp: data.timestamp || new Date().toISOString()
        }
      ]);
      
      if (sources && sources.length > 0) {
        setSearchResults(sources);
      }
      
      setStatus('idle');
    } catch (err) {
      console.error('Error sending message:', err);
      setMessages(prevMessages => [
        ...prevMessages,
        {
          role: 'assistant',
          content: `I'm having trouble connecting to the server right now. Please try again later or try a different question.`,
          error: true,
          timestamp: new Date().toISOString()
        }
      ]);
      setStatus('error');
    } finally {
      setLoading(false);
    }
  };

  // Handle file upload
  const handleFileUpload = async (file) => {
    if (!file) return;
    
    setUploadProgress(0);
    setStatus('uploading');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      // First check if the upload endpoint exists
      const healthCheck = await fetch(`${API_URL}/api/health`, { method: 'GET' });
      if (!healthCheck.ok) {
        throw new Error('Backend service is not available');
      }
      
      // Try the main upload endpoint
      let response;
      try {
        response = await fetch(`${API_URL}/api/files`, {
          method: 'POST',
          body: formData,
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(percentCompleted);
          }
        });
      } catch (uploadError) {
        // If the main endpoint fails, try the alternative endpoint
        console.warn('Primary upload endpoint failed, trying alternative:', uploadError);
        response = await fetch(`${API_URL}/api/documents/upload_and_ingest_document`, {
          method: 'POST',
          body: formData
        });
      }
      
      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`);
      }
      
      const data = await response.json();
      const documentInfo = data.document || { 
        id: Date.now(),
        filename: file.name,
        pages: 'Unknown',
        chunks: 'Unknown',
        uploadTime: new Date().toISOString()
      };
      
      setDocuments(prev => [...prev, documentInfo]);
      addMessage(`File '${file.name}' uploaded and processed successfully.`, false, 'system');
      setStatus('uploaded');
    } catch (err) {
      console.error('File upload error:', err);
      setError(`Error uploading file: ${err.message}`);
      addMessage(`Failed to upload file: ${err.message}. This feature may not be fully implemented in the current backend.`, false, 'error');
      setStatus('error');
    } finally {
      setUploadProgress(null);
    }
  };

  // Handle search within documents
  const handleSearch = async (query) => {
    if (!query.trim()) return;
    
    setLoading(true);
    setStatus('searching');
    
    try {
      const response = await fetch(`${API_URL}/api/search?query=${encodeURIComponent(query)}`);
      
      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`);
      }
      
      const data = await response.json();
      setSearchResults(data.results);
      setStatus('search_complete');
    } catch (err) {
      setError(`Error searching: ${err.message}`);
      setStatus('error');
    } finally {
      setLoading(false);
    }
  };

  // Handle RAG query with source retrieval
  const handleRAGQuery = async (query) => {
    if (!query.trim() || loading) return;
    
    addMessage(query, true);
    setLoading(true);
    setStatus('processing_rag');
    
    try {
      // First try with the /api/rag endpoint
      let response;
      try {
        response = await fetch(`${API_URL}/api/rag`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ query }),
        });
      } catch (ragError) {
        // If /api/rag fails, try the /api/chat endpoint
        console.warn('RAG endpoint failed, trying chat endpoint:', ragError);
        response = await fetch(`${API_URL}/api/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message: query }),
        });
      }
      
      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`);
      }
      
      const data = await response.json();
      
      // Handle different response formats
      const answer = data.answer || data.response || data.message || 'No response from server';
      const sources = data.sources || data.context || [];
      
      addMessage(answer, false, 'rag');
      setSearchResults(sources);
      setStatus('rag_complete');
    } catch (err) {
      console.error('RAG query error:', err);
      setError(`Error with RAG query: ${err.message}`);
      addMessage(`Sorry, there was an error processing your request: ${err.message}. Please try a different question or try again later.`, false, 'error');
      setStatus('error');
    } finally {
      setLoading(false);
    }
  };

  // Handle connection status change
  const handleConnectionChange = (newStatus, systemData) => {
    setConnected(newStatus);
    if (systemData) {
      setSystemInfo(systemData);
    }
    
    if (!newStatus) {
      setError('Server connection lost. Trying to reconnect...');
    } else if (newStatus && error && error.includes('connection')) {
      setError(null); // Clear connection errors when connection is restored
    }
  };

  // Retry any failed operations
  const retryLastOperation = async () => {
    if (status === 'error' && activeTab === 'chat') {
      // Retry last chat message
      const lastUserMessage = [...messages].reverse().find(m => m.role === 'user');
      if (lastUserMessage) {
        setInput(lastUserMessage.content);
        handleSubmit();
      }
    } else if (status === 'error' && activeTab === 'rag') {
      // Implement retry for RAG operations
      // This will depend on what specific operation failed
    }
  };

  return (
    <ErrorBoundary showDetails={true}>
      <div className="app-wrapper">
        <Navbar bg="primary" variant="dark" expand="lg" className="mb-3">
          <Container fluid>
            <Navbar.Brand href="#home">
              <img 
                src="/logo192.png" 
                width="30" 
                height="30" 
                className="d-inline-block align-top me-2" 
                alt="PocketPro SBA Logo" 
              />
              PocketPro SBA Assistant
            </Navbar.Brand>
            <Navbar.Toggle aria-controls="basic-navbar-nav" />
            <Navbar.Collapse id="basic-navbar-nav">
              <Nav className="me-auto">
                <Nav.Link 
                  href="#chat" 
                  active={activeTab === 'chat'}
                  onClick={() => setActiveTab('chat')}
                >
                  Chat
                </Nav.Link>
                <Nav.Link 
                  href="#rag" 
                  active={activeTab === 'rag'}
                  onClick={() => setActiveTab('rag')}
                >
                  RAG Workflow
                </Nav.Link>
                <Nav.Link 
                  href="#resources" 
                  active={activeTab === 'resources'}
                  onClick={() => setActiveTab('resources')}
                >
                  SBA Resources
                </Nav.Link>
                <Nav.Link 
                  href="#content" 
                  active={activeTab === 'content'}
                  onClick={() => setActiveTab('content')}
                >
                  Content Explorer
                </Nav.Link>
                <Nav.Link 
                  href="#documents" 
                  active={activeTab === 'documents'}
                  onClick={() => setActiveTab('documents')}
                >
                  Documents
                </Nav.Link>
              </Nav>
              <div className="d-flex align-items-center">
                <ConnectionStatusIndicator 
                  connected={connected}
                  systemInfo={systemInfo}
                  apiUrl={API_URL}
                  checkInterval={30000}
                  onConnectionChange={handleConnectionChange}
                />
              </div>
            </Navbar.Collapse>
          </Container>
        </Navbar>

        <Container fluid className="main-content">
          {/* Global error or alert messages */}
          {error && (
            <Row className="mb-3">
              <Col>
                <APIErrorHandler 
                  error={{ message: error }}
                  variant="danger"
                  onRetry={retryLastOperation}
                  dismissible={true}
                  resourceType="application"
                />
              </Col>
            </Row>
          )}
          
          {/* Main content area */}
          <Row>
            <Col xs={12} md={showSidebar ? 8 : 12} lg={showSidebar ? 9 : 12}>
              <Tab.Container activeKey={activeTab}>
                <Tab.Content>
                  <Tab.Pane eventKey="chat">
                    <Card className="chat-card">
                      <Card.Header className="d-flex justify-content-between align-items-center">
                        <h5 className="mb-0">Chat with PocketPro SBA Assistant</h5>
                        {loading && (
                          <LoadingIndicator 
                            type="dots" 
                            size="sm" 
                            text="" 
                            variant="primary" 
                          />
                        )}
                      </Card.Header>
                      <Card.Body>
                        {!connected && (
                          <ErrorBoundary>
                            <ServerStatusMonitor 
                              onStatusChange={(status, info) => {
                                setConnected(status === 'online');
                                if (info) setSystemInfo(info);
                              }} 
                            />
                          </ErrorBoundary>
                        )}
                        
                        <div className="chat-messages" ref={chatBoxRef}>
                          {messages.length === 0 ? (
                            <div className="text-center my-5">
                              <h4>Welcome to PocketPro SBA Assistant</h4>
                              <p>Ask any question about SBA programs and resources.</p>
                            </div>
                          ) : (
                            messages.map(message => (
                              <div 
                                key={message.id} 
                                className={`message ${message.role === 'user' ? 'user-message' : 'assistant-message'}`}
                              >
                                <div className="message-content">
                                  {message.type === 'loading' ? (
                                    <LoadingIndicator 
                                      type="dots" 
                                      size="sm"
                                      text="Thinking..." 
                                      variant={message.role === 'user' ? 'light' : 'primary'} 
                                    />
                                  ) : (
                                    <>{message.content}</>
                                  )}
                                </div>
                                <div className="message-metadata">
                                  <small>
                                    {message.role === 'user' ? 'You' : 'Assistant'} • 
                                    {new Date(message.timestamp).toLocaleTimeString()}
                                  </small>
                                </div>
                              </div>
                            ))
                          }
                          {loading && (
                            <div className="message assistant-message">
                              <div className="message-content">
                                <Spinner animation="border" size="sm" className="me-2" />
                                <span>Thinking...</span>
                              </div>
                            </div>
                          )}
                        </div>
                      </Card.Body>
                      <Card.Footer>
                        <Form onSubmit={handleSubmit}>
                          <InputGroup>
                            <Form.Control
                              type="text"
                              placeholder={connected ? "Type your message here..." : "Server connection required..."}
                              value={input}
                              onChange={(e) => setInput(e.target.value)}
                              disabled={loading || !connected}
                              aria-label="Message input"
                              aria-describedby="send-button"
                            />
                            <Button 
                              id="send-button"
                              variant="primary" 
                              type="submit" 
                              disabled={loading || !connected || !input.trim()}
                            >
                              {loading ? (
                                <Spinner animation="border" size="sm" role="status">
                                  <span className="visually-hidden">Loading...</span>
                                </Spinner>
                              ) : (
                                'Send'
                              )}
                            </Button>
                          </InputGroup>
                          
                          {/* Connection warning */}
                          {!connected && (
                            <Alert variant="warning" className="mt-2 mb-0 d-flex align-items-center">
                              <div className="me-2">
                                <i className="bi bi-exclamation-triangle-fill"></i>
                              </div>
                              <div>
                                Server connection issue. Trying to reconnect... 
                                <Button 
                                  variant="link" 
                                  className="p-0 ms-2" 
                                  onClick={() => window.location.reload()}
                                  size="sm"
                                >
                                  Refresh
                                </Button>
                              </div>
                            </Alert>
                          )}
                          
                          {/* Status indicator */}
                          {connected && status === 'sending' && (
                            <div className="text-muted mt-2 small d-flex align-items-center">
                              <Spinner animation="border" size="sm" className="me-2" />
                              Sending message...
                            </div>
                          )}
                          
                          {/* Error message for failed submission */}
                          {status === 'error' && (
                            <APIErrorHandler 
                              error={{ message: error || 'Failed to send message' }}
                              variant="danger"
                              onRetry={retryLastOperation}
                              dismissible={true}
                              resourceType="message"
                              className="mt-2 mb-0"
                            />
                          )}
                        </Form>
                      </Card.Footer>
                    </Card>
                  </Tab.Pane>
                  
                  <Tab.Pane eventKey="rag">
                    <RAGWorkflowInterface 
                      onSearch={handleSearch}
                      onUpload={handleFileUpload}
                      onQuery={handleRAGQuery}
                      documents={documents}
                      searchResults={searchResults}
                      ragResponse={messages.filter(m => m.type === 'rag').pop()}
                    />
                  </Tab.Pane>
                  
                  <Tab.Pane eventKey="resources">
                    <SBANavigation 
                      onProgramSelect={(programId) => {
                        setInput(`Tell me about ${programId} SBA program`);
                        handleSubmit({ preventDefault: () => {} });
                        setActiveTab('chat');
                      }}
                      onResourceSelect={(resourceId) => {
                        setInput(`What resources are available for ${resourceId}?`);
                        handleSubmit({ preventDefault: () => {} });
                        setActiveTab('chat');
                      }}
                    />
                  </Tab.Pane>
                  
                  <Tab.Pane eventKey="content">
                    <SBAContentExplorer />
                  </Tab.Pane>
                  
                  <Tab.Pane eventKey="documents">
                    <Card>
                      <Card.Header>
                        <h5 className="mb-0">Uploaded Documents</h5>
                      </Card.Header>
                      <Card.Body>
                        {documents.length === 0 ? (
                          <Alert variant="info">
                            No documents uploaded yet. Go to the RAG Workflow tab to upload documents.
                          </Alert>
                        ) : (
                          <ListGroup>
                            {documents.map((doc, index) => (
                              <ListGroup.Item key={index}>
                                <div className="d-flex justify-content-between align-items-center">
                                  <div>
                                    <h6 className="mb-0">{doc.filename}</h6>
                                    <small className="text-muted">
                                      {doc.pages} pages • {doc.chunks} chunks
                                    </small>
                                  </div>
                                  <Button 
                                    variant="outline-primary" 
                                    size="sm"
                                    onClick={() => {
                                      setInput(`Summarize the document ${doc.filename}`);
                                      handleSubmit({ preventDefault: () => {} });
                                      setActiveTab('chat');
                                    }}
                                  >
                                    Query
                                  </Button>
                                </div>
                              </ListGroup.Item>
                            ))}
                          </ListGroup>
                        )}
                      </Card.Body>
                      <Card.Footer>
                        <Button 
                          variant="primary" 
                          onClick={() => setActiveTab('rag')}
                        >
                          Upload New Document
                        </Button>
                      </Card.Footer>
                    </Card>
                  </Tab.Pane>
                </Tab.Content>
              </Tab.Container>
            </Col
            
            {showSidebar && (
              <Col xs={12} md={4} lg={3} className="sidebar-col">
                <Card className="system-info">
                  <Card.Header>
                    <h5 className="mb-0">System Information</h5>
                  </Card.Header>
                  <Card.Body>
                    {systemInfo ? (
                      <>
                        <p><strong>Status:</strong> {connected ? 'Online' : 'Offline'}</p>
                        <p><strong>Version:</strong> {systemInfo.version || 'Unknown'}</p>
                        <p><strong>Model:</strong> {systemInfo.model || 'Not specified'}</p>
                        <p><strong>Documents:</strong> {documents.length}</p>
                        <p><strong>Screen Size:</strong> {screenSize}</p>
                      </>
                    ) : (
                      <Spinner animation="border" />
                    )}
                  </Card.Body>
                </Card>
                
                {searchResults.length > 0 && (
                  <Card className="mt-3">
                    <Card.Header>
                      <h5 className="mb-0">Search Results</h5>
                    </Card.Header>
                    <Card.Body>
                      <ListGroup>
                        {searchResults.slice(0, 5).map((result, index) => (
                          <ListGroup.Item key={index}>
                            <h6>{result.title || `Result ${index + 1}`}</h6>
                            <p className="mb-1">{result.content.substring(0, 100)}...</p>
                            <Badge bg="info">Score: {(result.score * 100).toFixed(1)}%</Badge>
                          </ListGroup.Item>
                        ))}
                      </ListGroup>
                    </Card.Body>
                  </Card>
                )}
              </Col>
            )}
          </Row>
        </Container>
        
        {/* Mobile sidebar as offcanvas for small screens */}
        <Offcanvas 
          show={showSidebar && (screenSize === 'xs' || screenSize === 'sm')} 
          onHide={() => setShowSidebar(false)}
          placement="end"
        >
          <Offcanvas.Header closeButton>
            <Offcanvas.Title>System Information</Offcanvas.Title>
          </Offcanvas.Header>
          <Offcanvas.Body>
            {systemInfo ? (
              <>
                <p><strong>Status:</strong> {connected ? 'Online' : 'Offline'}</p>
                <p><strong>Version:</strong> {systemInfo.version || 'Unknown'}</p>
                <p><strong>Model:</strong> {systemInfo.model || 'Not specified'}</p>
                <p><strong>Documents:</strong> {documents.length}</p>
              </>
            ) : (
              <Spinner animation="border" />
            )}
            
            {searchResults.length > 0 && (
              <div className="mt-4">
                <h5>Search Results</h5>
                <ListGroup>
                  {searchResults.slice(0, 3).map((result, index) => (
                    <ListGroup.Item key={index}>
                      <h6>{result.title || `Result ${index + 1}`}</h6>
                      <p className="mb-1">{result.content.substring(0, 50)}...</p>
                      <Badge bg="info">Score: {(result.score * 100).toFixed(1)}%</Badge>
                    </ListGroup.Item>
                  ))}
                </ListGroup>
              </div>
            )}
          </Offcanvas.Body>
        </Offcanvas>
      </div>
    </ErrorBoundary>
  );
}

export default App;
