import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Navbar, Nav, Card, Alert, Button, Offcanvas, Badge } from 'react-bootstrap';
import { Bell, Menu, X, Home, MessageSquare, FolderOpen, Settings, User, BarChart3, FileText } from 'react-feather';
import './NewMainLayout.css';

const NewMainLayout = () => {
  const [activeSection, setActiveSection] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [userProfile, setUserProfile] = useState({ name: 'User', avatar: null });
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
      if (window.innerWidth >= 768) {
        setSidebarOpen(false);
      }
    };
    
    window.addEventListener('resize', handleResize);
    handleResize();
    
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const navigationItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Home, badge: null },
    { id: 'chat', label: 'SBA Assistant', icon: MessageSquare, badge: 3 },
    { id: 'documents', label: 'Documents', icon: FolderOpen, badge: null },
    { id: 'analytics', label: 'Analytics', icon: BarChart3, badge: null },
    { id: 'resources', label: 'SBA Resources', icon: FileText, badge: null },
    { id: 'settings', label: 'Settings', icon: Settings, badge: null }
  ];

  const renderContent = () => {
    switch (activeSection) {
      case 'dashboard':
        return <DashboardSection />;
      case 'chat':
        return <ChatSection />;
      case 'documents':
        return <DocumentsSection />;
      case 'analytics':
        return <AnalyticsSection />;
      case 'resources':
        return <ResourcesSection />;
      case 'settings':
        return <SettingsSection />;
      default:
        return <DashboardSection />;
    }
  };

  const Sidebar = () => (
    <div className={`sidebar ${sidebarOpen ? 'open' : ''} ${isMobile ? 'mobile' : ''}`}>
      <div className="sidebar-header">
        <h4 className="brand">PocketPro SBA</h4>
        {isMobile && (
          <Button variant="link" className="close-btn" onClick={() => setSidebarOpen(false)}>
            <X size={24} />
          </Button>
        )}
      </div>
      
      <Nav className="flex-column sidebar-nav">
        {navigationItems.map(item => (
          <Nav.Link
            key={item.id}
            className={`sidebar-nav-item ${activeSection === item.id ? 'active' : ''}`}
            onClick={() => {
              setActiveSection(item.id);
              if (isMobile) setSidebarOpen(false);
            }}
          >
            <item.icon size={20} className="nav-icon" />
            <span>{item.label}</span>
            {item.badge && <Badge bg="primary" className="ms-auto">{item.badge}</Badge>}
          </Nav.Link>
        ))}
      </Nav>
      
      <div className="sidebar-footer">
        <div className="user-profile">
          <div className="user-avatar">
            {userProfile.avatar ? (
              <img src={userProfile.avatar} alt={userProfile.name} />
            ) : (
              <User size={24} />
            )}
          </div>
          <div className="user-info">
            <span className="user-name">{userProfile.name}</span>
            <small className="user-status">Online</small>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="new-main-layout">
      {/* Top Navigation */}
      <Navbar bg="white" expand="lg" className="top-navbar shadow-sm">
        <Container fluid>
          <Button 
            variant="link" 
            className="sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            <Menu size={24} />
          </Button>
          
          <Navbar.Brand className="d-none d-md-block">PocketPro SBA Assistant</Navbar.Brand>
          
          <div className="ms-auto d-flex align-items-center">
            <Button variant="link" className="notification-btn">
              <Bell size={20} />
              {notifications.length > 0 && (
                <Badge bg="danger" className="position-absolute top-0 end-0">
                  {notifications.length}
                </Badge>
              )}
            </Button>
          </div>
        </Container>
      </Navbar>

      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <div className={`main-content ${sidebarOpen && isMobile ? 'overlay' : ''}`}>
        <Container fluid>
          <Row>
            <Col>
              {renderContent()}
            </Col>
          </Row>
        </Container>
      </div>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && isMobile && (
        <div 
          className="sidebar-overlay" 
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
};

// New Section Components
const DashboardSection = () => (
  <div className="dashboard-section">
    <h2 className="section-title">Dashboard</h2>
    <Row>
      <Col lg={3} md={6} className="mb-4">
        <Card className="stat-card">
          <Card.Body>
            <div className="stat-icon">
              <MessageSquare size={32} />
            </div>
            <div className="stat-info">
              <h3>247</h3>
              <p>Chat Sessions</p>
            </div>
          </Card.Body>
        </Card>
      </Col>
      <Col lg={3} md={6} className="mb-4">
        <Card className="stat-card">
          <Card.Body>
            <div className="stat-icon">
              <FileText size={32} />
            </div>
            <div className="stat-info">
              <h3>156</h3>
              <p>Documents</p>
            </div>
          </Card.Body>
        </Card>
      </Col>
      <Col lg={3} md={6} className="mb-4">
        <Card className="stat-card">
          <Card.Body>
            <div className="stat-icon">
              <BarChart3 size={32} />
            </div>
            <div className="stat-info">
              <h3>89%</h3>
              <p>Success Rate</p>
            </div>
          </Card.Body>
        </Card>
      </Col>
      <Col lg={3} md={6} className="mb-4">
        <Card className="stat-card">
          <Card.Body>
            <div className="stat-icon">
              <User size={32} />
            </div>
            <div className="stat-info">
              <h3>1,234</h3>
              <p>Users</p>
            </div>
          </Card.Body>
        </Card>
      </Col>
    </Row>
  </div>
);

const ChatSection = () => (
  <div className="chat-section">
    <h2 className="section-title">SBA Assistant</h2>
    <Card>
      <Card.Body>
        <p>Chat interface will be integrated here</p>
      </Card.Body>
    </Card>
  </div>
);

const DocumentsSection = () => (
  <div className="documents-section">
    <h2 className="section-title">Documents</h2>
    <Row>
      <Col lg={4} md={6} className="mb-3">
        <Card>
          <Card.Body>
            <Card.Title>Business Plan Template</Card.Title>
            <Card.Text>SBA-approved business plan template</Card.Text>
          </Card.Body>
        </Card>
      </Col>
      <Col lg={4} md={6} className="mb-3">
        <Card>
          <Card.Body>
            <Card.Title>Loan Application Guide</Card.Title>
            <Card.Text>Step-by-step loan application process</Card.Text>
          </Card.Body>
        </Card>
      </Col>
      <Col lg={4} md={6} className="mb-3">
        <Card>
          <Card.Body>
            <Card.Title>Grant Opportunities</Card.Title>
            <Card.Text>Current SBA grant programs</Card.Text>
          </Card.Body>
        </Card>
      </Col>
    </Row>
  </div>
);

const AnalyticsSection = () => (
  <div className="analytics-section">
    <h2 className="section-title">Analytics</h2>
    <Row>
      <Col lg={6} className="mb-4">
        <Card>
          <Card.Body>
            <Card.Title>Usage Analytics</Card.Title>
            <Card.Text>Analytics dashboard coming soon</Card.Text>
          </Card.Body>
        </Card>
      </Col>
      <Col lg={6} className="mb-4">
        <Card>
          <Card.Body>
            <Card.Title>Performance Metrics</Card.Title>
            <Card.Text>Performance tracking coming soon</Card.Text>
          </Card.Body>
        </Card>
      </Col>
    </Row>
  </div>
);

const ResourcesSection = () => (
  <div className="resources-section">
    <h2 className="section-title">SBA Resources</h2>
    <Row>
      <Col lg={4} className="mb-3">
        <Card>
          <Card.Body>
            <Card.Title>7(a) Loan Program</Card.Title>
            <Card.Text>Learn about SBA's primary loan program</Card.Text>
          </Card.Body>
        </Card>
      </Col>
      <Col lg={4} className="mb-3">
        <Card>
          <Card.Body>
            <Card.Title>Microloan Program</Card.Title>
            <Card.Text>Small loans up to $50,000</Card.Text>
          </Card.Body>
        </Card>
      </Col>
      <Col lg={4} className="mb-3">
        <Card>
          <Card.Body>
            <Card.Title>8(a) Business Development</Card.Title>
            <Card.Text>Support for disadvantaged businesses</Card.Text>
          </Card.Body>
        </Card>
      </Col>
    </Row>
  </div>
);

const SettingsSection = () => (
  <div className="settings-section">
    <h2 className="section-title">Settings</h2>
    <Card>
      <Card.Body>
        <h5>Application Settings</h5>
        <p>Configure your preferences and settings</p>
      </Card.Body>
    </Card>
  </div>
);

export default NewMainLayout;
