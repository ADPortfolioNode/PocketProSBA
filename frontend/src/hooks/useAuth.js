import { useState } from 'react';
import apiClient from '../api/apiClient';
import { useAppContext } from '../context/AppProvider';

export const useAuth = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { setUser } = useAppContext();

  const login = async (email, password) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.post('/api/login', { email, password });
      setUser(response.data.user); // Assuming API returns user data on successful login
      return response.data;
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (email, password) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.post('/api/register', { email, password });
      return response.data;
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Add other auth-related functions like logout, forgotPassword, etc.

  return { login, register, forgotPassword, loading, error };
};
