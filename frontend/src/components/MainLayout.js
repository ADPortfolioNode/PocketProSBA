import React, { useState } from 'react';
import { Container, Alert, Button, Badge, Spinner } from 'react-bootstrap';
import SBANavigation from './SBANavigation';
import Header from './Header';
import Footer from './Footer';
import SBAContentExplorer from './SBAContentExplorer';
import RAGWorkflowInterface from './RAGWorkflowInterface';
import ModernConciergeChat from './ModernConciergeChat';
import UploadsManagerComponent from './UploadsManager';
import SBAContent from './SBAContent';
import TaskOrchestrator from './TaskOrchestrator';
import { useConnection } from '../hooks/useConnection'; // Import the new hook

function MainLayout() {
  const [activeTab, setActiveTab] = useState('chat');
  const [messages, setMessages] = useState([]);
  const [diagnostics, setDiagnostics] = useState(null);

  // Use the custom connection hook
  const {
    serverConnected,
    backendError,
    isCheckingHealth,
    connectionInfo,
    checkConnection,
    apiCall,
    getDiagnostics,
    resetConnection,
  } = useConnection();

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    // No need to setBackendError(null) here, as useConnection manages it
  };

  const handleChatSend = async (message) => {
    try {
      // No need to setBackendError(null) here, as useConnection manages it
      
      const userMessage = { role: 'user', content: message };
      setMessages(prev => [...prev, userMessage]);
      
      const response = await apiCall('/api/chat', { // Use apiCall from hook
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_id: 1, message }) // Include user_id in the request
      });
      
      const assistantMessage = { 
        role: 'assistant', 
        content: response.response || response.message || 'Response received' 
      };
      setMessages(prev => [...prev, assistantMessage]);
      
      return response;
      
    } catch (error) {
      console.error('Error sending message:', error);
      
      let errorMessage = 'Failed to send message. ';
      
      if (error.name === 'AbortError') {
        errorMessage += 'Request timed out. Please check your connection.';
      } else if (error.message.includes('Failed to fetch')) {
        errorMessage += 'Unable to connect to server. Checking connection...';
        // Auto-retry connection
        await checkConnection(); // Use checkConnection from hook
      } else {
        errorMessage += error.message;
      }
      
      // No need to setBackendError(errorMessage) here, as useConnection manages it
      
      const errorChatMessage = { role: 'system', content: errorMessage };
      setMessages(prev => [...prev, errorChatMessage]);
      
      throw error;
    }
  };

  const showDiagnostics = async () => {
    const diag = await getDiagnostics(); // Use getDiagnostics from hook
    setDiagnostics(diag);
    console.log('Connection Diagnostics:', diag);
  };

  const renderConnectionStatus = () => {
    if (!serverConnected) {
      return (
        <Alert variant="danger" className="mt-4">
          <Alert.Heading>
            <Spinner animation="border" size="sm" className="me-2" />
            Connection Error
          </Alert.Heading>
          <p><strong>Error:</strong> {backendError}</p>
          
          <div className="mb-3">
            <strong>Connection Details:</strong>
            <ul>
              <li><Badge bg="secondary">Backend URL</Badge> {connectionInfo?.source || 'Unknown'}</li>
              <li><Badge bg="secondary">Environment</Badge> {connectionInfo?.source || 'Unknown'}</li>
              <li><Badge bg="secondary">Last checked</Badge> {new Date().toLocaleTimeString()}</li>
            </ul>
          </div>
          
          <div className="d-flex gap-2">
            <Button 
              variant="outline-danger" 
              onClick={checkConnection} // Use checkConnection from hook
              className="me-2"
              disabled={isCheckingHealth}
            >
              {isCheckingHealth ? 'Checking...' : 'Retry Connection'}
            </Button>
            <Button 
              variant="outline-secondary" 
              onClick={showDiagnostics}
            >
              Show Diagnostics
            </Button>
            <Button 
              variant="outline-info" 
              onClick={async () => {
                await resetConnection(); // Use resetConnection from hook
                await checkConnection(); // Use checkConnection from hook
              }}
            >
              Reset Connection
            </Button>
          </div>

          {diagnostics && (
            <div className="mt-3">
              <strong>Diagnostics:</strong>
              <pre className="bg-light p-2 rounded" style={{ fontSize: '0.8em', maxHeight: '200px', overflow: 'auto' }}>
                {JSON.stringify(diagnostics, null, 2)}
              </pre>
            </div>
          )}
        </Alert>
      );
    }

    return null;
  };

  const renderContent = () => {
    const connectionAlert = renderConnectionStatus();
    
    if (connectionAlert) {
      return connectionAlert;
    }

    switch (activeTab) {
      case 'chat':
        return (
          <ModernConciergeChat
            onSend={handleChatSend}
            messages={messages}
            loading={!serverConnected}
            userName="User"
            connectionInfo={connectionInfo}
          />
        );
      case 'browse':
        return <SBAContentExplorer />;
      case 'rag':
        return <RAGWorkflowInterface />;
      case 'documents':
        return <UploadsManagerComponent />;
      case 'sba':
        return <SBAContent />;
      case 'orchestrator':
        return <TaskOrchestrator />;
      default:
        return (
          <ModernConciergeChat
            onSend={handleChatSend}
            messages={messages}
            loading={!serverConnected}
            userName="User"
            connectionInfo={connectionInfo}
          />
        );
    }
  };

  return (
    <div className="d-flex flex-column min-vh-100">
      <Header />
      <SBANavigation
        activeTab={activeTab}
        onTabChange={handleTabChange}
        serverConnected={serverConnected}
        apiUrl={connectionInfo?.source || 'http://localhost:5000'}
      />
      <Container className="flex-grow-1">
        {renderContent()}
      </Container>
      <Footer />
    </div>
  );
}

export default MainLayout;
