import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Container } from 'react-bootstrap';
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
import LoadingBar from './LoadingBar';
import { ErrorState } from './AsyncState';
import { useSlowFlag } from '../hooks/useAsync';
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
    // Prefer live standalone Resources browser for /browse only.
    // /sba stays on SPA so SBA Programs | Lifecycle | Local tabs (API cards) render.
    const path = (location.pathname || '').toLowerCase();
    if (path === '/browse' || path === '/resources') {
      // Reload once so the server can serve resources.html. If we land back here
      // within a few seconds, the server has no /browse alias (e.g. a plain SPA
      // fallback): stay in the SPA explorer instead of reloading forever.
      if (typeof window !== 'undefined' && !window.__PP_RESOURCES_REDIRECT__) {
        window.__PP_RESOURCES_REDIRECT__ = true;
        let recent = false;
        try {
          const last = Number(window.sessionStorage.getItem('pp_browse_redirect_at') || 0);
          recent = Date.now() - last < 10000;
          if (!recent) window.sessionStorage.setItem('pp_browse_redirect_at', String(Date.now()));
        } catch (_) { /* storage blocked: fall through to one redirect */ }
        if (!recent) window.location.replace('/browse');
      }
    }
  }, [location.pathname]);
  const [messages, setMessages] = useState([]);
  const [chatPending, setChatPending] = useState(false);

  // Use the custom connection hook or injected test hook
  const {
    status: connectionStatus,
    serverConnected,
    backendError,
    isCheckingHealth,
    connectionInfo,
    checkConnection,
    retryConnection,
    apiCall,
  } = useConnectionHook();

  // Older/injected hooks may not report `status`; derive it so a missing first
  // result reads as "checking" (loader), never as an error.
  const status = connectionStatus
    || (serverConnected ? 'online' : (backendError ? 'offline' : 'checking'));
  const slowConnect = useSlowFlag(status === 'checking', 5000);
  const retry = retryConnection || checkConnection;

  const getConnectionBaseUrl = () => {
    return connectionInfo?.server?.self || connectionInfo?.self || connectionInfo?.source || 'http://localhost:5000';
  };

  const apiUrl = (path) => {
    const baseUrl = getConnectionBaseUrl();
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    return `${baseUrl.replace(/\/$/, '')}${normalizedPath}`;
  };

  const handleChatSend = async (message) => {
    const userMessage = { role: 'user', content: message };
    setMessages(prev => [...prev, userMessage]);
    setChatPending(true);
    try {
      const response = await apiCall('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_id: 1, message })
      });

      const assistantMessage = {
        role: 'assistant',
        content: response.response || response.message || 'Response received'
      };
      setMessages(prev => [...prev, assistantMessage]);
      return response;
    } catch (error) {
      console.error('Error sending message:', error);
      // Drop the unsent user bubble; the chat keeps the text in its input and
      // shows one friendly error with "Try again" (see ModernConciergeChat).
      setMessages(prev => prev.filter(m => m !== userMessage));
      if (!error.response) checkConnection();
      throw error;
    } finally {
      setChatPending(false);
    }
  };

  // Tabs that need the backend. Home is static and always renders.
  const needsBackend = activeTab !== 'home';

  const renderConnectionStatus = () => {
    if (!needsBackend || status === 'online') return null;
    if (status === 'checking') {
      return (
        <LoadingBar
          className="mt-4"
          label="Connecting to PocketPro…"
          slow={slowConnect}
          data-testid="connection-loading"
        />
      );
    }
    return (
      <ErrorState
        title="We can't reach PocketPro right now"
        message={backendError || "The service isn't responding. It may be restarting — please try again."}
        onRetry={() => retry()}
        retryLabel={isCheckingHealth ? 'Retrying…' : 'Retry'}
      />
    );
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
            loading={chatPending}
            userName="User"
            connectionInfo={connectionInfo}
            initialDraft={location.state?.draft}
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
        connectionStatus={status}
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
