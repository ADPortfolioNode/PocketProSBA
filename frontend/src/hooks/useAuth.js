import { useState, useCallback } from 'react';
import apiClient from '../api/apiClient';
import { useApp } from '../context/AppProvider';
import { clearSession, setSession } from '../utils/authStorage';

export const useAuth = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { setUser } = useApp();

  // Token + user go to authStorage; apiClient sends the token as a Bearer header.
  const persistSession = (user, token, expiresAt) => {
    setSession({ token, user, expiresAt });
    if (user && setUser) setUser(user);
  };

  const login = async (email, password) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.post('/api/login', { email, password });
      const user = response.data.user;
      const token = response.data.token;
      persistSession(user, token, response.data.expires_at);
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
      const response = await apiClient.post('/api/auth/reset-password', {
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
    clearSession();
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
