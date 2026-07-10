import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
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
import Home from './Home';
import { useConnection } from '../hooks/useConnection'; // Import the new hook

const ROUTE_TAB_MAP = {
  '': 'home',
  home: 'home',
  chat: 'chat',
  browse: 'browse',
  resources: 'browse',
  rag: 'rag',
  documents: 'documents',
  sba: 'sba',
  orchestrator: 'orchestrator'
};

function MainLayout({ useConnectionHook = useConnection }) {
  const [activeTab, setActiveTab] = useState('home');
  const location = useLocation();

  const resolveTabFromPath = (pathname) => {
    const segment = (pathname.split('/')[1] || '').toLowerCase();
    return ROUTE_TAB_MAP[segment] || 'chat';
  };

  useEffect(() => {
    const tab = resolveTabFromPath(location.pathname);
    setActiveTab(tab);
    // Prefer the live standalone Resources UI (nginx → resources.html)
    // so click-to-load + detail cards work without a CRA rebuild.
    const path = (location.pathname || '').toLowerCase();
    if (path === '/browse' || path === '/resources') {
      if (typeof window !== 'undefined' && !window.__PP_RESOURCES_REDIRECT__) {
        window.__PP_RESOURCES_REDIRECT__ = true;
        window.location.replace('/browse');
      }
    }
  }, [location.pathname]);
  const [messages, setMessages] = useState([]);
  const [diagnostics, setDiagnostics] = useState(null);

  // Use the custom connection hook or injected test hook
  const {
    serverConnected,
    backendError,
    isCheckingHealth,
    connectionInfo,
    checkConnection,
    apiCall,
    getDiagnostics,
    resetConnection,
  } = useConnectionHook();

  const getConnectionBaseUrl = () => {
    return connectionInfo?.server?.self || connectionInfo?.self || connectionInfo?.source || 'http://localhost:5000';
  };

  const getConnectionLabel = () => {
    return connectionInfo?.server?.self || connectionInfo?.self || connectionInfo?.source || 'Unknown';
  };

  const apiUrl = (path) => {
    const baseUrl = getConnectionBaseUrl();
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    return `${baseUrl.replace(/\/$/, '')}${normalizedPath}`;
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
                  <li><Badge bg="secondary">Backend URL</Badge> {getConnectionLabel()}</li>
              <li><Badge bg="secondary">Environment</Badge> {connectionInfo?.environment || connectionInfo?.server?.environment || connectionInfo?.source || 'Unknown'}</li>
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
      case 'home':
        return <Home />;
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
        return <Home />;
    }
  };

  return (
    <div className="pp-app d-flex flex-column min-vh-100">
      <Header />
      <SBANavigation
        serverConnected={serverConnected}
        apiUrl={apiUrl}
      />
      <main className="pp-main flex-grow-1">
        <Container className="pp-main-inner">
          {renderContent()}
        </Container>
      </main>
      <Footer />
    </div>
  );
}

export default MainLayout;
