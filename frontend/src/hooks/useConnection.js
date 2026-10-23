import { useState, useEffect, useCallback, useRef } from 'react';
import apiClient from '../api/apiClient';
import { friendlyError } from '../utils/friendlyError';

const CONNECTION_CHECK_INTERVAL = 5000; // 5 seconds

/**
 * Backend connection state.
 *
 * status: 'checking' until the first check settles (apiClient retries transient
 * failures for ~15-20s first), then 'online' or 'offline'. Background re-checks
 * keep the last known status, so the UI never flips to an error while a check
 * is merely in flight. backendError holds friendly copy, never raw exception text.
 */
export const useConnection = () => {
  const [status, setStatus] = useState('checking');
  const [serverConnected, setServerConnected] = useState(false);
  const [backendError, setBackendError] = useState(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);
  const [connectionInfo, setConnectionInfo] = useState(null);
  const inFlight = useRef(null);

  const checkConnection = useCallback(async ({ userInitiated = false } = {}) => {
    // One check at a time: a slow check plus the interval must not stack requests.
    if (inFlight.current) return inFlight.current;
    setIsCheckingHealth(true);
    // A user-pressed Retry goes back to the loading state; background polls don't.
    if (userInitiated) setStatus('checking');

    const run = (async () => {
      try {
        const response = await apiClient.get('/api/info', {}, { quiet: true });
        const connected = !!response?.data && response.data.status === 'operational';
        setServerConnected(connected);
        setConnectionInfo(response.data);
        setStatus(connected ? 'online' : 'offline');
        setBackendError(connected ? null : 'PocketPro is up but not ready yet. Please try again in a moment.');
        return { connected, info: response.data, error: null };
      } catch (error) {
        const message = friendlyError(error);
        setServerConnected(false);
        setConnectionInfo(null);
        setStatus('offline');
        setBackendError(message);
        return { connected: false, info: null, error: message };
      } finally {
        setIsCheckingHealth(false);
        inFlight.current = null;
      }
    })();
    inFlight.current = run;
    return run;
  }, []);

  const apiCall = useCallback(async (url, options = {}) => {
    try {
      const method = (options.method || 'GET').toUpperCase();
      const data = options.body ? (typeof options.body === 'string' ? JSON.parse(options.body) : options.body) : undefined;
      let response;

      if (method === 'POST') {
        response = await apiClient.post(url, data, { headers: options.headers });
      } else if (method === 'PUT') {
        response = await apiClient.put(url, data, { headers: options.headers });
      } else if (method === 'DELETE') {
        response = await apiClient.delete(url, { headers: options.headers });
      } else {
        response = await apiClient.get(url, { headers: options.headers });
      }

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
      return { error: friendlyError(error) };
    }
  }, []);

  const resetConnection = useCallback(async () => {
    await checkConnection({ userInitiated: true });
  }, [checkConnection]);

  const retryConnection = useCallback(() => checkConnection({ userInitiated: true }), [checkConnection]);

  useEffect(() => {
    checkConnection();
    const healthCheckIntervalId = setInterval(checkConnection, CONNECTION_CHECK_INTERVAL);
    return () => clearInterval(healthCheckIntervalId);
  }, [checkConnection]);

  return {
    status,
    serverConnected,
    backendError,
    isCheckingHealth,
    connectionInfo,
    checkConnection,
    retryConnection,
    apiCall,
    getDiagnostics,
    resetConnection,
  };
};
