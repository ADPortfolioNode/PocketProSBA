import { buildApiUrl, checkBackendConnection, apiCallWithRetry } from '../config/api';

/**
 * Comprehensive connection service for frontend-backend communication
 * Handles all connectivity scenarios with redundancy and fallback mechanisms
 */
class ConnectionService {
  constructor() {
    this.isConnected = false;
    this.backendInfo = null;
    this.connectionHistory = [];
    this.healthCheckInterval = null;
    this.listeners = new Set();
  }

  // Initialize connection monitoring
  async initialize() {
    await this.checkConnection();
    this.startHealthMonitoring();
  }

  // Check connection with multiple fallback strategies
  async checkConnection(customEndpoints = []) {
    try {
      // Strategy 1: Direct health check
      const result = await checkBackendConnection(customEndpoints);
      
      if (result.connected) {
        this.updateConnectionStatus(true, result.data);
        return result;
      }

      // Strategy 2: Try alternative ports
      const altPorts = [5000, 5001, 8080, 8000, 3001];
      for (const port of altPorts) {
        try {
          const altUrl = `http://localhost:${port}`;
          const response = await fetch(`${altUrl}/health`, {
            method: 'GET',
            signal: AbortSignal.timeout(3000)
          });
          
          if (response.ok) {
            // Update backend URL for this session
            sessionStorage.setItem('backendUrl', altUrl);
            this.updateConnectionStatus(true, { port });
            return { connected: true, port };
          }
        } catch (e) {
          continue;
        }
      }

      // Strategy 3: Check if running in Docker
      try {
        const dockerResponse = await fetch('/api/health', {
          method: 'GET',
          signal: AbortSignal.timeout(5000)
        });
        
        if (dockerResponse.ok) {
          this.updateConnectionStatus(true, { source: 'docker-proxy' });
          return { connected: true, source: 'docker-proxy' };
        }
      } catch (e) {
        // Continue to next strategy
      }

      // Strategy 4: Render deployment check
      if (window.location.hostname.includes('onrender.com')) {
        try {
          const renderResponse = await fetch('/api/health', {
            method: 'GET',
            signal: AbortSignal.timeout(10000)
          });
          
          if (renderResponse.ok) {
            this.updateConnectionStatus(true, { source: 'render' });
            return { connected: true, source: 'render' };
          }
        } catch (e) {
          // Continue
        }
      }

      // All strategies failed
      this.updateConnectionStatus(false, null, 'All connection strategies failed');
      return { connected: false, error: 'All connection strategies failed' };

    } catch (error) {
      this.updateConnectionStatus(false, null, error.message);
      return { connected: false, error: error.message };
    }
  }

  // Start continuous health monitoring
  startHealthMonitoring(interval = 30000) {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
    }

    this.healthCheckInterval = setInterval(async () => {
      await this.checkConnection();
    }, interval);
  }

  // Stop health monitoring
  stopHealthMonitoring() {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
    }
  }

  // Update connection status and notify listeners
  updateConnectionStatus(connected, info = null, error = null) {
    const wasConnected = this.isConnected;
    this.isConnected = connected;
    this.backendInfo = info;

    // Log connection history
    this.connectionHistory.push({
      timestamp: new Date().toISOString(),
      connected,
      info,
      error
    });

    // Keep only last 50 entries
    if (this.connectionHistory.length > 50) {
      this.connectionHistory = this.connectionHistory.slice(-50);
    }

    // Notify all listeners
    this.listeners.forEach(listener => {
      listener({
        connected,
        info,
        error,
        wasConnected,
        timestamp: new Date()
      });
    });
  }

  // Add connection status listener
  addConnectionListener(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  // Get current connection status
  getConnectionStatus() {
    return {
      connected: this.isConnected,
      info: this.backendInfo,
      history: this.connectionHistory
    };
  }

  // Make API call with automatic retry and fallback
  async apiCall(endpoint, options = {}) {
    const url = buildApiUrl(endpoint);
    
    try {
      return await apiCallWithRetry(url, options);
    } catch (error) {
      // If call fails, try to reconnect
      const connectionResult = await this.checkConnection();
      
      if (connectionResult.connected) {
        // Retry the call with new connection
        return await apiCallWithRetry(buildApiUrl(endpoint), options);
      }
      
      throw error;
    }
  }

  // Get connection diagnostics
  async getDiagnostics() {
    const diagnostics = {
      timestamp: new Date().toISOString(),
      environment: {
        hostname: window.location.hostname,
        protocol: window.location.protocol,
        port: window.location.port,
        userAgent: navigator.userAgent
      },
      backend: {
        configuredUrl: buildApiUrl(''),
        sessionUrl: sessionStorage.getItem('backendUrl') || 'not set',
        connected: this.isConnected,
        info: this.backendInfo
      },
      network: {
        online: navigator.onLine,
        connection: navigator.connection ? {
          effectiveType: navigator.connection.effectiveType,
          downlink: navigator.connection.downlink,
          rtt: navigator.connection.rtt
        } : null
      },
      history: this.connectionHistory.slice(-10)
    };

    return diagnostics;
  }

  // Reset connection and clear cache
  async resetConnection() {
    sessionStorage.removeItem('backendUrl');
    this.connectionHistory = [];
    this.backendInfo = null;
    await this.checkConnection();
  }
}

// Create singleton instance
const connectionService = new ConnectionService();

// Export for use in components
export default connectionService;

// React hook for connection status
export const useConnectionStatus = () => {
  const [status, setStatus] = React.useState(connectionService.getConnectionStatus());

  React.useEffect(() => {
    const unsubscribe = connectionService.addConnectionListener(setStatus);
    return unsubscribe;
  }, []);

  return status;
};
