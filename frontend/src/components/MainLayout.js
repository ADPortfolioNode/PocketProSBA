import React, { useState, useEffect } from 'react';
import { Container, Alert, Button, Badge, Spinner } from 'react-bootstrap';
import SBANavigation from './SBANavigation';
import Header from './Header';
import Footer from './Footer';
import SBAContentExplorer from './SBAContentExplorer';
import RAGWorkflowInterface from './RAGWorkflowInterface';
import ModernConciergeChat from './ModernConciergeChat';
import UploadsManagerComponent from './UploadsManager';
import SBAContent from './SBAContent';
import connectionService from '../services/connectionService';
import { buildApiUrl } from '../config/api';

function MainLayout() {
  const [activeTab, setActiveTab] = useState('chat');
  const [serverConnected, setServerConnected] = useState(false);
  const [backendError, setBackendError] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);
  const [connectionInfo, setConnectionInfo] = useState(null);
  const [diagnostics, setDiagnostics] = useState(null);

  // Enhanced API URL builder using the new configuration
  const apiUrl = (path) => {
    return buildApiUrl(path);
  };

  // Enhanced health check function
  const checkServerHealth = async () => {
    setIsCheckingHealth(true);
    setBackendError(null);
    
    try {
      const result = await connectionService.checkConnection();
      
      if (result.connected) {
        setServerConnected(true);
        setConnectionInfo(result.info || result);
        setBackendError(null);
        return true;
      } else {
        setServerConnected(false);
        setConnectionInfo(null);
        setBackendError(result.error || 'Unable to connect to backend server');
        return false;
      }
    } catch (error) {
      console.error('Health check failed:', error);
      setServerConnected(false);
      setBackendError(error.message || 'Connection failed');
      return false;
    } finally {
      setIsCheckingHealth(false);
    }
  };

  // Initialize connection monitoring
  useEffect(() => {
    // Initialize connection service
    connectionService.initialize();
    
    // Set up connection status listener
    const unsubscribe = connectionService.addConnectionListener((status) => {
      setServerConnected(status.connected);
      setConnectionInfo(status.info);
      
      if (!status.connected && status.error) {
        setBackendError(status.error);
      }
    });

    // Initial health check
    checkServerHealth();
    
    return () => {
      unsubscribe();
      connectionService.stopHealthMonitoring();
    };
  }, []);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setBackendError(null);
  };

  const handleChatSend = async (message) => {
    try {
      setBackendError(null);
      
      const userMessage = { role: 'user', content: message };
      setMessages(prev => [...prev, userMessage]);
      
      const response = await connectionService.apiCall('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message })
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
        await checkServerHealth();
      } else {
        errorMessage += error.message;
      }
      
      setBackendError(errorMessage);
      
      const errorChatMessage = { role: 'system', content: errorMessage };
      setMessages(prev => [...prev, errorChatMessage]);
      
      throw error;
    }
  };

  const showDiagnostics = async () => {
    const diag = await connectionService.getDiagnostics();
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
              <li><Badge bg="secondary">Backend URL</Badge> {apiUrl('')}</li>
              <li><Badge bg="secondary">Environment</Badge> {connectionInfo?.source || 'Unknown'}</li>
              <li><Badge bg="secondary">Last checked</Badge> {new Date().toLocaleTimeString()}</li>
            </ul>
          </div>
          
          <div className="d-flex gap-2">
            <Button 
              variant="outline-danger" 
              onClick={checkServerHealth} 
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
                await connectionService.resetConnection();
                await checkServerHealth();
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
        apiUrl={apiUrl}
        connectionInfo={connectionInfo}
      />
      <Container className="flex-grow-1">
        {renderContent()}
      </Container>
      <Footer />
    </div>
  );
}

export default MainLayout;
