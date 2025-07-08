import React, { useState, useEffect } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";
import { Container, Row, Col, Card, Button, Form, Navbar, Nav, Tab, Tabs } from "react-bootstrap";
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
  }, []);
  
  const checkServerConnection = async () => {
    try {
      const response = await fetch("http://localhost:5000/health");
      if (response.ok) {
        setServerConnected(true);
      } else {
        setServerConnected(false);
      }
    } catch (error) {
      console.error("Server connection error:", error);
      setServerConnected(false);
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
        body: JSON.stringify({ query: currentMessage }),
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
      const response = await fetch("http://localhost:5000/api/documents/upload", {
        method: "POST",
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`Upload failed with status ${response.status}`);
      }
      
      const result = await response.json();
      setDocuments(prev => [...prev, result.document]);
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
      const response = await fetch(`http://localhost:5000/api/documents/search?query=${encodeURIComponent(query)}`);
      
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
      const response = await fetch("http://localhost:5000/api/rag/query", {
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

  return (
    <div className="App">
      <Navbar bg="primary" variant="dark" expand="lg" className="mb-3">
        <Container>
          <Navbar.Brand href="#home">PocketPro SBA Assistant</Navbar.Brand>
          <ConnectionStatusIndicator connected={serverConnected} />
          <Navbar.Toggle aria-controls="basic-navbar-nav" />
          <Navbar.Collapse id="basic-navbar-nav">
            <Nav className="ms-auto">
              <Nav.Link 
                href="#chat" 
                active={activeTab === "chat"}
                onClick={() => setActiveTab("chat")}
              >
                Chat
              </Nav.Link>
              <Nav.Link 
                href="#browse" 
                active={activeTab === "browse"}
                onClick={() => setActiveTab("browse")}
              >
                Browse Resources
              </Nav.Link>
              <Nav.Link 
                href="#documents" 
                active={activeTab === "documents"}
                onClick={() => setActiveTab("documents")}
              >
                Document Center
              </Nav.Link>
            </Nav>
          </Navbar.Collapse>
        </Container>
      </Navbar>
      
      <Container className="main-container">
        {activeTab === "chat" && (
          <Row>
            <Col>
              <Card className="chat-card">
                <Card.Header>
                  <h4>Chat with SBA Assistant</h4>
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
                <SBANavigation 
                  onProgramSelect={setSelectedProgram} 
                  onResourceSelect={() => {}} 
                />
              </Col>
            </Row>
            <Row className="mt-3">
              <Col>
                <SBAContentExplorer />
              </Col>
            </Row>
          </ErrorBoundary>
        )}
        
        {activeTab === "documents" && (
          <ErrorBoundary>
            <Row>
              <Col>
                <RAGWorkflowInterface 
                  onSearch={handleSearch}
                  onUpload={handleDocumentUpload}
                  onQuery={handleRagQuery}
                  documents={documents}
                  searchResults={searchResults}
                  ragResponse={ragResponse}
                />
              </Col>
            </Row>
          </ErrorBoundary>
        )}
      </Container>
    </div>
  );
}

export default App;
