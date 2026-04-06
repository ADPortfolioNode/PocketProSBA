import React, { createContext, useContext, useState, useEffect } from 'react';
import apiClient from '../api/apiClient';

const AppContext = createContext();

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

export const AppProvider = ({ children }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [systemStatus, setSystemStatus] = useState({
    flask: { status: 'unknown', message: '' },
    chromadb: { status: 'unknown', message: '' }
  });

  // Fetch system status
  const fetchSystemStatus = async () => {
    try {
      const [flaskResp, chromaResp] = await Promise.all([
        apiClient.get('/api/health', {}, { quiet: true }).catch(() => ({ data: { status: 'error', message: 'Flask server unreachable' } })),
        apiClient.get('/api/chromadb_health', {}, { quiet: true }).catch(() => ({ data: { status: 'error', message: 'ChromaDB unreachable' } }))
      ]);

      setSystemStatus({
        flask: {
          status: ['ok', 'healthy'].includes(flaskResp.data?.status) ? 'online' : 'error',
          message: flaskResp.data?.message || ''
        },
        chromadb: {
          status: chromaResp.data?.status === 'ok' ? 'online' : 'error',
          message: chromaResp.data?.message || ''
        }
      });
    } catch (err) {
      console.error('Error fetching system status:', err);
    }
  };

  // Global error handler
  const handleError = (error, context = '') => {
    console.error(`Error in ${context}:`, error);
    setError(error.message || 'An unexpected error occurred');
  };

  // Clear error
  const clearError = () => setError(null);

  // Global loading state
  const setGlobalLoading = (isLoading) => setLoading(isLoading);

  useEffect(() => {
    fetchSystemStatus();
    const intervalId = setInterval(fetchSystemStatus, 30000);
    return () => clearInterval(intervalId);
  }, []);

  const value = {
    loading,
    error,
    systemStatus,
    setGlobalLoading,
    handleError,
    clearError,
    fetchSystemStatus
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};
