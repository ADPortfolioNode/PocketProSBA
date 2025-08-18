// Optimized connection manager for production startup
class ConnectionManager {
  constructor() {
    this.baseUrl = this.getBaseUrl();
    this.isConnected = false;
    this.retryCount = 0;
    this.maxRetries = 5;
    this.retryDelay = 1000;
    this.connectionStatus = {
      http: false,
      websocket: false,
      backend: null
    };
  }

  // Get base URL based on environment
  getBaseUrl() {
    if (process.env.REACT_APP_BACKEND_URL) {
      return process.env.REACT_APP_BACKEND_URL;
    }
    
    const hostname = window.location.hostname;
    
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:5000';
    }
    
    if (hostname.includes('onrender.com')) {
      return window.location.origin;
    }
    
    return window.location.origin;
  }

  // Optimized health check with multiple endpoints
  async checkHealth() {
    const endpoints = [
      '/api/health',
      '/health',
      '/api/status',
      '/ping'
    ];

    for (const endpoint of endpoints) {
      try {
        const url = `${this.baseUrl}${endpoint}`;
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        
        const response = await fetch(url, {
          method: 'GET',
          signal: controller.signal,
          headers: { 'Content-Type': 'application/json' }
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
          this.connectionStatus.http = true;
          this.connectionStatus.backend = url;
          return { success: true, endpoint: url, data: await response.json() };
        }
      } catch (error) {
        console.warn(`Health check failed for ${endpoint}:`, error.message);
        continue;
      }
    }
    
    this.connectionStatus.http = false;
    return { success: false, error: 'All health endpoints failed' };
  }

  // Optimized WebSocket connection with fallbacks
  async connectWebSocket() {
    const wsUrl = this.baseUrl.replace(/^http/, 'ws') + '/ws';
    
    return new Promise((resolve) => {
      try {
        const socket = new WebSocket(wsUrl);
        let resolved = false;

        const timeout = setTimeout(() => {
          if (!resolved) {
            socket.close();
            resolve({ success: false, error: 'WebSocket timeout' });
            resolved = true;
          }
        }, 10000);

        socket.onopen = () => {
          if (!resolved) {
            clearTimeout(timeout);
            this.connectionStatus.websocket = true;
            resolve({ success: true, socket });
            resolved = true;
          }
        };

        socket.onerror = (error) => {
          if (!resolved) {
            clearTimeout(timeout);
            console.warn('WebSocket error:', error);
            resolve({ success: false, error: 'WebSocket connection failed' });
            resolved = true;
          }
        };

        socket.onclose = (event) => {
          this.connectionStatus.websocket = false;
          if (!resolved) {
            clearTimeout(timeout);
            resolve({ success: false, error: 'WebSocket closed', code: event.code });
            resolved = true;
          }
        };

      } catch (error) {
        resolve({ success: false, error: 'WebSocket initialization failed' });
      }
    });
  }

  // Progressive connection establishment
  async establishConnection() {
    console.log('🔍 Starting connection establishment...');
    
    // Step 1: Check HTTP health
    const healthResult = await this.checkHealth();
    if (healthResult.success) {
      console.log('✅ HTTP connection established:', healthResult.endpoint);
      this.isConnected = true;
    } else {
      console.warn('⚠️ HTTP connection failed, continuing with degraded mode');
    }

    // Step 2: Attempt WebSocket (optional)
    const wsResult = await this.connectWebSocket();
    if (wsResult.success) {
      console.log('✅ WebSocket connection established');
    } else {
      console.log('💡 WebSocket unavailable, HTTP endpoints will be used');
    }

    return {
      http: healthResult.success,
      websocket: wsResult.success,
      backendUrl: this.baseUrl,
      status: this.connectionStatus
    };
  }

  // Get connection status
  getStatus() {
    return {
      isConnected: this.isConnected,
      baseUrl: this.baseUrl,
      ...this.connectionStatus
    };
  }
}

// Create singleton instance
const connectionManager = new ConnectionManager();

export default connectionManager;
