import axios from 'axios';

const getBackendHost = () => {
  const envHost = process.env.REACT_APP_API_URL || process.env.REACT_APP_BACKEND_URL;

  const normalizeHost = (host) => {
    if (!host) return host;
    return host.replace(/\/api\/?$/, '').replace(/\/+$/, '');
  };

  if (typeof window === 'undefined') {
    return normalizeHost(envHost) || 'http://localhost:5000';
  }

  const params = new URLSearchParams(window.location.search);
  const backendHost = params.get('backend_host') || params.get('backendUrl') || params.get('api_host');
  if (backendHost) {
    return normalizeHost(backendHost);
  }

  if (envHost) {
    return normalizeHost(envHost);
  }

  const { protocol, hostname, port } = window.location;
  return `${protocol}//${hostname}${port ? `:${port}` : ''}`;
};

const BASE_URL = getBackendHost();
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
const makeRequest = async (method, endpoint, data = null, config = {}, retries = MAX_RETRIES, options = {}) => {
  const { quiet = false } = options;

  try {
    console.log('Making request to:', endpoint);
    const requestConfig = {
      method,
      url: endpoint,
      ...config
    };

    if (data !== null) {
      requestConfig.data = data;
    }

    const response = await axiosInstance(requestConfig);
    return response;
  } catch (error) {
    if (!quiet) {
      console.error('API Error:', error);
    }
    if (retries > 0 && (error.code === 'ECONNREFUSED' || error.code === 'ECONNRESET')) {
      if (!quiet) {
        console.log(`Retrying... (${retries} attempts left)`);
      }
      await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
      return makeRequest(method, endpoint, data, config, retries - 1, options);
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
const get = (endpoint, config = {}, options = {}) => makeRequest('GET', endpoint, null, config, MAX_RETRIES, options);
const post = (endpoint, data, config = {}, options = {}) => makeRequest('POST', endpoint, data, config, MAX_RETRIES, options);
const put = (endpoint, data, config = {}, options = {}) => makeRequest('PUT', endpoint, data, config, MAX_RETRIES, options);
const delete_ = (endpoint, config = {}, options = {}) => makeRequest('DELETE', endpoint, null, config, MAX_RETRIES, options);

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
