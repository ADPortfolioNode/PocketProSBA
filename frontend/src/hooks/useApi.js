import { useState, useCallback } from 'react';
import apiClient from '../api/apiClient';

export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const callApi = useCallback(async (method, url, payload = null) => {
    setLoading(true);
    setError(null);
    
    try {
      let response;
      switch (method.toLowerCase()) {
        case 'get':
          response = await apiClient.get(url);
          break;
        case 'post':
          response = await apiClient.post(url, payload);
          break;
        case 'put':
          response = await apiClient.put(url, payload);
          break;
        case 'delete':
          response = await apiClient.delete(url);
          break;
        default:
          throw new Error(`Unsupported HTTP method: ${method}`);
      }
      
      setData(response.data);
      return response.data;
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message || 'An error occurred';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setLoading(false);
    setError(null);
    setData(null);
  }, []);

  return {
    loading,
    error,
    data,
    callApi,
    reset,
  };
};
