import apiClient, { BASE_URL } from '../api/apiClient';

// 15s — aggressive 5s polling hammered the backend during restarts
const CONNECTION_CHECK_INTERVAL = 15000;
let healthCheckIntervalId = null;
let connectionListeners = [];
let lastFailLogAt = 0;

/**
 * Health probe through apiClient, so it uses the same base URL as every other
 * call (REACT_APP_API_URL at build, ?backend_host=, or same-origin). No
 * hard-coded loopback-port fallbacks.
 */
async function probeHealth() {
  const response = await apiClient.get('/api/health', { timeout: 4000 }, { quiet: true, retry: false });
  const data = response?.data || { status: 'healthy' };
  return { connected: true, data, url: `${BASE_URL || ''}/api/health` };
}

const connectionService = {
  initialize: () => {
    // Start periodic health checks
    connectionService.startHealthMonitoring();
  },

  addConnectionListener: (listener) => {
    connectionListeners.push(listener);
    return () => {
      connectionListeners = connectionListeners.filter(l => l !== listener);
    };
  },

  notifyConnectionListeners: (status) => {
    connectionListeners.forEach(listener => listener(status));
  },

  startHealthMonitoring: () => {
    if (healthCheckIntervalId) {
      clearInterval(healthCheckIntervalId);
    }
    healthCheckIntervalId = setInterval(async () => {
      await connectionService.checkConnection();
    }, CONNECTION_CHECK_INTERVAL);
  },

  stopHealthMonitoring: () => {
    if (healthCheckIntervalId) {
      clearInterval(healthCheckIntervalId);
      healthCheckIntervalId = null;
    }
  },

  checkConnection: async () => {
    try {
      // Lightweight /api/health probe first, /api/info as a fallback
      let info = null;
      try {
        const probed = await probeHealth();
        info = probed.data || { status: 'healthy', server: { self: probed.url } };
        const status = { connected: true, info, data: info, error: null };
        connectionService.notifyConnectionListeners(status);
        return status;
      } catch (probeErr) {
        // Fallback to apiClient
        const response = await apiClient.get('/api/info', { timeout: 5000 }, { quiet: true });
        info = response.data;
        const status = {
          connected: response.status === 200,
          info,
          data: info,
          error: null,
        };
        connectionService.notifyConnectionListeners(status);
        return status;
      }
    } catch (error) {
      // Rate-limit console noise (prebuilt logs every failure)
      const now = Date.now();
      if (now - lastFailLogAt > 15000) {
        console.warn('Connection check failed (will retry):', error?.message || error);
        lastFailLogAt = now;
      }
      const status = {
        connected: false,
        info: null,
        data: null,
        error: error.message || 'Network Error',
      };
      connectionService.notifyConnectionListeners(status);
      return status;
    }
  },

  apiCall: async (url, options = {}) => {
    try {
      const response = await apiClient({
        url,
        method: options.method || 'GET',
        data: options.body ? JSON.parse(options.body) : undefined,
        headers: options.headers,
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  getDiagnostics: async () => {
    try {
      const response = await apiClient.get('/api/diagnostics', { skipAuthRedirect: true }, { quiet: true, retry: false });
      return response.data;
    } catch (error) {
      // Diagnostics need a signed-in user; a 401 is expected when signed out.
      if (error?.response?.status === 401) return { unauthorized: true };
      console.error('Error fetching diagnostics:', error);
      return { error: error.message || 'Failed to fetch diagnostics' };
    }
  },

  resetConnection: async () => {
    // This might involve clearing local storage, re-initializing services, etc.
    // For now, just re-run health check
    await connectionService.checkConnection();
  },
};

export default connectionService;
