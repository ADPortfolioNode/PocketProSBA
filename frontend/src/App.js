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
    const wsUrl = process.env.REACT_APP_BACKEND_WS_URL || 'ws://localhost:10000/ws';
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log('WebSocket connection established to', wsUrl);
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    socket.onclose = (event) => {
      console.log('WebSocket connection closed:', event);
    };

    // Cleanup on unmount
    return () => {
      socket.close();
    };
  }, []);

  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        {/* React Router v7 requires relative splat path syntax */}
        {/* Change "/*" to "*", or use relative paths as per https://reactrouter.com/en/main/upgrading/v6#v7_relativesplatpath */}
        {/* So update to: */}
        <Route path="*" element={<MainLayout />} />
        <Route path="/" element={<Navigate to="/chat" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
