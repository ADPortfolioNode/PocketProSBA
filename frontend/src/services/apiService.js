// Universal API service for all environments
class ApiService {
  constructor() {
    this.baseUrl = this.getBaseUrl();
    this.isConnected = false;
    this.retryCount = 0;
    this.maxRetries = 3;
  }

  // Get base URL based on environment
  getBaseUrl() {
    // Check for environment variables first
    if (process.env.REACT_APP_BACKEND_URL) {
      return process.env.REACT_APP_BACKEND_URL;
    }
    
    if (process.env.REACT_APP_API_BASE) {
      return process.env.REACT_APP_API_BASE;
    }

    // Detect environment based on hostname
    const hostname = window.location.hostname;
    
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:5000';
    }
    
    // For Render.com and other production environments
    if (hostname.includes('onrender.com')) {
      // Use the same origin for backend when on Render
      return window.location.origin;
    }
    
    // Default fallback
    return window.location.origin;
  }

  // Build full API URL
  buildUrl(endpoint) {
    const baseUrl = this.baseUrl;
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    return `${baseUrl}${cleanEndpoint}`;
  }

  // Health check with retry
  async healthCheck() {
    const endpoints = [
      '/api/health',
      '/health',
      '/api/status'
    ];

    for (const endpoint of endpoints) {
      try {
        const url = this.buildUrl(endpoint);
        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          signal: AbortSignal.timeout(5000)
        });

        if (response.ok) {
          this.isConnected = true;
          return {
            connected: true,
            endpoint,
            url,
            data: await response.json()
          };
        }
      } catch (error) {
        console.warn(`Health check failed for ${endpoint}:`, error.message);
        continue;
      }
    }

    this.isConnected = false;
    return {
      connected: false,
      error: 'All health endpoints failed'
    };
  }

  // Generic API call with retry logic
  async apiCall(endpoint, options = {}, retries = this.maxRetries) {
    const url = this.buildUrl(endpoint);
    
    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        const response = await fetch(url, {
          ...options,
          headers: {
            'Content-Type': 'application/json',
            ...options.headers
          },
          signal: AbortSignal.timeout(30000)
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
      } catch (error) {
        if (attempt === retries) {
          throw error;
        }
        
        // Exponential backoff
        const delay = Math.pow(2, attempt - 1) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  // Chat API
  async sendChat(message, sessionId = 'default') {
    return this.apiCall('/api/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        session_id: sessionId
      })
    });
  }

  // Search API
  async searchDocuments(query, limit = 5) {
    return this.apiCall('/api/search', {
      method: 'POST',
      body: JSON.stringify({
        query,
        limit
      })
    });
  }

  // Get documents
  async getDocuments() {
    return this.apiCall('/api/documents');
  }

  // Get status
  async getStatus() {
    return this.apiCall('/api/status');
  }
}

// Create singleton instance
const apiService = new ApiService();

// Export for use in components
export default apiService;
