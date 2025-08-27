import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a response interceptor
apiClient.interceptors.response.use(
  response => response,
  error => {
    // Handle errors globally
    console.error('API Error:', error.response ? error.response.data : error.message);
    return Promise.reject(error);
  }
);

// Add a request interceptor
apiClient.interceptors.request.use(
  config => {
    // You can add any custom headers or logging here
    console.log('Making request to:', config.url);
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Endpoint registry
const endpointRegistry = {
  api_health: '/api/health',
  api_info: '/api/info',
  api_decompose: '/api/decompose',
  api_execute: '/api/execute',
  api_validate: '/api/validate',
  api_query: '/api/query',
  api_chat: '/api/chat',
  api_diagnostics: '/api/diagnostics'
};

// Function to load endpoints (used in tests)
export const loadEndpoints = async () => {
  return {
    endpoints: endpointRegistry,
    baseURL: apiClient.defaults.baseURL,
    timestamp: new Date().toISOString()
  };
};

export default apiClient;
