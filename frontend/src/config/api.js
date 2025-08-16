// Comprehensive backend connectivity configuration
// Supports multiple environments: local, docker, render, production

const API_CONFIG = {
  // Environment detection
  getEnvironment: () => {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'development';
    } else if (hostname.includes('onrender.com')) {
      return 'render';
    } else if (hostname.includes('herokuapp.com')) {
      return 'heroku';
    } else if (protocol === 'https:') {
      return 'production';
    }
    return 'development';
  },

  // Backend URL resolution with fallbacks
  getBackendUrl: () => {
    const env = API_CONFIG.getEnvironment();
    
    // Priority order for backend URL resolution
    const urlSources = [
      // 1. Environment variable (highest priority)
      process.env.REACT_APP_BACKEND_URL,
      
      // 2. Render-specific
      env === 'render' ? process.env.REACT_APP_RENDER_BACKEND_URL : null,
      
      // 3. Docker-specific
      env === 'development' && process.env.REACT_APP_DOCKER_BACKEND_URL,
      
      // 4. Default ports by environment
      env === 'development' ? 'http://localhost:5000' : null,
      env === 'development' ? 'http://localhost:5001' : null,
      
      // 5. Production defaults
      env === 'production' ? '/api' : null,
      
      // 6. Render default
      env === 'render' ? window.location.origin : null
    ].filter(Boolean);

    // Return first valid URL
    return urlSources[0] || 'http://localhost:5000';
  },

  // Health check endpoints
  healthEndpoints: [
    '/health',
    '/api/health',
    '/api/status',
    '/ping'
  ],

  // Connection timeout settings
  timeouts: {
    healthCheck: 5000,
    apiCall: 30000,
    retryDelay: 2000,
    maxRetries: 3
  },

  // Retry configuration
  retryConfig: {
    maxRetries: 3,
    retryDelay: 1000,
    backoffMultiplier: 2
  }
};

// Enhanced API URL builder with redundancy
export const buildApiUrl = (endpoint, options = {}) => {
  const baseUrl = API_CONFIG.getBackendUrl();
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  
  // Handle different URL formats
  const url = new URL(cleanEndpoint, baseUrl);
  
  // Add query parameters if provided
  if (options.params) {
    Object.keys(options.params).forEach(key => {
      url.searchParams.append(key, options.params[key]);
    });
  }
  
  return url.toString();
};

// Connection status checker
export const checkBackendConnection = async (customEndpoints = []) => {
  const endpoints = [...API_CONFIG.healthEndpoints, ...customEndpoints];
  const timeout = API_CONFIG.timeouts.healthCheck;
  
  for (const endpoint of endpoints) {
    try {
      const url = buildApiUrl(endpoint);
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);
      
      const response = await fetch(url, {
        method: 'GET',
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const data = await response.json();
        return {
          connected: true,
          endpoint,
          data,
          responseTime: Date.now()
        };
      }
    } catch (error) {
      console.warn(`Health check failed for ${endpoint}:`, error.message);
      continue;
    }
  }
  
  return {
    connected: false,
    error: 'All health endpoints failed',
    endpoints: endpoints
  };
};

// Retry wrapper for API calls
export const apiCallWithRetry = async (url, options = {}, retries = API_CONFIG.retryConfig.maxRetries) => {
  let lastError;
  
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const response = await fetch(url, {
        ...options,
        signal: AbortSignal.timeout(API_CONFIG.timeouts.apiCall)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      lastError = error;
      
      if (attempt < retries) {
        const delay = API_CONFIG.retryConfig.retryDelay * Math.pow(
          API_CONFIG.retryConfig.backoffMultiplier, 
          attempt - 1
        );
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  
  throw lastError;
};

// Export configuration for use in components
export default API_CONFIG;
