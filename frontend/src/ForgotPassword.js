import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import LoadingBar from './components/LoadingBar';
import { friendlyError } from './utils/friendlyError';

function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const { forgotPassword, loading, error: authError } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    if (!email) {
      setError('Email is required.');
      return;
    }

    try {
      await forgotPassword(email);
      setMessage('If this email is registered, you will receive password reset instructions.');
    } catch (err) {
      // authError from useAuth is stale inside this closure; read the failed request instead.
      // friendlyError keeps short 4xx messages ("Invalid credentials") and hides raw 5xx/network text.
      setError(friendlyError(err, authError || 'Password reset request failed. Please try again.'));
    }
  };

  return (
    <div className="container-centered">
      <h2 className="mb-4">Forgot Password</h2>
      {error && <div className="alert alert-danger">{error}</div>}
      {message && <div className="alert alert-success">{message}</div>}
      <form onSubmit={handleSubmit} noValidate>
        <div className="mb-3">
          <label htmlFor="email" className="form-label">Email address</label>
          <input
            type="email"
            className="form-control"
            id="email"
            placeholder="name@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <button type="submit" className="btn btn-primary w-100" disabled={loading} aria-busy={loading}>
          {loading ? <LoadingBar inline label="Sending…" /> : 'Send Reset Link'}
        </button>
      </form>
      <p className="mt-3 text-center auth-links">
        Have a reset token? <Link to="/reset-password">Set a new password</Link>
      </p>
      <p className="mt-2 text-center auth-links">
        Remembered your password? <Link to="/login">Log in</Link>
      </p>
    </div>
  );
}

export default ForgotPassword;
