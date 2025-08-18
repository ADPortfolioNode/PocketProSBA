// Environment configuration utility
class EnvironmentConfig {
  constructor() {
    this.environment = this.detectEnvironment();
    this.config = this.getConfig();
  }

  // Detect current environment
  detectEnvironment() {
    const hostname = window.location.hostname;
    return hostname.includes('onrender.com') ? 'render' : 'development';
  }

  // Get configuration for current environment
  getConfig() {
    return {
      backendUrl: process.env.REACT_APP_BACKEND_URL || 'https://pocketprosba-backend.onrender.com',
      wsUrl: 'wss://pocketprosba-backend.onrender.com',
      healthEndpoint: 'https://pocketprosba-backend.onrender.com/api/health',
      corsEnabled: true,
      debug: false
    };
  }

  // Get API endpoints
  getApiEndpoints() {
    return {
      chat: 'https://pocketprosba-backend.onrender.com/api/chat',
      health: 'https://pocketprosba-backend.onrender.com/api/health',
      status: 'https://pocketprosba-backend.onrender.com/api/status',
      documents: 'https://pocketprosba-backend.onrender.com/api/documents',
      search: 'https://pocketprosba-backend.onrender.com/api/search'
    };
  }

  // Get WebSocket URL
  getWebSocketUrl() {
    return 'wss://pocketprosba-backend.onrender.com';
  }

  // Get health check URL
  getHealthCheckUrl() {
    return 'https://pocketprosba-backend.onrender.com/api/health';
  }
}

// Create singleton instance
const environmentConfig = new EnvironmentConfig();

// Export for use in components
export default environmentConfig;
