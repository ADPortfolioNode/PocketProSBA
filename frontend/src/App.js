import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';
import Login from './Login';
import Register from './Register';
import ForgotPassword from './ForgotPassword';
import MainLayout from './components/MainLayout';
import connectionManager from './services/connectionManager';

function App() {
  const [connectionStatus, setConnectionStatus] = useState({
    loading: true,
    connected: false,
    backendUrl: null,
    websocket: false
  });

  useEffect(() => {
    // Optimized startup sequence
    const initializeConnection = async () => {
      console.log('🚀 Initializing application connection...');
      
      try {
        const status = await connectionManager.establishConnection();
        
        setConnectionStatus({
          loading: false,
          connected: status.http,
          backendUrl: status.backendUrl,
          websocket: status.websocket
        });

        if (status.http) {
          console.log('✅ Application ready for full RAG operations');
        } else {
          console.warn('⚠️ Application running in degraded mode');
        }
      } catch (error) {
        console.error('❌ Connection initialization failed:', error);
        setConnectionStatus({
          loading: false,
          connected: false,
          backendUrl: null,
          websocket: false
        });
      }
    };

    initializeConnection();
  }, []);

  // Connection status indicator
  const ConnectionStatus = () => {
    if (connectionStatus.loading) {
      return (
        <div style={{ 
          position: 'fixed', 
          top: 0, 
          left: 0, 
          right: 0, 
          background: '#f0f0f0', 
          padding: '10px', 
          textAlign: 'center',
          zIndex: 9999
        }}>
          🔍 Establishing connection...
        </div>
      );
    }

    if (!connectionStatus.connected) {
      return (
        <div style={{ 
          position: 'fixed', 
          top: 0, 
          left: 0, 
          right: 0, 
          background: '#ffebee', 
          padding: '10px', 
          textAlign: 'center',
          zIndex: 9999
        }}>
          ⚠️ Connection issues detected. Using fallback mode.
        </div>
      );
    }

    return null;
  };

  return (
    <>
      <ConnectionStatus />
      <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="*" element={<MainLayout connectionStatus={connectionStatus} />} />
          <Route path="/" element={<Navigate to="/chat" replace />} />
        </Routes>
      </Router>
    </>
  );
}

export default App;
