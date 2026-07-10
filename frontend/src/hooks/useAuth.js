import { useState, useCallback } from 'react';
import apiClient from '../api/apiClient';
import { useApp } from '../context/AppProvider';

const TOKEN_KEY = 'pocketpro_auth_token';
const USER_KEY = 'pocketpro_auth_user';

export const useAuth = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { setUser } = useApp();

  const persistSession = (user, token) => {
    if (user) {
      try {
        localStorage.setItem(USER_KEY, JSON.stringify(user));
      } catch (_) {
        /* ignore quota */
      }
      if (setUser) setUser(user);
    }
    if (token) {
      try {
        localStorage.setItem(TOKEN_KEY, token);
      } catch (_) {
        /* ignore */
      }
    }
  };

  const login = async (email, password) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.post('/api/login', { email, password });
      const user = response.data.user;
      const token = response.data.token;
      persistSession(user, token);
      return response.data;
    } catch (err) {
      const msg = err.response?.data?.error || 'Login failed';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (email, password, name) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.post('/api/register', {
        email,
        password,
        name: name || undefined,
      });
      return response.data;
    } catch (err) {
      const msg = err.response?.data?.error || 'Registration failed';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const forgotPassword = async (email) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.post('/api/forgot-password', { email });
      return response.data;
    } catch (err) {
      const msg = err.response?.data?.error || 'Password reset request failed';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const resetPassword = async (token, password) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.post('/api/reset-password', {
        token,
        password,
      });
      return response.data;
    } catch (err) {
      const msg = err.response?.data?.error || 'Password reset failed';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = useCallback(() => {
    try {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    } catch (_) {
      /* ignore */
    }
    if (setUser) setUser(null);
  }, [setUser]);

  return {
    login,
    register,
    forgotPassword,
    resetPassword,
    logout,
    loading,
    error,
  };
};
