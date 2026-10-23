import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import LoadingBar from './components/LoadingBar';
import { friendlyError } from './utils/friendlyError';

// Keep in sync with backend/routes/auth.py MIN_PASSWORD_LENGTH
export const MIN_PASSWORD_LENGTH = 8;

function Register() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const { register, loading, error: authError } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email || !password || !confirmPassword) {
      setError('All fields are required.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    if (password.length < MIN_PASSWORD_LENGTH) {
      setError(`Password must be at least ${MIN_PASSWORD_LENGTH} characters.`);
      return;
    }

    try {
      await register(email, password);
      alert('Registration successful! Please log in.');
      navigate('/login');
    } catch (err) {
      // authError from useAuth is stale inside this closure; read the failed request instead.
      // friendlyError keeps short 4xx messages ("Invalid credentials") and hides raw 5xx/network text.
      setError(friendlyError(err, authError || 'Registration failed. Please try again.'));
    }
  };

  return (
    <div className="container-centered">
      <h2 className="mb-4">Register</h2>
      {error && <div className="alert alert-danger">{error}</div>}
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
        <div className="mb-3">
          <label htmlFor="password" className="form-label">Password</label>
          <input
            type="password"
            className="form-control"
            id="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={MIN_PASSWORD_LENGTH}
            aria-describedby="passwordHelp"
            required
          />
          <div id="passwordHelp" className="form-text">Use {MIN_PASSWORD_LENGTH} or more characters.</div>
        </div>
        <div className="mb-3">
          <label htmlFor="confirmPassword" className="form-label">Confirm Password</label>
          <input
            type="password"
            className="form-control"
            id="confirmPassword"
            placeholder="Confirm Password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />
        </div>
        <button type="submit" className="btn btn-primary w-100" disabled={loading} aria-busy={loading}>
          {loading ? <LoadingBar inline label="Creating account…" /> : 'Sign Up'}
        </button>
      </form>
      <p className="mt-3 text-center auth-links">
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </div>
  );
}

export default Register;
