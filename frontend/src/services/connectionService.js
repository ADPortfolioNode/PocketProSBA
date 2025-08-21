import apiClient from '../api/apiClient';

const CONNECTION_CHECK_INTERVAL = 5000; // 5 seconds
let healthCheckIntervalId = null;
let connectionListeners = [];

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
      const response = await apiClient.get('/api/info');
      const status = {
        connected: response.status === 200,
        info: response.data,
        error: null,
      };
      connectionService.notifyConnectionListeners(status);
      return status;
    } catch (error) {
      const status = {
        connected: false,
        info: null,
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
      const response = await apiClient.get('/api/diagnostics'); // Assuming a diagnostics endpoint
      return response.data;
    } catch (error) {
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
