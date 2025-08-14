import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';
import Login from './Login';
import Register from './Register';
import ForgotPassword from './ForgotPassword';
import MainLayout from './components/MainLayout';

function App() {
  useEffect(() => {
    // WebSocket connection is optional - don't let it break the app
    const wsUrl = process.env.REACT_APP_BACKEND_WS_URL || 'ws://localhost:10000/ws';
    
    try {
      const socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        console.log('WebSocket connection established to', wsUrl);
      };

      socket.onerror = (error) => {
        console.warn('WebSocket connection error (non-critical):', error);
        console.log('Note: WebSocket is optional. HTTP endpoints will still work.');
      };

      socket.onclose = (event) => {
        console.log('WebSocket connection closed:', event);
        if (!event.wasClean) {
          console.log('WebSocket disconnected unexpectedly, but HTTP endpoints remain available');
        }
      };

      // Cleanup on unmount
      return () => {
        if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
          socket.close();
        }
      };
    } catch (error) {
      console.warn('WebSocket initialization failed:', error);
      console.log('Application will continue to work with HTTP endpoints only');
    }
  }, []);

  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="*" element={<MainLayout />} />
        <Route path="/" element={<Navigate to="/chat" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
