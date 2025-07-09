import React, { useState, useEffect } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";
import { Container, Row, Col, Card, Button, Form, Navbar, Nav } from "react-bootstrap";
import SBANavigation from "./components/SBANavigation";
import RAGWorkflowInterface from "./components/RAGWorkflowInterface";
import SBAContentExplorer from "./components/SBAContentExplorer";
import ConnectionStatusIndicator from "./components/ConnectionStatusIndicator";
import LoadingIndicator from "./components/LoadingIndicator";
import ErrorBoundary from "./components/ErrorBoundary";

function App() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("chat");
  const [serverConnected, setServerConnected] = useState(false);
  const [selectedProgram, setSelectedProgram] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [ragResponse, setRagResponse] = useState(null);
  
  // Check backend connection on load
  useEffect(() => {
    checkServerConnection();
    fetchDocuments(); // Fetch documents on load
  }, []);
  
  const checkServerConnection = async () => {
    try {
      const response = await fetch('/api/health');
      
      if (response.ok) {
        const data = await response.json();
        console.log("Backend connected:", data);
        setServerConnected(true);
      } else {
        console.error("Backend connection failed with status:", response.status);
        setServerConnected(false);
      }
    } catch (error) {
      console.error("Backend connection error:", error);
      setServerConnected(false);
    }
  };
  
  // Fetch documents from the backend
  const fetchDocuments = async () => {
    if (!serverConnected) {
      console.log("Server not connected, skipping document fetch");
      return;
    }
    
    try {
      const response = await fetch('/api/documents/list');
      
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

    // Store current message to avoid state closure issues
    const currentMessage = message;
    
    // Add user message
    setMessages(prevMessages => [...prevMessages, { id: Date.now(), role: "user", content: currentMessage }]);
    setLoading(true);
    setMessage(""); // Clear input immediately for better UX
    
    // Call backend with RAG if server is connected
    if (serverConnected) {
      fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: currentMessage }),
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
          // Fallback to simulated response on error
          simulateResponse(currentMessage);
        });
    } else {
      // Simulate response if server is not connected
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
      const response = await fetch("/api/documents/upload", {
        method: "POST",
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`Upload failed with status ${response.status}`);
      }
      
      const result = await response.json();
      
      // Refresh the document list after successful upload
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
      const response = await fetch(`/api/documents/search?query=${encodeURIComponent(query)}`);
      
      if (!response.ok) {
        throw new Error(`Search failed with status ${response.status}`);
      }
      
      const results = await response.json();
      setSearchResults(results.matches || []);
      return results;
    } catch (error) {
      console.error("Error searching documents:", error);
      // Return mock results for now
      const mockResults = [
        { id: 1, title: "SBA Loan Programs", snippet: "Information about various SBA loan programs...", score: 0.92 },
        { id: 2, title: "Business Plan Guide", snippet: "How to create an effective business plan...", score: 0.85 }
      ];
      setSearchResults(mockResults);
      return { matches: mockResults };
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
  
  return (
    <div className="App">
      <SBANavigation 
        activeTab={activeTab} 
        onTabChange={handleTabChange}
        serverConnected={serverConnected}
      />
      
      <Container fluid className="py-4">
        {activeTab === "chat" && (
          <Row className="justify-content-center">
            <Col xs={12} md={10} lg={8} xl={7}>
              <Card className="shadow-sm">
                <Card.Header className="d-flex justify-content-between align-items-center">
                  <h4>Chat with SBA Assistant</h4>
                  <ConnectionStatusIndicator connected={serverConnected} />
                </Card.Header>
                <Card.Body>
                  <div className="chat-messages">
                    {messages.length === 0 ? (
                      <div className="welcome-message">
                        <h5>Welcome to PocketPro SBA Assistant</h5>
                        <p>Ask me anything about SBA programs and resources!</p>
                      </div>
                    ) : (
                      messages.map(msg => (
                        <div 
                          key={msg.id} 
                          className={`message ${msg.role === "user" ? "user-message" : "assistant-message"}`}
                        >
                          {msg.content}
                        </div>
                      ))
                    )}
                    
                    {loading && (
                      <div className="message assistant-message">
                        <LoadingIndicator text="Thinking..." />
                      </div>
                    )}
                  </div>
                </Card.Body>
                <Card.Footer>
                  <Form onSubmit={handleSubmit}>
                    <Form.Group className="d-flex">
                      <Form.Control
                        type="text"
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        placeholder="Type your message here..."
                      />
                      <Button type="submit" variant="primary" className="ms-2">
                        Send
                      </Button>
                    </Form.Group>
                  </Form>
                </Card.Footer>
              </Card>
            </Col>
          </Row>
        )}
        
        {activeTab === "browse" && (
          <ErrorBoundary>
            <Row>
              <Col>
                <SBAContentExplorer
                  selectedProgram={selectedProgram}
                  setSelectedProgram={setSelectedProgram}
                  serverConnected={serverConnected}
                />
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
                  onDocumentUpload={handleDocumentUpload}
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
              <Col>
                <Card className="shadow-sm">
                  <Card.Header>
                    <h4>Document Center</h4>
                  </Card.Header>
                  <Card.Body>
                    {documents.length > 0 ? (
                      <div className="document-list">
                        {documents.map((doc, index) => (
                          <div key={index} className="document-item mb-3 p-3 border rounded">
                            <h5>{doc.filename}</h5>
                            <div className="document-meta">
                              <span className="me-3">Type: {doc.type || 'Unknown'}</span>
                              <span className="me-3">Size: {Math.round(doc.size / 1024)} KB</span>
                              <span>Modified: {doc.modified}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="no-documents-message">
                        <p>No documents found. Upload documents in the RAG tab to get started.</p>
                      </div>
                    )}
                  </Card.Body>
                  <Card.Footer>
                    <Button 
                      variant="primary" 
                      onClick={() => handleTabChange("rag")}
                    >
                      Upload Documents
                    </Button>
                    <Button 
                      variant="outline-secondary" 
                      className="ms-2"
                      onClick={fetchDocuments}
                    >
                      Refresh
                    </Button>
                  </Card.Footer>
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
