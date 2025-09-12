import axios from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

const axiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Create the request handler
const makeRequest = async (method, endpoint, data = null, retries = MAX_RETRIES) => {
  try {
    console.log('Making request to:', endpoint);
    const config = {
      method,
      url: endpoint,
      data: data || undefined
    };
    const response = await axiosInstance(config);
    return response.data;
  } catch (error) {
    console.error('API Error:', error);
    if (retries > 0 && (error.code === 'ECONNREFUSED' || error.code === 'ECONNRESET')) {
      console.log(`Retrying... (${retries} attempts left)`);
      await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
      return makeRequest(method, endpoint, data, retries - 1);
    }
    throw error;
  }
};

// Define the endpoints
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

// Create the API methods
const get = (endpoint) => makeRequest('GET', endpoint);
const post = (endpoint, data) => makeRequest('POST', endpoint, data);
const put = (endpoint, data) => makeRequest('PUT', endpoint, data);
const delete_ = (endpoint) => makeRequest('DELETE', endpoint);

// Helper function to load endpoints (used in tests)
const loadEndpoints = async () => ({
  endpoints: endpointRegistry,
  baseURL: axiosInstance.defaults.baseURL,
  timestamp: new Date().toISOString()
});

// Export a consistent API object
const api = {
  get,
  post,
  put,
  delete: delete_,
  makeRequest,
  loadEndpoints,
  endpoints: endpointRegistry
};

export default api;
