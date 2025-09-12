import { useState, useEffect, useCallback } from 'react';
import apiClient from '../api/apiClient';

const CONNECTION_CHECK_INTERVAL = 5000; // 5 seconds

export const useConnection = () => {
  const [serverConnected, setServerConnected] = useState(false);
  const [backendError, setBackendError] = useState(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);
  const [connectionInfo, setConnectionInfo] = useState(null);

  const checkConnection = useCallback(async () => {
    setIsCheckingHealth(true);
    setBackendError(null);
    try {
      const response = await apiClient.get('/api/info');
      const connected = response.status === 200;
      setServerConnected(connected);
      setConnectionInfo(response.data);
      if (!connected) {
        setBackendError('Unable to connect to backend server');
      }
      return { connected, info: response.data, error: null };
    } catch (error) {
      setServerConnected(false);
      setConnectionInfo(null);
      setBackendError(error.message || 'Connection failed');
      return { connected: false, info: null, error: error.message || 'Connection failed' };
    } finally {
      setIsCheckingHealth(false);
    }
  }, []);

  const apiCall = useCallback(async (url, options = {}) => {
    try {
      const response = await apiClient({
        url,
        method: options.method || 'GET',
        data: options.body ? (typeof options.body === 'string' ? JSON.parse(options.body) : options.body) : undefined,
        headers: options.headers,
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  }, []);

  const getDiagnostics = useCallback(async () => {
    try {
      const response = await apiClient.get('/api/diagnostics');
      return response.data;
    } catch (error) {
      console.error('Error fetching diagnostics:', error);
      return { error: error.message || 'Failed to fetch diagnostics' };
    }
  }, []);

  const resetConnection = useCallback(async () => {
    await checkConnection();
  }, [checkConnection]);

  useEffect(() => {
    checkConnection();
    const healthCheckIntervalId = setInterval(checkConnection, CONNECTION_CHECK_INTERVAL);
    return () => clearInterval(healthCheckIntervalId);
  }, [checkConnection]);

  return {
    serverConnected,
    backendError,
    isCheckingHealth,
    connectionInfo,
    checkConnection,
    apiCall,
    getDiagnostics,
    resetConnection,
  };
};
