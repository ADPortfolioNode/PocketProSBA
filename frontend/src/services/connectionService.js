import apiClient from '../api/apiClient';

// 15s — aggressive 5s polling hammered the backend during restarts
const CONNECTION_CHECK_INTERVAL = 15000;
let healthCheckIntervalId = null;
let connectionListeners = [];
let lastFailLogAt = 0;

/** Prefer same-origin nginx proxy, then IPv4 backend (avoids Windows localhost→IPv6 flakes). */
async function probeHealth() {
  const candidates = [];
  if (typeof window !== 'undefined' && window.location?.origin) {
    // When UI is on :3000, /api/* is proxied by nginx → backend
    candidates.push(`${window.location.origin}/api/health`);
  }
  candidates.push('http://127.0.0.1:5000/api/health');
  candidates.push('http://127.0.0.1:5000/api/api/health');
  candidates.push('http://localhost:5000/api/health');

  let lastError = null;
  for (const url of candidates) {
    try {
      const controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
      const timer = controller ? setTimeout(() => controller.abort(), 4000) : null;
      const res = await fetch(url, {
        method: 'GET',
        headers: { Accept: 'application/json' },
        signal: controller?.signal,
        cache: 'no-store',
      });
      if (timer) clearTimeout(timer);
      if (!res.ok) {
        lastError = new Error(`HTTP ${res.status} from ${url}`);
        continue;
      }
      const data = await res.json().catch(() => ({ status: 'healthy' }));
      return { connected: true, data, url };
    } catch (e) {
      lastError = e;
    }
  }
  throw lastError || new Error('All health probes failed');
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
      // Prefer lightweight multi-URL probe (IPv4 + same-origin proxy)
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
