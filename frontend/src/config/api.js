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
    
    // Check for specific environment variables first
    if (process.env.REACT_APP_BACKEND_URL) {
      return process.env.REACT_APP_BACKEND_URL;
    }
    
    // Render deployment - use same origin
    if (env === 'render') {
      return window.location.origin;
    }
    
    // Production deployment
    if (env === 'production') {
      return window.location.origin;
    }
    
    // Development - check for Docker
    const isDocker = window.location.hostname === 'localhost' && window.location.port === '3000';
    if (isDocker) {
      return 'http://localhost:5000';
    }
    
    // Local development
    return 'http://localhost:5000';
  },

  // Health check endpoints
  healthEndpoints: [
    '/health',
    '/api/health',
    '/api/status',
    '/ping',
    '/api/info'
  ],

  // Connection timeout settings
  timeouts: {
    healthCheck: 8000,
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
  
  // Handle relative URLs
  if (endpoint.startsWith('http')) {
    return endpoint;
  }
  
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = new URL(cleanEndpoint, baseUrl);
  
  // Add query parameters if provided
  if (options.params) {
    Object.keys(options.params).forEach(key => {
      url.searchParams.append(key, options.params[key]);
    });
  }
  
  return url.toString();
};

// Connection status checker with better error handling
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

// Retry wrapper for API calls with improved error handling
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
