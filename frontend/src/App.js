import React, { useState, useEffect, useRef } from 'react';
import { Container, Row, Col, Form, Button, Card, Badge, Alert, Spinner } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';

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
  const chatBoxRef = useRef(null);

  // Fetch system info
  useEffect(() => {
    fetchSystemInfo();
  }, []);

  // Scroll to bottom of chat box when messages change
  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [messages]);

  // Fetch system info
  const fetchSystemInfo = async () => {
    try {
      const response = await fetch(`${API_URL}/api/info`);
      const data = await response.json();
      setSystemInfo(data);
    } catch (err) {
      console.error('Error fetching system info:', err);
      setError('Failed to fetch system information');
    }
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Add user message to chat
    setMessages(prevMessages => [
      ...prevMessages,
      { role: 'user', content: input, timestamp: new Date().toISOString() }
    ]);

    // Clear input and show loading state
    setInput('');
    setLoading(true);
    setStatus('processing');

    try {
      // Send message to API
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

      // Handle API response
      if (response.ok) {
        const data = await response.json();
        
        setMessages(prevMessages => [
          ...prevMessages,
          {
            role: 'assistant',
            content: data.response,
            sources: data.sources,
            timestamp: data.timestamp
          }
        ]);
        setStatus('idle');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to send message');
      }
    } catch (err) {
      console.error('Error sending message:', err);
      setMessages(prevMessages => [
        ...prevMessages,
        {
          role: 'assistant',
          content: `Error: ${err.message}. Please try again later.`,
          error: true,
          timestamp: new Date().toISOString()
        }
      ]);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container fluid className="app-container">
      <Row className="header">
        <Col>
          <h1 className="text-center my-4">PocketPro: SBA Edition</h1>
          {systemInfo && (
            <div className="text-center mb-3">
              <Badge bg="info" className="mx-1">
                Version: {systemInfo.version}
              </Badge>
              <Badge bg={systemInfo.rag_status === 'available' ? 'success' : 'warning'} className="mx-1">
                RAG: {systemInfo.rag_status}
              </Badge>
              <Badge bg="secondary" className="mx-1">
                Documents: {systemInfo.document_count}
              </Badge>
            </div>
          )}
        </Col>
      </Row>

      {error && (
        <Row className="mb-3">
          <Col>
            <Alert variant="danger" onClose={() => setError(null)} dismissible>
              {error}
            </Alert>
          </Col>
        </Row>
      )}

      <Row>
        <Col>
          <Card className="chat-card">
            <Card.Header>
              <div className="d-flex justify-content-between align-items-center">
                <div className="d-flex align-items-center">
                  <div className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}></div>
                  <span className="ms-2">
                    {connected ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
                <div>
                  <Badge bg={status === 'idle' ? 'success' : 'warning'}>
                    {status === 'processing' ? (
                      <>
                        <Spinner animation="border" size="sm" className="me-1" />
                        Processing
                      </>
                    ) : (
                      status.charAt(0).toUpperCase() + status.slice(1)
                    )}
                  </Badge>
                </div>
              </div>
            </Card.Header>
            <Card.Body className="chat-container" ref={chatBoxRef}>
              {messages.length === 0 ? (
                <div className="text-center text-muted my-5">
                  <h5>Welcome to PocketPro:SBA Edition</h5>
                  <p>Ask me anything about small business resources and SBA programs!</p>
                </div>
              ) : (
                messages.map((message, index) => (
                  <div key={index} className={`message message-${message.role}`}>
                    <div className="message-content">{message.content}</div>
                    {message.sources && message.sources.length > 0 && (
                      <div className="message-sources">
                        <small>
                          <strong>Sources:</strong>
                          <ul>
                            {message.sources.map((source, idx) => (
                              <li key={idx}>{source.name || `Source ${idx + 1}`}</li>
                            ))}
                          </ul>
                        </small>
                      </div>
                    )}
                  </div>
                ))
              )}
              {loading && (
                <div className="text-center my-2">
                  <Spinner animation="border" role="status" size="sm">
                    <span className="visually-hidden">Loading...</span>
                  </Spinner>
                </div>
              )}
            </Card.Body>
            <Card.Footer>
              <Form onSubmit={handleSubmit}>
                <div className="d-flex">
                  <Form.Control
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Type your message here..."
                    disabled={loading}
                  />
                  <Button variant="primary" type="submit" disabled={loading || !input.trim()} className="ms-2">
                    {loading ? <Spinner animation="border" size="sm" /> : 'Send'}
                  </Button>
                </div>
              </Form>
            </Card.Footer>
          </Card>
        </Col>
      </Row>

      <Row className="footer">
        <Col className="text-center mt-4">
          <p className="text-muted">
            &copy; {new Date().getFullYear()} PocketPro:SBA Edition by StainlessDeoism.biz
          </p>
        </Col>
      </Row>
    </Container>
  );
}

export default App;

export default App;
      });
      
      setTimeout(() => setUploadProgress(null), 5000);
      addMessage(`❌ Batch upload failed: ${error.message}`, false, 'error');
    }
  };
  
  const handleDocumentDelete = async (documentId) => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
      const response = await fetch(`${backendUrl}/api/documents/${documentId}`, {
        method: 'DELETE'
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Update document list
        await fetchDocuments();
        await fetchCollectionStats();
        
        // If the deleted document was selected, clear selection
        if (selectedDocument && selectedDocument.id === documentId) {
          setSelectedDocument(null);
          setDocumentChunks([]);
        }
        
        addMessage(`✅ Document deleted successfully.`, false, 'system');
      } else {
        addMessage(`❌ Error deleting document: ${data.error}`, false, 'error');
      }
    } catch (error) {
      addMessage(`❌ Error deleting document: ${error.message}`, false, 'error');
    }
  };
  
  const handleDocumentView = async (documentId) => {
    try {
      // First get document details
      const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
      const response = await fetch(`${backendUrl}/api/documents/${documentId}`);
      const data = await response.json();
      
      if (data.success) {
        setSelectedDocument(data.document);
        
        // Then get document chunks
        const chunksResponse = await fetch(`${backendUrl}/api/documents/${documentId}/chunks`);
        const chunksData = await chunksResponse.json();
        
        if (chunksData.success) {
          setDocumentChunks(chunksData.chunks);
        }
        
        // Switch to document view tab
        setActiveTab('documents');
      } else {
        addMessage(`❌ Error retrieving document: ${data.error}`, false, 'error');
      }
    } catch (error) {
      addMessage(`❌ Error retrieving document: ${error.message}`, false, 'error');
    }
  };

  // Search & RAG Operations
  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
      const response = await fetch(`${backendUrl}/api/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: searchQuery,
          n_results: 10,
          filters: searchFilters
        }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        setSearchResults(data.results);
        setActiveTab('search');
        
        if (data.results.length === 0) {
          addMessage(`ℹ️ No results found for search: "${searchQuery}"`, false, 'system');
        }
      } else {
        setSearchResults([]);
        addMessage(`❌ Search error: ${data.error}`, false, 'error');
      }
    } catch (error) {
      setSearchResults([]);
      addMessage(`❌ Search error: ${error.message}`, false, 'error');
    }
  };
  
  const handleRagQuery = async (e) => {
    e.preventDefault();
    if (!ragQuery.trim()) return;
    
    setRagResponse({ status: 'loading' });
    
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
      const response = await fetch(`${backendUrl}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: ragQuery,
          include_sources: true,
          max_context_length: 3000,
          n_results: 5
        }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        setRagResponse({
          status: 'success',
          answer: data.answer,
          sources: data.sources,
          metadata: data.metadata
        });
        
        // Add to chat as well
        addMessage(ragQuery, true);
        addMessage(data.answer, false);
        
        if (data.sources && data.sources.length > 0) {
          const sourcesText = `📚 Sources: ${data.sources.map(s => s.filename || 'Document').join(', ')}`;
          addMessage(sourcesText, false, 'sources');
        }
      } else {
        setRagResponse({
          status: 'error',
          error: data.error
        });
        
        addMessage(`❌ Query error: ${data.error}`, false, 'error');
      }
    } catch (error) {
      setRagResponse({
        status: 'error',
        error: error.message
      });
      
      addMessage(`❌ Query error: ${error.message}`, false, 'error');
    }
  };
  
  const updateSearchFilter = (filterType, value, isActive) => {
    setSearchFilters(prev => {
      const newFilters = { ...prev };
      
      if (!newFilters[filterType]) {
        newFilters[filterType] = [];
      }
      
      if (isActive) {
        // Add filter if not already present
        if (!newFilters[filterType].includes(value)) {
          newFilters[filterType] = [...newFilters[filterType], value];
        }
      } else {
        // Remove filter if present
        newFilters[filterType] = newFilters[filterType].filter(v => v !== value);
        
        // Clean up empty arrays
        if (newFilters[filterType].length === 0) {
          delete newFilters[filterType];
        }
      }
      
      return newFilters;
    });
  };
  
  const clearSearchFilters = () => {
    setSearchFilters({});
  };

  // Task Management Operations
  const handleTaskRequest = async (taskDescription) => {
    const newTask = {
      id: Date.now(),
      description: taskDescription,
      status: 'processing',
      steps: [],
      created: new Date().toISOString()
    };
    
    setTasks(prev => [...prev, newTask]);

    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
      const response = await fetch(`${backendUrl}/api/decompose`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: taskDescription }),
      });
      const data = await response.json();
      
      if (data.response?.text) {
        // Parse task breakdown from response
        const steps = data.response.text.split('\n').filter(line => 
          line.trim().length > 0 && (line.includes('•') || line.includes('-') || line.includes('1.'))
        ).map((step, index) => ({
          id: index,
          description: step.trim(),
          completed: false,
          status: 'pending',
          suggested_agent_type: data.response.suggested_agent_type || 'function'
        }));

        const updatedTask = {
          ...newTask,
          status: 'ready',
          steps,
          decomposed_at: new Date().toISOString()
        };

        setTasks(prev => prev.map(task => 
          task.id === newTask.id ? updatedTask : task
        ));
        
        setCurrentTask(updatedTask);
        setActiveTab('tasks');
        
        addMessage(`✅ Task decomposed into ${steps.length} steps.`, false, 'system');
      } else {
        setTasks(prev => prev.map(task => 
          task.id === newTask.id 
            ? { ...task, status: 'error', error: 'Failed to decompose task' }
            : task
        ));
        
        addMessage(`❌ Task decomposition failed: ${data.error || 'Unknown error'}`, false, 'error');
      }
    } catch (error) {
      setTasks(prev => prev.map(task => 
        task.id === newTask.id 
          ? { ...task, status: 'error', error: 'Failed to process task' }
          : task
      ));
      
      addMessage(`❌ Task decomposition failed: ${error.message}`, false, 'error');
    }
  };
  
  const executeTaskStep = async (taskId, stepIndex) => {
    // Find the task
    const task = tasks.find(t => t.id === taskId);
    if (!task) return;
    
    // Get the step
    const step = task.steps[stepIndex];
    if (!step) return;
    
    // Update step status to executing
    const updatedTasks = [...tasks];
    const taskIndex = updatedTasks.findIndex(t => t.id === taskId);
    updatedTasks[taskIndex].steps[stepIndex].status = 'executing';
    setTasks(updatedTasks);
    
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
      const response = await fetch(`${backendUrl}/api/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task: {
            id: taskId,
            step_number: stepIndex,
            instruction: step.description,
            suggested_agent_type: step.suggested_agent_type || 'function'
          }
        }),
      });
      
      const data = await response.json();
      
      if (data.status === 'completed') {
        // Update step status to completed
        updatedTasks[taskIndex].steps[stepIndex].status = 'completed';
        updatedTasks[taskIndex].steps[stepIndex].completed = true;
        updatedTasks[taskIndex].steps[stepIndex].result = data.result;
        updatedTasks[taskIndex].steps[stepIndex].executed_at = new Date().toISOString();
        
        // Check if all steps are completed
        const allCompleted = updatedTasks[taskIndex].steps.every(s => s.completed);
        if (allCompleted) {
          updatedTasks[taskIndex].status = 'completed';
          updatedTasks[taskIndex].completed_at = new Date().toISOString();
        }
        
        setTasks(updatedTasks);
        addMessage(`✅ Step ${stepIndex + 1} executed: ${step.description}`, false, 'system');
      } else {
        updatedTasks[taskIndex].steps[stepIndex].status = 'failed';
        updatedTasks[taskIndex].steps[stepIndex].error = data.error || 'Execution failed';
        setTasks(updatedTasks);
        
        addMessage(`❌ Step execution failed: ${data.error || 'Unknown error'}`, false, 'error');
      }
    } catch (error) {
      // Update step status to failed
      updatedTasks[taskIndex].steps[stepIndex].status = 'failed';
      updatedTasks[taskIndex].steps[stepIndex].error = error.message;
      setTasks(updatedTasks);
      
      addMessage(`❌ Step execution failed: ${error.message}`, false, 'error');
    }
  };
  
  const validateTaskStep = async (taskId, stepIndex) => {
    // Find the task
    const task = tasks.find(t => t.id === taskId);
    if (!task) return;
    
    // Get the step
    const step = task.steps[stepIndex];
    if (!step || !step.result) return;
    
    // Update step validation status
    const updatedTasks = [...tasks];
    const taskIndex = updatedTasks.findIndex(t => t.id === taskId);
    updatedTasks[taskIndex].steps[stepIndex].validation_status = 'validating';
    setTasks(updatedTasks);
    
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
      const response = await fetch(`${backendUrl}/api/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task: {
            id: taskId,
            step_number: stepIndex,
            instruction: step.description
          },
          result: step.result
        }),
      });
      
      const data = await response.json();
      
      // Update validation results
      updatedTasks[taskIndex].steps[stepIndex].validation_status = data.status;
      updatedTasks[taskIndex].steps[stepIndex].validation_confidence = data.confidence;
      updatedTasks[taskIndex].steps[stepIndex].validation_feedback = data.feedback;
      updatedTasks[taskIndex].steps[stepIndex].validated_at = new Date().toISOString();
      
      setTasks(updatedTasks);
      
      if (data.status === 'PASS') {
        addMessage(`✅ Step ${stepIndex + 1} validated successfully.`, false, 'system');
      } else {
        addMessage(`⚠️ Step ${stepIndex + 1} validation issue: ${data.feedback}`, false, 'warning');
      }
    } catch (error) {
      updatedTasks[taskIndex].steps[stepIndex].validation_status = 'ERROR';
      updatedTasks[taskIndex].steps[stepIndex].validation_feedback = error.message;
      setTasks(updatedTasks);
      
      addMessage(`❌ Step validation failed: ${error.message}`, false, 'error');
    }
  };
  
  // Assistant Chat Operations
  const handleSend = async () => {
    if (!input.trim()) return;
    addMessage(input, true);

    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
      const endpoint = currentAssistant === 'concierge' 
        ? `${backendUrl}/api/decompose` 
        : `${backendUrl}/api/assistants/${currentAssistant}/query`;
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query: input,
          message: input, // For compatibility with decompose endpoint
          use_rag: true
        }),
      });
      
      const data = await response.json();
      
      let responseText;
      if (currentAssistant === 'concierge') {
        responseText = data.response?.text || 'No response from concierge';
      } else {
        responseText = data.response || 'No response from assistant';
      }
      
      addMessage(responseText, false);
      
      // Show sources if available
      if ((data.response?.sources && data.response.sources.length > 0) || 
          (data.sources && data.sources.length > 0)) {
        const sources = data.response?.sources || data.sources || [];
        const sourcesText = `📚 Sources: ${sources.map(s => s.title || s.filename || 'Document').join(', ')}`;
        addMessage(sourcesText, false, 'sources');
      }
      
      // Handle task creation if detected in message
      if (input.toLowerCase().includes('create a task') || 
          input.toLowerCase().includes('new task') || 
          input.toLowerCase().includes('setup task')) {
        const taskDescription = input.replace(/create a task|new task|setup task/gi, '').trim();
        if (taskDescription) {
          handleTaskRequest(taskDescription);
        }
      }
    } catch (error) {
      addMessage('❌ Error: Unable to get response from server. Please try again.', false, 'error');
    }
    setInput('');
  };

  const handleSbaResourceSelect = (programId) => {
    // Find the selected program
    const program = sbaPrograms.find(p => p.id === programId);
    if (!program) return;
    
    // Set the query to search for information about this program
    setRagQuery(`Tell me about the SBA ${program.name} program and how it can help small businesses`);
    
    // Switch to the RAG tab
    setActiveTab('rag');
    
    // Automatically execute the query
    handleRagQuery({ preventDefault: () => {} });
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatMessage = (content) => {
    // Convert markdown-style formatting to HTML
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br/>')
      .replace(/^(#{1,6})\s+(.*?)$/gm, (match, hashes, text) => {
        const level = hashes.length;
        return `<h${level}>${text}</h${level}>`;
      })
      .replace(/```([a-z]*)\n([\s\S]*?)\n```/g, '<pre><code>$2</code></pre>')
      .replace(/`([^`]+)`/g, '<code>$1</code>');
  };

  if (isLoading) {
    return (
      <div className="app-container loading">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Starting PocketPro:SBA Edition...</p>
        </div>
      </div>
    );
  }
  
  if (backendError) {
    return (
      <div className="app-container error">
        <div className="backend-error">
          <h2>⚠️ Backend Connection Error</h2>
          <p>Unable to connect to the backend API server.</p>
          <div className="error-details">
            <h3>Possible solutions:</h3>
            <ol>
              <li>Make sure the backend server is running with <code>docker-compose up</code> or <code>deploy-docker.bat</code></li>
              <li>Check that the backend is accessible at <code>http://localhost:10000</code></li>
              <li>Verify that the frontend is configured to connect to the correct backend URL</li>
            </ol>
            <div className="error-actions">
              <button 
                className="retry-button"
                onClick={() => {
                  setBackendError(false);
                  setIsLoading(true);
                  initializeApp();
                }}
              >
                Retry Connection
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Header with logo and navigation */}
      <header className="app-header">
        <div className="logo-container">
          <h1>🚀 PocketPro:SBA Edition</h1>
          <button 
            className="sidebar-toggle" 
            onClick={() => setSidebarVisible(!sidebarVisible)}
            title={sidebarVisible ? "Hide sidebar" : "Show sidebar"}
          >
            {sidebarVisible ? '◀' : '▶'}
          </button>
        </div>
        <nav className="main-nav">
          <button 
            className={`nav-button ${activeTab === 'chat' ? 'active' : ''}`} 
            onClick={() => setActiveTab('chat')}
          >
            💬 Chat
          </button>
          <button 
            className={`nav-button ${activeTab === 'documents' ? 'active' : ''}`} 
            onClick={() => setActiveTab('documents')}
          >
            📄 Documents
          </button>
          <button 
            className={`nav-button ${activeTab === 'search' ? 'active' : ''}`} 
            onClick={() => setActiveTab('search')}
          >
            🔍 Search
          </button>
          <button 
            className={`nav-button ${activeTab === 'rag' ? 'active' : ''}`} 
            onClick={() => setActiveTab('rag')}
          >
            🧠 RAG Query
          </button>
          <button 
            className={`nav-button ${activeTab === 'rag-workflow' ? 'active' : ''}`} 
            onClick={() => setActiveTab('rag-workflow')}
          >
            ⚙️ RAG Workflow
          </button>
          <button 
            className={`nav-button ${activeTab === 'tasks' ? 'active' : ''}`} 
            onClick={() => setActiveTab('tasks')}
          >
            ✅ Tasks
          </button>
          <button 
            className={`nav-button ${activeTab === 'resources' ? 'active' : ''}`} 
            onClick={() => setActiveTab('resources')}
          >
            🏢 SBA Resources
          </button>
        </nav>
      </header>

      <div className="main-content">
        {/* Left sidebar with assistants and models */}
        {sidebarVisible && (
          <aside className="sidebar">
            <section className="sidebar-section">
              <h3>Assistants</h3>
              <div className="assistant-list">
                {assistants.map(assistant => (
                  <button 
                    key={assistant.type} 
                    className={`assistant-button ${currentAssistant === assistant.type ? 'active' : ''}`}
                    onClick={() => setCurrentAssistant(assistant.type)}
                    title={assistant.description}
                  >
                    {assistant.name}
                  </button>
                ))}
              </div>
            </section>
            
            <section className="sidebar-section">
              <h3>LLM Models</h3>
              <div className="model-list">
                {availableModels.map(model => (
                  <button 
                    key={model.name} 
                    className={`model-button ${selectedModel === model.name ? 'active' : ''}`}
                    onClick={() => setSelectedModel(model.name)}
                    title={model.description}
                  >
                    {model.display_name}
                  </button>
                ))}
              </div>
            </section>
            
            <section className="sidebar-section">
              <h3>Collection Stats</h3>
              <div className="stats-list">
                <div className="stat-item">
                  <span className="stat-label">Documents:</span>
                  <span className="stat-value">{collectionStats.document_count || 0}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Chunks:</span>
                  <span className="stat-value">{collectionStats.chunk_count || 0}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Database:</span>
                  <span className="stat-value">{collectionStats.db_size || "Unknown"}</span>
                </div>
              </div>
            </section>
            
            <section className="sidebar-section sba-quick-links">
              <h3>SBA Quick Links</h3>
              <div className="quick-links">
                <a href="https://www.sba.gov/funding-programs/loans" target="_blank" rel="noopener noreferrer">Loan Programs</a>
                <a href="https://www.sba.gov/federal-contracting" target="_blank" rel="noopener noreferrer">Government Contracting</a>
                <a href="https://www.sba.gov/local-assistance" target="_blank" rel="noopener noreferrer">Local Assistance</a>
                <a href="https://www.sba.gov/business-guide" target="_blank" rel="noopener noreferrer">Business Guide</a>
              </div>
            </section>
          </aside>
        )}
        
        {/* Main content area - changes based on active tab */}
        <main className="content-area">
          {activeTab === 'chat' && (
            <div className="chat-tab">
              <div className="chat-container" ref={chatBoxRef}>
                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`message ${msg.isUser ? 'message-user' : 'message-assistant'} ${msg.type === 'greeting' ? 'message-greeting' : ''} ${msg.type === 'sources' ? 'message-sources' : ''} ${msg.type === 'error' ? 'message-error' : ''} ${msg.type === 'system' ? 'message-system' : ''} ${msg.type === 'warning' ? 'message-warning' : ''}`}
                  >
                    <div 
                      dangerouslySetInnerHTML={{ 
                        __html: formatMessage(msg.content) 
                      }} 
                    />
                    {msg.timestamp && (
                      <div className="message-timestamp">
                        {new Date(msg.timestamp).toLocaleTimeString()}
                      </div>
                    )}
                  </div>
                ))}
              </div>
              <div className="input-container">
                <textarea
                  className="input-box"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={`Ask ${assistants.find(a => a.type === currentAssistant)?.name || 'the assistant'} about SBA programs, resources, or upload documents...`}
                  disabled={isLoading}
                />
                <button className="send-button" onClick={handleSend} disabled={isLoading || !input.trim()}>
                  Send
                </button>
              </div>
            </div>
          )}
          
          {activeTab === 'documents' && (
            <div className="documents-tab">
              <div className="documents-header">
                <h2>Document Management</h2>
                <div className="document-actions">
                  <label className="upload-button">
                    Upload Document
                    <input type="file" onChange={handleFileUpload} style={{ display: 'none' }} />
                  </label>
                  <label className="upload-button">
                    Batch Upload
                    <input 
                      type="file" 
                      multiple 
                      onChange={(e) => handleBatchUpload(e.target.files)} 
                      style={{ display: 'none' }} 
                    />
                  </label>
                </div>
              </div>
              
              {uploadProgress && (
                <div className={`upload-progress ${uploadProgress.status}`}>
                  <div className="progress-bar" style={{ width: `${uploadProgress.progress}%` }}></div>
                  <div className="progress-info">
                    <span className="filename">{uploadProgress.filename}</span>
                    <span className="status">
                      {uploadProgress.status === 'uploading' && 'Uploading...'}
                      {uploadProgress.status === 'success' && 'Upload successful!'}
                      {uploadProgress.status === 'error' && `Error: ${uploadProgress.error}`}
                    </span>
                    {uploadProgress.completed && (
                      <span className="stats">
                        {uploadProgress.completed}/{uploadProgress.total} files processed
                      </span>
                    )}
                  </div>
                </div>
              )}
              
              <div className="documents-layout">
                <div className="documents-list">
                  <h3>Available Documents</h3>
                  {documents.length === 0 ? (
                    <div className="no-documents">
                      <p>No documents available. Upload a document to get started.</p>
                    </div>
                  ) : (
                    <ul className="document-items">
                      {documents.map(doc => (
                        <li 
                          key={doc.id} 
                          className={`document-item ${selectedDocument && selectedDocument.id === doc.id ? 'selected' : ''}`}
                          onClick={() => handleDocumentView(doc.id)}
                        >
                          <div className="document-icon">📄</div>
                          <div className="document-info">
                            <div className="document-name">{doc.filename || 'Unnamed document'}</div>
                            <div className="document-meta">
                              {doc.metadata && doc.metadata.created && (
                                <span className="document-date">
                                  {new Date(doc.metadata.created).toLocaleDateString()}
                                </span>
                              )}
                              {doc.chunk_count && (
                                <span className="document-chunks">
                                  {doc.chunk_count} chunks
                                </span>
                              )}
                            </div>
                          </div>
                          <button 
                            className="document-delete"
                            onClick={(e) => {
                              e.stopPropagation();
                              if (window.confirm(`Are you sure you want to delete "${doc.filename}"?`)) {
                                handleDocumentDelete(doc.id);
                              }
                            }}
                            title="Delete document"
                          >
                            🗑️
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                
                <div className="document-details">
                  {selectedDocument ? (
                    <>
                      <h3>Document Details: {selectedDocument.filename}</h3>
                      <div className="document-metadata">
                        <div className="metadata-item">
                          <span className="metadata-label">ID:</span>
                          <span className="metadata-value">{selectedDocument.id}</span>
                        </div>
                        {selectedDocument.metadata && Object.entries(selectedDocument.metadata).map(([key, value]) => (
                          <div className="metadata-item" key={key}>
                            <span className="metadata-label">{key}:</span>
                            <span className="metadata-value">
                              {typeof value === 'object' ? JSON.stringify(value) : value}
                            </span>
                          </div>
                        ))}
                      </div>
                      
                      <h4>Document Chunks</h4>
                      {documentChunks.length > 0 ? (
                        <div className="document-chunks-list">
                          {documentChunks.map((chunk, index) => (
                            <div className="document-chunk" key={index}>
                              <div className="chunk-header">
                                <span className="chunk-index">Chunk {index + 1}</span>
                                {chunk.metadata && chunk.metadata.chunk_type && (
                                  <span className="chunk-type">{chunk.metadata.chunk_type}</span>
                                )}
                              </div>
                              <div className="chunk-content">
                                {chunk.content || chunk.text || 'No content available'}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="no-chunks">
                          <p>No chunks available for this document.</p>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="no-document-selected">
                      <p>Select a document to view details.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
          
          {activeTab === 'search' && (
            <div className="search-tab">
              <div className="search-header">
                <h2>Semantic Search</h2>
                <form className="search-form" onSubmit={handleSearch}>
                  <input
                    type="text"
                    className="search-input"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search your documents..."
                  />
                  <button type="submit" className="search-button">Search</button>
                </form>
              </div>
              
              <div className="search-layout">
                <div className="search-filters">
                  <div className="filters-header">
                    <h3>Filters</h3>
                    <button 
                      className="clear-filters-button" 
                      onClick={clearSearchFilters}
                      disabled={Object.keys(searchFilters).length === 0}
                    >
                      Clear All
                    </button>
                  </div>
                  
                  {Object.keys(availableFilters).length > 0 ? (
                    <div className="filter-groups">
                      {Object.entries(availableFilters).map(([filterType, values]) => (
                        <div className="filter-group" key={filterType}>
                          <h4>{availableFilters[`filter_descriptions`]?.[filterType] || filterType}</h4>
                          <div className="filter-options">
                            {values.map(value => (
                              <label className="filter-option" key={value}>
                                <input
                                  type="checkbox"
                                  checked={searchFilters[filterType]?.includes(value) || false}
                                  onChange={(e) => updateSearchFilter(filterType, value, e.target.checked)}
                                />
                                <span className="filter-value">{value}</span>
                              </label>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="no-filters">
                      <p>No filters available. Upload documents first.</p>
                    </div>
                  )}
                </div>
                
                <div className="search-results">
                  <h3>Results {searchResults.length > 0 ? `(${searchResults.length})` : ''}</h3>
                  
                  {searchResults.length > 0 ? (
                    <div className="results-list">
                      {searchResults.map((result, index) => (
                        <div className="search-result" key={index}>
                          <div className="result-header">
                            <span className="result-title">
                              {result.metadata?.filename || 'Untitled chunk'}
                            </span>
                            <span className="result-score">
                              {result.score ? `Score: ${Number(result.score).toFixed(2)}` : ''}
                            </span>
                          </div>
                          <div className="result-content">
                            {result.content || result.text || 'No content available'}
                          </div>
                          <div className="result-metadata">
                            {result.metadata && Object.entries(result.metadata)
                              .filter(([key]) => !['filename', 'id'].includes(key))
                              .map(([key, value]) => (
                                <span className="metadata-tag" key={key}>
                                  {key}: {typeof value === 'object' ? JSON.stringify(value) : value}
                                </span>
                              ))
                            }
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : searchQuery ? (
                    <div className="no-results">
                      <p>No results found for "{searchQuery}".</p>
                    </div>
                  ) : (
                    <div className="no-query">
                      <p>Enter a search query to find information in your documents.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
          
          {activeTab === 'rag' && (
            <div className="rag-tab">
              <div className="rag-header">
                <h2>RAG Query</h2>
                <p className="rag-description">
                  Ask questions about your documents using Retrieval-Augmented Generation (RAG).
                </p>
                <form className="rag-form" onSubmit={handleRagQuery}>
                  <input
                    type="text"
                    className="rag-input"
                    value={ragQuery}
                    onChange={(e) => setRagQuery(e.target.value)}
                    placeholder="Ask a question about your documents..."
                  />
                  <button type="submit" className="rag-button">Generate Answer</button>
                </form>
              </div>
              
              <div className="rag-content">
                {ragResponse ? (
                  <div className={`rag-response ${ragResponse.status}`}>
                    {ragResponse.status === 'loading' && (
                      <div className="loading-indicator">
                        <div className="spinner"></div>
                        <p>Generating response...</p>
                      </div>
                    )}
                    
                    {ragResponse.status === 'success' && (
                      <>
                        <div className="rag-answer">
                          <h3>Answer</h3>
                          <div dangerouslySetInnerHTML={{ __html: formatMessage(ragResponse.answer) }} />
                        </div>
                        
                        {ragResponse.sources && ragResponse.sources.length > 0 && (
                          <div className="rag-sources">
                            <h3>Sources</h3>
                            <ul className="source-list">
                              {ragResponse.sources.map((source, index) => (
                                <li className="source-item" key={index}>
                                  <div className="source-name">
                                    📄 {source.filename || 'Document'}
                                  </div>
                                  {source.relevance_score && (
                                    <div className="source-score">
                                      Relevance: {Number(source.relevance_score).toFixed(2)}
                                    </div>
                                  )}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        {ragResponse.metadata && (
                          <div className="rag-metadata">
                            <h3>Metadata</h3>
                            <div className="metadata-items">
                              {Object.entries(ragResponse.metadata).map(([key, value]) => (
                                <div className="metadata-item" key={key}>
                                  <span className="metadata-key">{key}:</span>
                                  <span className="metadata-value">
                                    {typeof value === 'object' ? JSON.stringify(value) : value}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </>
                    )}
                    
                    {ragResponse.status === 'error' && (
                      <div className="rag-error">
                        <h3>Error</h3>
                        <p>{ragResponse.error}</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="rag-placeholder">
                    <p>Enter a question above to get an answer based on your documents.</p>
                    <div className="rag-example">
                      <h3>Example Questions</h3>
                      <ul>
                        <li onClick={() => {
                          setRagQuery("What SBA loan programs are available for small businesses?");
                          handleRagQuery({ preventDefault: () => {} });
                        }}>
                          What SBA loan programs are available for small businesses?
                        </li>
                        <li onClick={() => {
                          setRagQuery("How do I qualify for government contracting as a small business?");
                          handleRagQuery({ preventDefault: () => {} });
                        }}>
                          How do I qualify for government contracting as a small business?
                        </li>
                        <li onClick={() => {
                          setRagQuery("What resources does the SBA offer for business planning?");
                          handleRagQuery({ preventDefault: () => {} });
                        }}>
                          What resources does the SBA offer for business planning?
                        </li>
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {activeTab === 'rag-workflow' && (
            <div className="rag-workflow-tab">
              <RAGWorkflowInterface 
                onSearch={handleSearch}
                onUpload={handleFileUpload}
                onQuery={handleRagQuery}
                documents={documents}
                searchResults={searchResults}
                ragResponse={ragResponse}
              />
            </div>
          )}
          
          {activeTab === 'tasks' && (
            <div className="tasks-tab">
              <div className="tasks-header">
                <h2>Task Management</h2>
                <div className="task-create">
                  <input
                    type="text"
                    className="task-input"
                    placeholder="Describe a new task..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey && input.trim()) {
                        e.preventDefault();
                        handleTaskRequest(input);
                        setInput('');
                      }
                    }}
                  />
                  <button 
                    className="task-create-button"
                    onClick={() => {
                      if (input.trim()) {
                        handleTaskRequest(input);
                        setInput('');
                      }
                    }}
                  >
                    Create Task
                  </button>
                </div>
              </div>
              
              <div className="tasks-content">
                <div className="tasks-list">
                  <h3>Your Tasks</h3>
                  
                  {tasks.length > 0 ? (
                    <ul className="task-items">
                      {tasks.map(task => (
                        <li 
                          key={task.id}
                          className={`task-item ${task.status} ${currentTask && currentTask.id === task.id ? 'selected' : ''}`}
                          onClick={() => setCurrentTask(task)}
                        >
                          <div className="task-icon">
                            {task.status === 'completed' && '✅'}
                            {task.status === 'processing' && '⏳'}
                            {task.status === 'ready' && '📋'}
                            {task.status === 'error' && '❌'}
                          </div>
                          <div className="task-info">
                            <div className="task-name">{task.description}</div>
                            <div className="task-meta">
                              <span className="task-status">{task.status}</span>
                              <span className="task-steps">
                                {task.steps ? `${task.steps.filter(s => s.completed).length}/${task.steps.length} steps` : ''}
                              </span>
                              {task.created && (
                                <span className="task-date">
                                  {new Date(task.created).toLocaleDateString()}
                                </span>
                              )}
                            </div>
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <div className="no-tasks">
                      <p>No tasks available. Create a new task to get started.</p>
                    </div>
                  )}
                </div>
                
                <div className="task-details">
                  {currentTask ? (
                    <>
                      <h3>Task: {currentTask.description}</h3>
                      
                      <div className="task-status-info">
                        <div className="status-badge">{currentTask.status}</div>
                        {currentTask.created && (
                          <div className="task-created">
                            Created: {new Date(currentTask.created).toLocaleString()}
                          </div>
                        )}
                        {currentTask.completed_at && (
                          <div className="task-completed">
                            Completed: {new Date(currentTask.completed_at).toLocaleString()}
                          </div>
                        )}
                      </div>
                      
                      {currentTask.steps && currentTask.steps.length > 0 && (
                        <div className="task-steps-list">
                          <h4>Steps</h4>
                          {currentTask.steps.map((step, index) => (
                            <div className={`task-step ${step.status || ''}`} key={index}>
                              <div className="step-header">
                                <div className="step-number">Step {index + 1}</div>
                                <div className={`step-status ${step.status || ''}`}>
                                  {step.status === 'completed' && '✅'}
                                  {step.status === 'executing' && '⏳'}
                                  {step.status === 'failed' && '❌'}
                                  {(!step.status || step.status === 'pending') && '⬜'}
                                </div>
                              </div>
                              
                              <div className="step-description">
                                {step.description}
                              </div>
                              
                              {step.completed && step.result && (
                                <div className="step-result">
                                  <h5>Result</h5>
                                  <div className="result-content">
                                    {step.result}
                                  </div>
                                </div>
                              )}
                              
                              {step.validation_status && (
                                <div className={`step-validation ${step.validation_status}`}>
                                  <span className="validation-status">
                                    {step.validation_status === 'PASS' ? '✅ Passed' : '⚠️ Issue'}
                                  </span>
                                  {step.validation_feedback && (
                                    <div className="validation-feedback">
                                      {step.validation_feedback}
                                    </div>
                                  )}
                                </div>
                              )}
                              
                              <div className="step-actions">
                                {(!step.status || step.status === 'pending' || step.status === 'failed') && (
                                  <button 
                                    className="execute-button"
                                    onClick={() => executeTaskStep(currentTask.id, index)}
                                  >
                                    Execute Step
                                  </button>
                                )}
                                
                                {step.completed && !step.validation_status && (
                                  <button 
                                    className="validate-button"
                                    onClick={() => validateTaskStep(currentTask.id, index)}
                                  >
                                    Validate Result
                                  </button>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="no-task-selected">
                      <p>Select a task to view details and execute steps.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
          
          {activeTab === 'resources' && (
            <div className="resources-tab">
              <div className="resources-header">
                <h2>SBA Programs & Resources</h2>
                <p className="resources-intro">
                  Explore resources available to small businesses through the Small Business Administration (SBA).
                </p>
              </div>
              
              <SBANavigation 
                onProgramSelect={handleSbaResourceSelect}
                onResourceSelect={(resource) => {
                  setRagQuery(`Tell me about ${resource.title} for ${resource.stage || 'small businesses'}`);
                  setActiveTab('rag');
                  handleRagQuery({ preventDefault: () => {} });
                }}
              />
              
              <div className="additional-resources">
                <h3>Additional SBA Resources</h3>
                <div className="resource-links">
                  <a href="https://www.sba.gov/local-assistance/find/" target="_blank" rel="noopener noreferrer" className="resource-link">
                    <div className="resource-icon">📍</div>
                    <div className="resource-info">
                      <h4>Find Local Assistance</h4>
                      <p>Connect with a nearby SBA office or resource partner</p>
                    </div>
                  </a>
                  
                  <a href="https://www.sba.gov/business-guide/plan-your-business/write-your-business-plan" target="_blank" rel="noopener noreferrer" className="resource-link">
                    <div className="resource-icon">📝</div>
                    <div className="resource-info">
                      <h4>Business Plan Resources</h4>
                      <p>Templates and guidance for creating a business plan</p>
                    </div>
                  </a>
                  
                  <a href="https://www.sba.gov/events" target="_blank" rel="noopener noreferrer" className="resource-link">
                    <div className="resource-icon">📅</div>
                    <div className="resource-info">
                      <h4>Events & Training</h4>
                      <p>Workshops, webinars, and training events</p>
                    </div>
                  </a>
                  
                  <a href="https://www.sba.gov/funding-programs/disaster-assistance" target="_blank" rel="noopener noreferrer" className="resource-link">
                    <div className="resource-icon">🚨</div>
                    <div className="resource-info">
                      <h4>Disaster Assistance</h4>
                      <p>Help for businesses affected by declared disasters</p>
                    </div>
                  </a>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
