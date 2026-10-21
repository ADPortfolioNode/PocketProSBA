import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
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
  const fetchSystemStatus = useCallback(async () => {
    try {
      const [flaskResp, chromaResp] = await Promise.all([
        apiClient.get('/api/health', {}, { quiet: true }).catch(() => ({ data: { status: 'error', message: 'Flask server unreachable' } })),
        apiClient.get('/api/chromadb_health', {}, { quiet: true }).catch(() => ({ data: { status: 'error', message: 'ChromaDB unreachable' } }))
      ]);

      setSystemStatus({
        flask: {
          status: ['ok', 'healthy'].includes(flaskResp?.data?.status) ? 'online' : 'error',
          message: flaskResp?.data?.message || ''
        },
        chromadb: {
          status: chromaResp?.data?.status === 'ok' ? 'online' : 'error',
          message: chromaResp?.data?.message || ''
        }
      });
    } catch (err) {
      console.error('Error fetching system status:', err);
    }
  }, []);

  // The helpers below are memoized so their identity is stable across renders.
  // Before, a new function on every render re-fired any effect that depended on
  // them (e.g. useEffect(() => handleError(...), [handleError]) loops after clearError).

  // Global error handler
  const handleError = useCallback((err, context = '') => {
    console.error(`Error in ${context}:`, err);
    setError(err?.message || 'An unexpected error occurred');
  }, []);

  // Clear error
  const clearError = useCallback(() => setError(null), []);

  // Global loading state
  const setGlobalLoading = useCallback((isLoading) => setLoading(isLoading), []);

  useEffect(() => {
    fetchSystemStatus();
    const intervalId = setInterval(fetchSystemStatus, 30000);
    return () => clearInterval(intervalId);
  }, [fetchSystemStatus]);

  const value = useMemo(() => ({
    loading,
    error,
    systemStatus,
    setGlobalLoading,
    handleError,
    clearError,
    fetchSystemStatus
  }), [loading, error, systemStatus, setGlobalLoading, handleError, clearError, fetchSystemStatus]);

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};
