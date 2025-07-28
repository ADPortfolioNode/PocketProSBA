import React, { useState } from 'react';
import { Container } from 'react-bootstrap';
import SBANavigation from './SBANavigation';
import Header from './Header';
import Footer from './Footer';
import ConciergeChat from './ConciergeChat';
import SBAContentExplorer from './SBAContentExplorer';
import RAGWorkflowInterface from './RAGWorkflowInterface';
import UploadsManagerComponent from './UploadsManager';
import SBAContent from './SBAContent';

function MainLayout() {
  const [activeTab, setActiveTab] = useState('chat');
  const [serverConnected, setServerConnected] = React.useState(true); // Placeholder, update as needed
  
  // Create apiUrl function that returns the correct backend URL
  const apiUrl = (path) => {
    const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000';
    if (backendUrl.includes('localhost')) {
      // For localhost, use relative paths (proxy will handle it)
      return path;
    } else {
      // For remote backend, use absolute URLs
      return `${backendUrl}${path}`;
    }
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
  };

  const handleChatSend = async (message) => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000';
      const apiUrl = backendUrl.includes('localhost') ? '/api/chat' : `${backendUrl}/api/chat`;
      
      console.log('Sending chat message to:', apiUrl);
      
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data;
      
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'chat':
        return <ConciergeChat onSend={handleChatSend} />;
      case 'browse':
        return <SBAContentExplorer />;
      case 'rag':
        return <RAGWorkflowInterface />;
      case 'documents':
        return <UploadsManagerComponent />;
      case 'sba':
        return <SBAContent />;
      default:
        return <ConciergeChat onSend={handleChatSend} />;
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
