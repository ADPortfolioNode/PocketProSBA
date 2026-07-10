import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';
import Login from './Login';
import Register from './Register';
import ForgotPassword from './ForgotPassword';
import MainLayout from './components/MainLayout';
import { AppProvider } from './context/AppProvider';

function App() {
  return (
    <AppProvider>
      <div className="pp-app">
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            {/* Home + app tabs share one minimal shell (MainLayout) */}
            <Route path="/*" element={<MainLayout />} />
          </Routes>
        </Router>
      </div>
    </AppProvider>
  );
}

export default App;
