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

export default apiClient;
