import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';
import Login from './Login';
import Register from './Register';
import ForgotPassword from './ForgotPassword';
import MainLayout from './components/MainLayout';
import { AppProvider } from './context/AppProvider';
import ErrorBoundary from './components/ErrorBoundary';

function App() {
  return (
    // Last-resort catch: any render error shows the friendly card + Reload
    // instead of a blank page. MainLayout adds a per-tab boundary inside.
    <ErrorBoundary className="pp-error-boundary--app">
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
    </ErrorBoundary>
  );
}

export default App;
