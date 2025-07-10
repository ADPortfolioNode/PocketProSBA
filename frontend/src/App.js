import React, { useState, useEffect } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";
import { Container, Row, Col, Card, Button } from "react-bootstrap";
import SBANavigation from "./components/SBANavigation";
import RAGWorkflowInterface from "./components/RAGWorkflowInterface";
import SBAContentExplorer from "./components/SBAContentExplorer";
import SBAContent from "./components/SBAContent";
import ConnectionStatusIndicator from "./components/ConnectionStatusIndicator";
import ConnectionErrorHandler from "./components/ConnectionErrorHandler";
import ConciergeGreeting from "./components/ConciergeGreeting";
import LoadingIndicator from "./components/LoadingIndicator";
import ErrorBoundary from "./components/ErrorBoundary";
import StatusBar from "./components/StatusBar";
import UploadsManager from "./components/uploads/UploadsManager";

const BACKEND_URL = process.env.BACKEND_URL || "http://backend:5000";

function App() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("chat");
  const [serverConnected, setServerConnected] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const [usingFallbackConnection, setUsingFallbackConnection] = useState(false);
  const [systemInfo, setSystemInfo] = useState(null);
  const [userName, setUserName] = useState("");
  const [greeted, setGreeted] = useState(false);
  const [selectedProgram, setSelectedProgram] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [ragResponse, setRagResponse] = useState(null);
  const [resources, setResources] = useState([]);
  const [expandedResource, setExpandedResource] = useState(null);
  
  // Check backend connection on load
  useEffect(() => {
    checkServerConnection();
    fetchDocuments(); // Fetch documents on load
  }, []);
  
  // Fetch resources from API on load
  useEffect(() => {
    fetch(`${BACKEND_URL}/api/resources`)
      .then(res => res.json())
      .then(data => {
        if (data && Array.isArray(data.resources)) {
          setResources(data.resources);
        }
      })
      .catch(err => {
        console.error("Failed to fetch resources:", err);
      });
  }, []);
  
  const handleConnectionChange = (status, data, error) => {
    setServerConnected(status);
    if (data) {
      setSystemInfo(data);
    }
    
    if (!status) {
      setConnectionError(error || new Error("Connection failed"));
    } else {
      setConnectionError(null);
    }
    
    // If connection successful, fetch documents
    if (status) {
      fetchDocuments();
    }
  };
  
  // Try a fallback connection method (using HEAD request)
  const tryFallbackConnection = async () => {
    try {
      const endpoints = ['/api/health', '/healthcheck', '/health'];
      
      for (const endpoint of endpoints) {
        try {
          const response = await fetch(endpoint, { method: 'HEAD' });
          
          if (response.ok) {
            console.log(`Fallback connection successful using ${endpoint}`);
            setUsingFallbackConnection(true);
            setServerConnected(true);
            setConnectionError(null);
            return true;
          }
        } catch (error) {
          console.warn(`Fallback attempt to ${endpoint} failed:`, error);
        }
      }
      
      return false;
    } catch (error) {
      console.error("All fallback connection attempts failed:", error);
      return false;
    }
  };
  
  const checkServerConnection = async () => {
    try {
      // Use the backend service name and port
      const response = await fetch(`${BACKEND_URL}/api/health`);
      if (response.ok) {
        try {
          const data = await response.json();
          console.log("Backend connected:", data);
          setSystemInfo(data);
          setServerConnected(true);
          setConnectionError(null);
        } catch (jsonError) {
          console.warn("Backend returned non-JSON response:", jsonError);
          setServerConnected(true);
          setSystemInfo({ server_type: "Unknown (non-JSON response)" });
          setConnectionError(null);
        }
      } else {
        console.error("Backend connection failed with status:", response.status);
        setServerConnected(false);
        setConnectionError(new Error(`HTTP Error: ${response.status}`));
        tryFallbackConnection();
      }
    } catch (error) {
      console.error("Backend connection error:", error);
      setServerConnected(false);
      setConnectionError(error);
      tryFallbackConnection();
    }
  };
  
  // Fetch documents from the backend
  const fetchDocuments = async () => {
    if (!serverConnected) {
      console.log("Server not connected, skipping document fetch");
      return;
    }
    try {
      const response = await fetch(`${BACKEND_URL}/api/documents/list`);
      if (!response.ok) {
        throw new Error(`Failed to fetch documents: ${response.status} ${response.statusText}`);
      }
      const data = await response.json();
      if (data.success && data.documents) {
        setDocuments(data.documents);
        console.log(`Fetched ${data.documents.length} documents`);
      }
    } catch (error) {
      console.error("Error fetching documents:", error);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!message.trim()) return;
    const currentMessage = message;
    setMessages(prevMessages => [...prevMessages, { id: Date.now(), role: "user", content: currentMessage }]);
    setLoading(true);
    setMessage("");
    if (serverConnected) {
      fetch(`${BACKEND_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          message: currentMessage,
          userName: userName || "Guest",
          query: currentMessage
        }),
      })
        .then(response => response.json())
        .then(data => {
          setMessages(prevMessages => [
            ...prevMessages,
            { id: Date.now() + 1, role: "assistant", content: data.response }
          ]);
          setLoading(false);
        })
        .catch(error => {
          console.error("Error calling API:", error);
          simulateResponse(currentMessage);
        });
    } else {
      simulateResponse(currentMessage);
    }
  };
  
  const simulateResponse = (query) => {
    setTimeout(() => {
      setMessages(prevMessages => [
        ...prevMessages,
        { id: Date.now() + 1, role: "assistant", content: "Thank you for your message. I am the SBA Assistant and can help you with information about SBA programs and resources." }
      ]);
      setLoading(false);
    }, 1000);
  };
  
  // Handle document upload for RAG
  const handleDocumentUpload = async (file) => {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    try {
      const response = await fetch(`${BACKEND_URL}/api/documents/upload`, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        throw new Error(`Upload failed with status ${response.status}`);
      }
      const result = await response.json();
      await fetchDocuments();
      return result;
    } catch (error) {
      console.error("Error uploading document:", error);
      throw error;
    }
  };
  
  // Handle search for RAG
  const handleSearch = async (query) => {
    if (!query.trim()) return;
    try {
      const response = await fetch(`${BACKEND_URL}/api/documents/search?query=${encodeURIComponent(query)}`);
      if (!response.ok) {
        throw new Error(`Search failed with status ${response.status}`);
      }
      const results = await response.json();
      setSearchResults(results.matches || []);
      return results;
    } catch (error) {
      console.error("Error searching documents:", error);
    }
  };
  
  // Handle RAG query
  const handleRagQuery = async (query) => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const response = await fetch("/api/rag/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query }),
      });
      
      if (!response.ok) {
        throw new Error(`RAG query failed with status ${response.status}`);
      }
      
      const result = await response.json();
      setRagResponse(result);
      
      // Also add to chat
      setMessages(prev => [
        ...prev,
        { id: Date.now(), role: "user", content: query },
        { id: Date.now() + 1, role: "assistant", content: result.response }
      ]);
      
      setLoading(false);
      return result;
    } catch (error) {
      console.error("Error with RAG query:", error);
      setLoading(false);
      
      // Mock response
      const mockResponse = {
        response: "Based on the documents I've analyzed, the SBA offers various loan programs to help small businesses. The most common is the 7(a) loan program which provides up to $5 million for business purposes.",
        sources: [
          { title: "SBA Loan Programs Guide", page: 12 }
        ]
      };
      
      setRagResponse(mockResponse);
      
      // Add to chat
      setMessages(prev => [
        ...prev,
        { id: Date.now(), role: "user", content: query },
        { id: Date.now() + 1, role: "assistant", content: mockResponse.response }
      ]);
      
      return mockResponse;
    }
  };
  
  const handleTabChange = (tab) => {
    setActiveTab(tab);
  };
  
  const handleProgramSelect = (programId) => {
    setSelectedProgram(programId);
    console.log("Selected program:", programId);
  };
  
  const handleNameSubmit = (name) => {
    setUserName(name);
    setGreeted(true);
    
    // Add initial greeting message from assistant
    const greeting = `Hello ${name}! I'm your SBA Assistant. How can I help you today?`;
    setMessages([
      { 
        id: Date.now(), 
        role: "assistant", 
        content: greeting 
      }
    ]);
    
    // Send greeting to backend to store user session info
    if (serverConnected) {
      fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          message: "SYSTEM: User session started", 
          userName: name 
        }),
      }).catch(error => {
        console.error("Error sending user info to API:", error);
      });
    }
  };
  
  // Handler to open resource details in the browse tab
  const handleResourceMore = (resource) => {
    setActiveTab("browse");
    setSelectedProgram(resource.id || resource.title || "");
  };

  // Example RAG task status for progress bar demo
  const ragTaskStatus = loading ? { progress: 60 } : { progress: 100 };
  
  return (
    <div className="App bg-light min-vh-100">
      <SBANavigation activeTab={activeTab} onTabChange={setActiveTab} serverConnected={serverConnected} />
      <Container className="mt-3">
        <StatusBar serverConnected={serverConnected} userName={userName} ragTaskStatus={ragTaskStatus} />
        {/* Resource Badges Section */}
        <div className="mb-4 d-flex flex-wrap gap-2">
          {resources.length > 0 ? resources.map((resource, idx) => (
            <div key={resource.id || resource.title || idx} style={{ minWidth: 200, marginBottom: 8 }}>
              <span
                className="badge bg-info text-dark resource-badge"
                style={{ cursor: "pointer", fontSize: "1rem", padding: "0.75em 1.25em", display: "inline-block" }}
                onClick={() => setExpandedResource(expandedResource === (resource.id || resource.title) ? null : (resource.id || resource.title))}
              >
                {resource.title}
              </span>
              {expandedResource === (resource.id || resource.title) && (
                <div className="resource-summary bg-white border rounded shadow-sm p-3 mt-2">
                  <div style={{ fontSize: "0.98rem" }}>
                    {resource.description || resource.summary || "No summary available."}
                  </div>
                  <Button
                    variant="link"
                    size="sm"
                    className="p-0 mt-2"
                    onClick={() => handleResourceMore(resource)}
                  >
                    More &gt;&gt;&gt;
                  </Button>
                </div>
              )}
            </div>
          )) : (
            <span className="text-muted">No resources available.</span>
          )}
        </div>
        {/* Main Content Tabs */}
        {activeTab === "chat" && (
          <ErrorBoundary>
            <Row>
              <Col md={8} className="mx-auto">
                <Card className="shadow-sm">
                  <Card.Body>
                    <ConciergeGreeting onNameSubmit={setUserName} />
                  </Card.Body>
                </Card>
              </Col>
            </Row>
          </ErrorBoundary>
        )}
        {activeTab === "browse" && (
          <ErrorBoundary>
            <Row>
              <Col>
                <SBAContentExplorer selectedResource={selectedProgram} />
              </Col>
            </Row>
          </ErrorBoundary>
        )}
        {activeTab === "rag" && (
          <ErrorBoundary>
            <Row>
              <Col>
                <RAGWorkflowInterface
                  documents={documents}
                  onUpload={handleDocumentUpload}
                  onSearch={handleSearch}
                  searchResults={searchResults}
                  onRagQuery={handleRagQuery}
                  ragResponse={ragResponse}
                  serverConnected={serverConnected}
                />
              </Col>
            </Row>
          </ErrorBoundary>
        )}
        {activeTab === "documents" && (
          <ErrorBoundary>
            <Row>
              <Col md={10} className="mx-auto">
                <Card className="shadow-sm document-center-hero">
                  <Card.Header className="bg-primary text-white">
                    <h3 className="mb-0">Document Center</h3>
                    <p className="mb-0">All your uploaded documents in one place. Upload, view, and manage your files for RAG tasks.</p>
                  </Card.Header>
                  <Card.Body>
                    <Row>
                      <Col md={6}>
                        <UploadsManager files={documents} onUpload={fetchDocuments} onRefresh={fetchDocuments} />
                      </Col>
                      <Col md={6}>
                        <div className="document-list-hero">
                          <h5>Uploaded Documents</h5>
                          {documents.length > 0 ? (
                            <ul className="list-group">
                              {documents.map((doc, index) => (
                                <li key={index} className="list-group-item d-flex flex-column align-items-start">
                                  <span className="fw-bold">{doc.filename}</span>
                                  <span className="text-muted small">Type: {doc.type || 'Unknown'} | Size: {Math.round(doc.size / 1024)} KB | Modified: {doc.modified}</span>
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <div className="no-documents-message">
                              <p>No documents found. Upload documents to get started.</p>
                            </div>
                          )}
                        </div>
                      </Col>
                    </Row>
                  </Card.Body>
                </Card>
              </Col>
            </Row>
          </ErrorBoundary>
        )}
      </Container>
    </div>
  );
}

export default App;
