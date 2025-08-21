import { useState, useContext } from 'react';
import apiClient from '../api/apiClient';
import { AppContext } from '../context/AppProvider';

const useApi = () => {
  const { setLoading } = useContext(AppContext);
  const [error, setError] = useState(null);

  const request = async (method, url, data = null) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient[method](url, data);
      setLoading(false);
      return response.data;
    } catch (err) {
      setError(err.response ? err.response.data : err.message);
      setLoading(false);
      throw err;
    }
  };

  return { request, error };
};

export default useApi;
