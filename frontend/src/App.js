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
import { loadEndpoints, getEndpoints, apiFetch } from "./apiClient";

// Use only the React build-time env variable for backend URL
// Use correct backend URL based on environment
// Production-ready backend URL logic
let BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
if (!BACKEND_URL || BACKEND_URL === "") {
  // Default to localhost for development
  BACKEND_URL = process.env.NODE_ENV === "development"
    ? "http://localhost:10000/api"
    : "https://pocketprosba-backend.onrender.com/api";
}
// If running in production, use the deployed backend URL from env or fallback
if (process.env.NODE_ENV === "production") {
  BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "https://pocketprosba-backend.onrender.com";
}

// Helper to prefix endpoint paths with BACKEND_URL if not already absolute
const apiUrl = (path) => {
  // If path is absolute (starts with http), return as is
  if (path.startsWith('http')) return path;
  // If path is exactly /api/api or starts with /api/api/, return as is
  if (path === '/api/api' || path.startsWith('/api/api/')) return path;
  // If path starts with /api and BACKEND_URL is /api, avoid double prefix
  if (BACKEND_URL === '/api' && path.startsWith('/api')) return path;
  // In production, ensure /api is used for proxying if needed
  if (process.env.NODE_ENV === "production" && path.startsWith('/api')) {
    return `/api${path.substring(4)}`;
  }
  // Otherwise, prefix with BACKEND_URL
  return `${BACKEND_URL}${path.startsWith('/') ? '' : '/'}${path}`;
};

// Helper to check response status
const isSuccessResponse = (response) => response && response.status === 200;

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
  const [showGreeting, setShowGreeting] = useState(true);
  const [selectedProgram, setSelectedProgram] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [ragResponse, setRagResponse] = useState(null);
  const [resources, setResources] = useState([]);
  const [expandedResource, setExpandedResource] = useState(null);
  const [endpoints, setEndpoints] = useState(null);
  
  // Enhanced loading sequence with progress
  useEffect(() => {
    const startup = async () => {
      setLoading(true);
      setProgress(10);
      try {
        // Wait for backend health to be 200
        let healthRes = await fetch(apiUrl("/api/health"));
        if (healthRes.status !== 200) throw new Error("Backend not healthy");
        let sysInfo = await healthRes.json();
        setSystemInfo(sysInfo);
        setServerConnected(true);
        setProgress(50);
        // Wait for registry to be 200
        let regRes = await fetch(apiUrl("/api/registry"));
        if (regRes.status !== 200) throw new Error("API registry not available");
        let eps = await regRes.json();
        setEndpoints(eps);
        setProgress(100);
        setLoading(false);
      } catch (err) {
        setLoading(false);
        setProgress(0);
        setConnectionError(err);
        console.error("Failed to load health or endpoints:", err);
      }
    };
    startup();
  }, []);
  // Progress state for loading sequence
  const [progress, setProgress] = useState(0);

  // Fetch documents and resources only after health check and endpoint registry are loaded
  useEffect(() => {
    if (serverConnected && endpoints) {
      // Expose endpoints globally for UploadsManager
      window.endpoints = endpoints;
      fetchDocuments();
      fetchResources();
    }
  }, [serverConnected, endpoints]);
  
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
      const endpoints = [
        apiUrl("/api/health"),
        apiUrl("/healthcheck"),
        apiUrl("/health")
      ];
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

  const checkServerConnection = async (healthUrl) => {
    let healthChecked = false;
    let data = null;
    try {
      // Use /health endpoint
      let response = await fetch(apiUrl(healthUrl));
      if (isSuccessResponse(response)) {
        data = await response.json();
        healthChecked = true;
      }
      if (healthChecked) {
        setSystemInfo(data);
        setServerConnected(true);
        setConnectionError(null);
      } else {
        throw new Error("Health check failed");
      }
    } catch (error) {
      setServerConnected(false);
      setConnectionError(error);
    }
  };
  
  // Fetch documents from the backend
  const fetchDocuments = async () => {
    if (!serverConnected || !endpoints || !endpoints.documents) {
      console.log("Server not connected or endpoints not loaded, skipping document fetch");
      return;
    }
    try {
      // Use endpoint from registry
      const response = await apiFetch("documents", {
        method: "GET"
      });
      if (response && response.success && response.documents) {
        setDocuments(response.documents);
        console.log(`Fetched ${response.documents.length} documents`);
      }
    } catch (error) {
      console.error("Error fetching documents:", error);
    }
  };

  // Fetch resources from the backend
  const fetchResources = async () => {
    if (!serverConnected || !endpoints || !endpoints.resources) {
      console.log("Server not connected or endpoints not loaded, skipping resources fetch");
      return;
    }
    try {
      const response = await apiFetch("resources", {
        method: "GET"
      });
      if (response && Array.isArray(response.resources)) {
        setResources(response.resources);
      }
    } catch (err) {
      console.error("Failed to fetch resources:", err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim() || !endpoints || !endpoints.chat) return;
    const currentMessage = message;
    setMessages((prevMessages) => [
      ...prevMessages,
      { id: Date.now(), role: "user", content: currentMessage },
    ]);
    setLoading(true);
    setMessage("");
    if (serverConnected) {
      try {
        const data = await apiFetch("chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: currentMessage,
            userName: userName || "Guest",
            query: currentMessage,
          }),
        });
        setMessages((prevMessages) => [
          ...prevMessages,
          { id: Date.now() + 1, role: "assistant", content: data.response },
        ]);
        setLoading(false);
      } catch (error) {
        console.error("Error calling API:", error);
        setMessages((prevMessages) => [
          ...prevMessages,
          { id: Date.now() + 1, role: "assistant", content: "Sorry, there was an error processing your request. Please try again later." },
        ]);
        setLoading(false);
      }
    } else {
      setMessages((prevMessages) => [
        ...prevMessages,
        { id: Date.now() + 1, role: "assistant", content: "Server is not connected. Please check your connection and try again." },
      ]);
      setLoading(false);
    }
  };
  
  // Removed simulateResponse placeholder. All chat responses now require backend inference.
  
  // Handle document upload for RAG
  const handleDocumentUpload = async (file) => {
    if (!file || !endpoints || !endpoints.upload) return;
    const formData = new FormData();
    formData.append("file", file);
    try {
      const result = await apiFetch("upload", {
        method: "POST",
        body: formData,
      });
      await fetchDocuments();
      return result;
    } catch (error) {
      console.error("Error uploading document:", error);
      throw error;
    }
  };
  
  // Handle search for RAG
  const handleSearch = async (query) => {
    if (!query.trim() || !endpoints || !endpoints.search) return;
    try {
      const results = await apiFetch("search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query })
      });
      setSearchResults(results.matches || []);
      return results;
    } catch (error) {
      console.error("Error searching documents:", error);
    }
  };
  
  // Handle RAG query
  const handleRagQuery = async (query) => {
    if (!query.trim() || !endpoints || !endpoints.search) return;
    setLoading(true);
    try {
      const result = await apiFetch("search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      // If backend returns 'results', use them for context display
      if (result && result.results && Array.isArray(result.results)) {
        setRagResponse({ content: result.results.map(r => r.content).join('\n\n'), sources: result.results });
        setMessages((prev) => [
          ...prev,
          { id: Date.now(), role: "user", content: query },
          { id: Date.now() + 1, role: "assistant", content: result.results.map(r => r.content).join('\n\n') },
        ]);
      } else if (result && result.response) {
        setRagResponse({ content: result.response });
        setMessages((prev) => [
          ...prev,
          { id: Date.now(), role: "user", content: query },
          { id: Date.now() + 1, role: "assistant", content: result.response },
        ]);
      } else {
        setRagResponse({ content: "No relevant context found." });
        setMessages((prev) => [
          ...prev,
          { id: Date.now(), role: "user", content: query },
          { id: Date.now() + 1, role: "assistant", content: "No relevant context found." },
        ]);
      }
      setLoading(false);
      return result;
    } catch (error) {
      console.error("Error with RAG query:", error);
      setLoading(false);
      setMessages((prev) => [
        ...prev,
        { id: Date.now(), role: "user", content: query },
        { id: Date.now() + 1, role: "assistant", content: "Sorry, there was an error processing your RAG query. Please try again later." },
      ]);
      setRagResponse({ content: "Sorry, there was an error processing your RAG query. Please try again later." });
      return null;
    }
  };
  
  // Send greeting to backend to store user session info
  // Send greeting to backend to store user session info
  const handleNameSubmit = (name) => {
    setUserName(name);
    setGreeted(true);
    setShowGreeting(false);
    setActiveTab("chat");
    const greeting = `Hello ${name}! I'm your SBA Assistant. How can I help you today?`;
    setMessages([
      {
        id: Date.now(),
        role: "assistant",
        content: greeting,
      },
    ]);
    if (serverConnected && endpoints) {
      apiFetch("chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: "SYSTEM: User session started", userName: name }),
      }).catch((error) => {
        console.error("Error sending user info to API:", error);
      });
    }
  };
  
  // Example RAG task status for progress bar demo
  const ragTaskStatus = loading ? { progress: 60 } : { progress: 100 };

  return (
    <div className="App bg-light min-vh-100 d-flex flex-column" style={{ minHeight: "100vh", width: "100vw" }}>
      <SBANavigation activeTab={activeTab} onTabChange={setActiveTab} serverConnected={serverConnected} apiUrl={apiUrl} />
      <Container fluid className="flex-grow-1 px-0" style={{ maxWidth: "100vw", minHeight: "100vh", overflow: "visible" }}>
        {/* Progress bar for loading sequence */}
        {loading && (
          <div className="mb-3">
            <div className="progress" style={{ height: "24px" }}>
              <div
                className="progress-bar progress-bar-striped progress-bar-animated bg-info"
                role="progressbar"
                style={{ width: `${progress}%`, fontWeight: "bold", fontSize: "1.1em" }}
                aria-valuenow={progress}
                aria-valuemin={0}
                aria-valuemax={100}
              >
                {progress < 100 ? `Loading... (${progress}%)` : "Ready"}
              </div>
            </div>
          </div>
        )}
        <StatusBar serverConnected={serverConnected} userName={userName} ragTaskStatus={ragTaskStatus} systemInfo={systemInfo} />
        <ConnectionStatusIndicator
          connected={serverConnected}
          systemInfo={systemInfo}
          apiUrl={apiUrl}
          onConnectionChange={handleConnectionChange}
        />
        {/* Adaptive Mosaic Grid Layout */}
        <div className="mosaic-grid d-flex flex-row flex-wrap w-100 h-100" style={{ minHeight: "calc(100vh - 56px)", gap: "0px", overflow: "visible" }}>
          {/* Sidebar: Resources & Assistants */}
          <div
            className="sidebar-col bg-white border-end shadow-sm animate__animated animate__fadeIn d-flex flex-column"
            style={{
              minWidth: 0,
              width: "100%",
              maxWidth: "340px",
              flex: "1 1 320px",
              zIndex: 2,
              height: "100%",
              position: "relative",
              overflow: "visible"
            }}
          >
            <div className="sticky-top" style={{ top: 80 }}>
              <h5 className="mb-3">Resources</h5>
              {resources.length > 0 ? (
                <ul className="list-group mb-4">
                  {resources.map((resource, idx) => (
                    <li key={resource.id || resource.title || idx} className="list-group-item p-2">
                      <div className="d-flex align-items-center justify-content-between">
                        <span
                          style={{ cursor: "pointer", fontWeight: "bold" }}
                          onClick={() => setExpandedResource(expandedResource === (resource.id || resource.title) ? null : (resource.id || resource.title))}
                        >
                          {resource.title}
                        </span>
                        <span className="badge bg-info text-dark ms-2">Info</span>
                      </div>
                      {expandedResource === (resource.id || resource.title) && (
                        <div className="mt-2 p-2 bg-light border rounded animate__animated animate__fadeIn">
                          <div style={{ fontSize: "0.98rem" }}>
                            {resource.description || resource.summary || "No summary available."}
                          </div>
                          <Button
                            variant="link"
                            size="sm"
                            className="p-0 mt-2"
                            onClick={() => window.open(`/resources/${(resource.slug || resource.title || "").replace(/\s+/g, '-').toLowerCase()}`, "_blank")}
                          >
                            More &gt;&gt;&gt;
                          </Button>
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              ) : (
                <span className="text-muted">No resources available.</span>
              )}

              {/* Active Assistants Section */}
              <h5 className="mb-3">Active Assistants</h5>
              <ul className="list-group">
                <li className="list-group-item p-2">
                  <div className="d-flex align-items-center justify-content-between">
                    <span style={{ fontWeight: "bold" }}>Concierge Assistant</span>
                    <span className="badge bg-success">Online</span>
                  </div>
                  {/* Expand for task/progress */}
                  <Button
                    variant="link"
                    size="sm"
                    className="p-0 mt-2"
                    onClick={() => setExpandedResource(expandedResource === "concierge" ? null : "concierge")}
                  >
                    {expandedResource === "concierge" ? "Hide Details" : "Show Details"}
                  </Button>
                  {expandedResource === "concierge" && (
                    <div className="mt-2 p-2 bg-light border rounded animate__animated animate__fadeIn">
                      <div><strong>Task:</strong> User chat, RAG queries, document search</div>
                      <div><strong>Status:</strong> {serverConnected ? "Connected" : "Disconnected"}</div>
                      <div className="mt-2">
                        <strong>Progress:</strong>
                        <div className="progress" style={{ height: "18px", maxWidth: 180 }}>
                          <div
                            className={`progress-bar ${serverConnected ? "bg-success" : "bg-danger"}`}
                            role="progressbar"
                            style={{ width: `${ragTaskStatus.progress}%` }}
                            aria-valuenow={ragTaskStatus.progress}
                            aria-valuemin={0}
                            aria-valuemax={100}
                          >
                            {ragTaskStatus.progress}%
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </li>
                {/* Add more assistants here if needed */}
              </ul>
            </div>
          </div>
          {/* Main Content Area - Adaptive Mosaic Grid */}
          <div
            className="main-content-col animate__animated animate__fadeIn flex-grow-1 d-flex flex-column"
            style={{
              minWidth: 0,
              width: "100%",
              flex: "4 1 0px",
              maxWidth: "100vw",
              height: "100%",
              overflow: "visible",
              position: "relative"
            }}
          >
            {/* Main Content Tabs - Responsive Mosaic */}
            {showGreeting && activeTab === "chat" && (
              <div className="fade-in-out mosaic-chat">
                <ErrorBoundary>
                  <Row className="justify-content-center">
                    <Col xs={12} sm={10} md={8} lg={7} xl={6} className="mx-auto">
                      <Card className="shadow-sm">
                        <Card.Body>
                          <ConciergeGreeting onNameSubmit={handleNameSubmit} />
                        </Card.Body>
                      </Card>
                    </Col>
                  </Row>
                </ErrorBoundary>
              </div>
            )}
            {!showGreeting && activeTab === "chat" && (
              <ErrorBoundary>
                <Row className="justify-content-center mosaic-chat-content">
                  <Col xs={12} sm={10} md={8} lg={7} xl={6} className="mx-auto">
                    <Card className="shadow-sm">
                      <Card.Body>
                        {/* Chat UI: message history and input */}
                        <div className="chat-history mb-3" style={{ maxHeight: "50vh", overflow: "hidden", position: "relative" }}>
                          <div style={{ height: "100%", maxHeight: "50vh", overflowY: "auto", paddingRight: "4px" }}>
                            {messages.length === 0 ? (
                              <div className="text-muted text-center py-4">Start chatting with your SBA Assistant!</div>
                            ) : (
                              messages.map((msg) => (
                                <div key={msg.id} className={`chat-message chat-message-${msg.role} mb-2`}>
                                  <div className={`fw-bold text-${msg.role === 'user' ? 'primary' : 'success'}`}>{msg.role === 'user' ? userName || 'You' : 'Assistant'}:</div>
                                  <div>{msg.content}</div>
                                </div>
                              ))
                            )}
                          </div>
                        </div>
                        <form onSubmit={handleSubmit} className="d-flex flex-row align-items-center gap-2">
                          <input
                            type="text"
                            className="form-control"
                            placeholder="Type your message..."
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            disabled={loading}
                            style={{ flex: 1 }}
                          />
                          <Button type="submit" variant="primary" disabled={loading || !message.trim()}>
                            Send
                          </Button>
                        </form>
                      </Card.Body>
                    </Card>
                  </Col>
                </Row>
              </ErrorBoundary>
            )}
            {activeTab === "browse" && (
              <ErrorBoundary>
                <Row className="mosaic-browse">
                  <Col xs={12}>
                    <SBAContentExplorer selectedResource={selectedProgram} endpoints={endpoints} />
                  </Col>
                </Row>
              </ErrorBoundary>
            )}
            {activeTab === "rag" && (
              <ErrorBoundary>
                <Row className="mosaic-rag">
                  <Col xs={12}>
                    <RAGWorkflowInterface
                      documents={documents}
                      onUpload={handleDocumentUpload}
                      onSearch={handleSearch}
                      onRagQuery={handleRagQuery}
                      searchResults={searchResults}
                      ragResponse={ragResponse}
                      serverConnected={serverConnected}
                    />
                  </Col>
                </Row>
              </ErrorBoundary>
            )}
            {activeTab === "documents" && (
              <ErrorBoundary>
                <Row className="mosaic-documents">
                  <Col xs={12} md={10} className="mx-auto">
                    <Card className="shadow-sm document-center-hero">
                      <Card.Header className="bg-primary text-white">
                        <h3 className="mb-0">Document Center</h3>
                        <p className="mb-0">All your uploaded documents in one place. Upload, view, and manage your files for RAG tasks.</p>
                      </Card.Header>
                      <Card.Body>
                        <Row>
                          <Col xs={12} md={6}>
                            <UploadsManager files={documents} onUpload={fetchDocuments} onRefresh={fetchDocuments} />
                          </Col>
                          <Col xs={12} md={6}>
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
          </div>
        </div>
      </Container>
    </div>
  );
}

export default App;
