import { useState, useCallback } from 'react';
import apiClient from '../api/apiClient';
import { useApp } from '../context/AppProvider';

export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { setGlobalLoading, handleError } = useApp();

  const executeRequest = useCallback(async (method, url, data = null, config = {}) => {
    setLoading(true);
    setError(null);
    setGlobalLoading(true);

    try {
      const response = await apiClient[method](url, data, config);
      return response.data;
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message || 'Request failed';
      setError(errorMessage);
      handleError(err, `API ${method.toUpperCase()} ${url}`);
      throw err;
    } finally {
      setLoading(false);
      setGlobalLoading(false);
    }
  }, [setGlobalLoading, handleError]);

  const get = useCallback((url, config = {}) => executeRequest('get', url, null, config), [executeRequest]);
  const post = useCallback((url, data, config = {}) => executeRequest('post', url, data, config), [executeRequest]);
  const put = useCallback((url, data, config = {}) => executeRequest('put', url, data, config), [executeRequest]);
  const deleteRequest = useCallback((url, config = {}) => executeRequest('delete', url, null, config), [executeRequest]);

  return {
    loading,
    error,
    get,
    post,
    put,
    delete: deleteRequest,
    clearError: () => setError(null)
  };
};

export const useSBAContent = () => {
  const api = useApi();

  const searchContent = useCallback(async (contentType, query = '', page = 1) => {
    const endpoint = `/api/sba/content/${contentType}`;
    const params = query ? { query, page } : { page };
    return api.get(endpoint, { params });
  }, [api]);

  const getContentDetails = useCallback(async (contentType, id) => {
    const endpoint = `/api/sba/content/${contentType}/${id}`;
    return api.get(endpoint);
  }, [api]);

  const getNodeDetails = useCallback(async (nodeId) => {
    return api.get(`/api/sba/content/node/${nodeId}`);
  }, [api]);

  return {
    searchContent,
    getContentDetails,
    getNodeDetails,
    loading: api.loading,
    error: api.error,
    clearError: api.clearError
  };
};
