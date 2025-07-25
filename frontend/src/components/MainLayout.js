import React, { useState } from 'react';
import { Container } from 'react-bootstrap';
import SBANavigation from './SBANavigation';
import Header from './Header';
import Footer from './Footer';

function MainLayout({ children }) {
  const [activeTab, setActiveTab] = useState('chat');
  const [serverConnected, setServerConnected] = React.useState(true); // Placeholder, update as needed
  const apiUrl = () => {}; // Placeholder, update as needed

  const handleTabChange = (tab) => {
    setActiveTab(tab);
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
        {children}
      </Container>
      <Footer />
    </div>
  );
}

export default MainLayout;
