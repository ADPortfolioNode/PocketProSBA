import React, { useState, useEffect } from 'react';
import { Container, Alert, Button, Badge, Spinner } from 'react-beta';
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
  const [serverConnected, setServerConnected] = useState(true);
  const [backendError, setBackendError] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);
  const [connectionInfo, setConnectionInfo] = useState(null);

  // Enhanced API URL builder using the new configuration
  const apiUrl = (path) => {
    return buildApiUrl(path);
  };

  // Enhanced health check function
  const checkServerHealth = async () => {
    setIsCheckingHealth(true);
    setBackendError(null);
    try {
      const result = await checkBackendConnection();
      if (result.connected) {
        this.updateConnectionStatus(true, result.data);
        return result;
      }
      return { connected: false, error: 'All connection endpoints failed' };
    } catch (error) {
      console.error('Health check failed:', error);
      return { connected: false, error: 'All connection endpoints failed' };
    }
  };

  // Initialize connection monitoring
  useEffect(() => {
    connectionService.initialize();
    this.startHealthMonitoring();
  }, []);

  // Enhanced health check function
  const checkServerHealth = async () => {
    setIsCheckingHealth(true);
    setBackendError(null);
    try {
      const result = await checkBackendConnection();
      if (result.connected) {
        this.updateConnectionStatus(true, result.data);
        return result;
    } catch (error) {
      console.error('Health check failed:', error);
      return { connected: false, error: 'All connection endpoints failed' };
    }
  }

  // Enhanced health check function
  const checkServerHealth = async () => {
    setIsCheckingHealth(true);
    setBackendError(null);
    try {
      const result = await checkBackendConnection();
      if (result.connected) {
        this.updateConnectionStatus(true, result.data);
        return result;
    } catch (error) {
      console.error('Health check failed:', error);
        return { connected: false, error: 'All connection endpoints failed' };
    }
  }

  // Enhanced health check function
    const checkServerHealth = async () => {
        setIsCheckingHealth(true);
        setBackendError(null);
        try {
            const result = await checkBackendConnection();
            if (result.connected) {
                this.updateConnectionStatus(true, result.data);
                return result;
            } catch (error) {
                console.error('Health check failed:', error);
                return { connected: false, error: 'All connection endpoints failed' };
            }
        }
    }

  // Enhanced health check function
    const checkServerHealth = async () => {
        setIsCheckingHealth(true);
        setBackendError(null);
        try {
            const result = await checkBackendConnection();
            if (result.connected) {
                this.updateConnectionStatus(true, result.data);
                return result;
            } catch (error) {
                console.error('Health check failed:', error);
                return { connected: false, error: 'All connection endpoints failed' };
            }
        }
    }

  // Enhanced health check function
    const checkServerHealth = async () => {
        setIsCheckingHealth(true);
        setBackendError(null);
        try {
            const result = await checkBackendConnection();
            if (result.connected) {
                this.updateConnectionStatus(true, result.data);
                return result;
            } catch (error) {
                console.error('Health check failed:', error);
                return { connected: false, error: 'All connection endpoints failed' };
            }
        }
    }

  // Enhanced health check function
    const checkServerHealth = async () => {
        setIsCheckingHealth(true);
        setBackendError(null);
        try {
            const result = await checkBackendConnection();
            if (result.connected) {
                this.updateConnectionStatus(true, result.data);
                return result;
            } catch (error) {
                console.error('Health check failed:', error);
                return { connected: false, error: 'All connection endpoints failed' };
            }
        }
    }

  // Enhanced health check function
    const checkServerHealth = async () => {
        setIsCheckingHealth(true);
        setBackendError(null);
        try {
            const result = await checkBackendConnection();
            if (result.connected) {
                this.updateConnectionStatus(true, result.data);
                return result;
            } catch (error) {
                console.error('Health check failed:', error);
                return { connected: false, error: 'All connection endpoints failed' };
            }
        }
    }

  // Enhanced health check function
    const checkServerHealth = async () => {
        setisCheckingHealth(true);
        setBackendError(null);
        try {
            const result = await checkBackendConnection();
            if (result.connected) {
                this.updateConnectionStatus(true, result.data);
                return result;
            } catch (error) {
                console.error('Health check failed:', error);
                return { connected: false, error: 'All connection endpoints failed' };
            }
        }
    }

  // Enhanced health check function
    const checkServerHealth = async () => {
        setisCheckingHealth(true);
        setBackendError(null);
        try {
            const result = await checkBackendConnection();
            if (result.connected) {
                this.updateConnectionStatus(true, result.data);
                return result;
            } catch (error) {
                console.error('Health check failed:', error);
                return { connected: false, error: 'All connection endpoints failed' };
            }
        }
    }

  // Enhanced health check function
    const checkserverHealth = async () => {
        setisCheckingHealth(true);
        setBackendError(null);
        try {
            const result = await checkBackendConnection();
            if (result.connected) {
                this.updateConnectionStatus(true, result.data);
                return result;
            } catch (error) {
                console.error('Health check failed:', error);
                return { connected: false, error: 'All connection endpoints failed' };
            }
        }
    }

  // Enhanced health check function
    const checkserverHealth = async () => {
        setisCheckingHealth(true);
        setBackendError(null);
        try {
            const result = await checkBackendConnection();
            if (result.connected) {
                this.updateConnectionStatus(true, result.data);
                return result;
            } catch (error) {
                console.error('Health check failed:', error);
                return { connected: false, error: 'All connection endpoints failed' };
            }
        }
    }

  // Enhanced health check function
    const checkserverHealth = async () => {
        setisCheckingHealth(true);
        setBackendError(null);
        try {
            const result = await checkBackendConnection();
            if (result.connected) {
                this.updateConnectionStatus(true, result.data);
                return result;
            } catch (error) {
                console.error('Health check failed:', error);
                return { connected: false, error: 'All connection endpoints failed' };
            }
        }
    }

  // Enhanced health check function
    const checkserverHealth = async () => {
        setisCheckingHealth(true);
        setBackendError(null);
        try {
            const result = await checkBackendConnection();
            if (result.connected) {
                this.updateConnectionStatus(true, result.data);
                return result;
            } catch (error) {
                console.error('Health check failed:', error);
                return { connected: false, error: 'All connection endpoints failed' };
            }
        }
    }

  // Enhanced health check function
    const checkserverHealth = async () => {
        setisCheckingHealth(true);
        setBackendError(null);
        try {
            const result = await checkBackendConnection();
            if (result.connected) {
                this.updateConnectionStatus(true, result.data);
                return result;
            } catch (error) {
                console.error('Health check failed:', error);
                return { connected: false, error: 'All connection endpoints failed' };
            }
        }
    }

  // Enhanced health check function
    const checkserverHealth = async () => {
        setisCheckingHealth(true);
        setBackendError(null);
        try {
            const result = await checkBackendConnection();
            if (result.connected) {
                this.updateConnectionStatus(true, result.data);
                return result;
            } catch (error) {
                console.error('Health check failed:', error);
                return { connected: false, error: 'All connection endpoints failed' };
            }
        }
    }

  // Enhanced health check function
    const checkserverHealth = async () => {
        setisCheckingHealth(true);
        setBackendError(null);
        try {
            const result = await checkBackendConnection();
            if (result.connected) {
                this.updateConnectionStatus(true, result.data);
                return result;
            } catch (error) {
                console.error('Health check failed:', error);
                return { connected: false, error: 'All connection endpoints failed' };
            }
        }
    }

  // Enhanced health check function
    const checkserverHealth = async () => {
        setisCheckingHealth(true);
                setBackendError(null);
                try {
                    const result = await checkBackendConnection();
                    if (result.connected) {
                        this.updateConnectionStatus(true, result.data);
                        return result;
                    } catch (error) {
                        console.error('Health check failed:', error);
                        return { connected: false, error: 'All connection endpoints failed' };
                    }
                }
            }

  // Enhanced health check function
    const checkserverHealth = async () => {
        setisCheckingHealth(true);
                setBackendError(null);
                try {
                    const result = await checkBackendConnection();
                    if<edit_file>
<path>frontend/src/components/MainLayout.js</path>
<content>
<<<<<<< SEARCH
import React, { useState, useEffect } from 'react';
import { Container, Alert, Button } from 'react-bootstrap';
import SBANavigation from './SBANavigation';
import Header from './Header';
import Footer from './Footer';
import SBAContentExplorer from './SBAContentExplorer';
import RAGWorkflowInterface from './RAGWorkflowInterface';
import ModernConciergeChat from './ModernConciergeChat';
import UploadsManagerComponent from './UploadsManager';
import SBAContent from './SBAContent';
=======
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
>>>>>>> REPLACE
function MainLayout() {
  const [activeTab, setActiveTab] = useState('chat');
  const [serverConnected, setServerConnected] = useState(true);
  const [backendError, setBackendError] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);
<<<<<<< SEARCH
  // Create apiUrl function that returns the correct backend URL
  const apiUrl = (path) => {
    const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000';
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    
    if (backendUrl.includes('localhost') || backendUrl.includes('127.0.0.1')) {
      // For localhost, use relative paths (proxy will handle it)
      return cleanPath;
    } else {
      // For remote backend, use absolute URLs
      return `${backendUrl}${cleanPath}`;
    }
  };
=======
  const [connectionInfo, setConnectionInfo] = useState(null);
  // Enhanced API URL builder using the new configuration
  const apiUrl = (path) => {
    return buildApiUrl(path);
  };
>>>>>>> REPLACE
  // Health check function
  const checkServerHealth = async () => {
    setIsCheckingHealth(true);
    try {
      const healthUrl = apiUrl('/api/health');
      const response = await fetch(healthUrl, {
        method: 'GET',
        signal: AbortSignal.timeout(10000), // 10 second timeout for health check
      });
      
      if (response.ok) {
        setServerConnected(true);
        setBackendError(null);
        return true;
      } else {
        setServerConnected(false);
        return false;
      }
    } catch (error) {
      console.error('Health check failed:', error);
      setServerConnected(false);
      return false;
    } finally {
      setIsCheckingHealth(false);
    }
  };

  useEffect(() => {
    // Initial health check
    checkServerHealth();
    
    // Set up periodic health checks
    const healthCheckInterval = setInterval(checkServerHealth, 30000);
    
    return () => clearInterval(healthCheckInterval);
  }, []);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setBackendError(null); // Clear errors when changing tabs
  };

  const handleChatSend = async (message) => {
    try {
      setBackendError(null);
      
      // Add user message to local state
      const userMessage = { role: 'user', content: message };
      setMessages(prev => [...prev, userMessage]);
      
      const chatUrl = apiUrl('/api/chat');
      console.log('Sending request to:', chatUrl);
      
      const response = await fetch(chatUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
        signal: AbortSignal.timeout(30000), // 30 second timeout for chat
      });
      
      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`Server error: ${response.status} - ${errorData || response.statusText}`);
      }
      
      const data = await response.json();
      
      // Add assistant response to local state
      const assistantMessage = { role: 'assistant', content: data.response || data.message || 'Response received' };
      setMessages(prev => [...prev, assistantMessage]);
      
      return data;
      
    } catch (error) {
      console.error('Error sending message:', error);
      
      let errorMessage = 'Failed to send message. ';
      
      if (error.name === 'AbortError') {
        errorMessage += 'Request timed out. Please check your connection.';
      } else if (error.message.includes('Failed to fetch')) {
        errorMessage += 'Unable to connect to server. Please check if the backend is running.';
      } else if (error.message.includes('504')) {
        errorMessage += 'Server is taking too long to respond. This might be due to high load or processing time.';
      } else {
        errorMessage += error.message;
      }
      
      setBackendError(errorMessage);
      
      // Add error message to chat
      const errorChatMessage = { role: 'system', content: errorMessage };
      setMessages(prev => [...prev, errorChatMessage]);
      
      throw error;
    }
  };

  const renderContent = () => {
    if (backendError && !serverConnected) {
      return (
        <Alert variant="danger" className="mt-4">
          <Alert.Heading>Connection Error</Alert.Heading>
          <p>{backendError}</p>
          <hr />
          <p className="mb-0">
            Please check your internet connection and ensure the backend server is running.
          </p>
          <Button 
            variant="outline-danger" 
            onClick={checkServerHealth} 
            className="mt-2"
            disabled={isCheckingHealth}
          >
            {isCheckingHealth ? 'Checking...' : 'Retry Connection'}
          </Button>
        </Alert>
      );
    }

    switch (activeTab) {
      case 'chat':
        return (
          <ModernConciergeChat 
            onSend={handleChatSend} 
            messages={messages}
            loading={!serverConnected}
            userName="User"
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
      />
      <Container className="flex-grow-1">
        {renderContent()}
      </Container>
      <Footer />
    </div>
  );
}

export default MainLayout;
