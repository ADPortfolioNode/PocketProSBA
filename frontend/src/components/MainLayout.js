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
  const apiUrl = () => {}; // Placeholder, update as needed

  const handleTabChange = (tab) => {
    setActiveTab(tab);
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'chat':
        return <ConciergeChat />;
      case 'browse':
        return <SBAContentExplorer />;
      case 'rag':
        return <RAGWorkflowInterface />;
      case 'documents':
        return <UploadsManagerComponent />;
      case 'sba':
        return <SBAContent />;
      default:
        return <ConciergeChat />;
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
