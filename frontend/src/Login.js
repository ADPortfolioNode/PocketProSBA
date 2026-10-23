import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import LoadingBar from './components/LoadingBar';
import { friendlyError } from './utils/friendlyError';
import { safeReturnPath } from './utils/authStorage';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  // Set by the route guard / a 401: where to go back to after signing in.
  const nextParam = searchParams.get('next');
  const returnTo = safeReturnPath(nextParam || '/');

  const { login, loading, error: authError } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email || !password) {
      setError('Both email and password are required.');
      return;
    }

    try {
      await login(email, password);
      alert('Login successful!');
      navigate(returnTo, { replace: true }); // back to the page that needed sign-in (or Home)
    } catch (err) {
      // Error is already set by useAuth hook, but we can add more specific handling here if needed
      // authError from useAuth is stale inside this closure; read the failed request instead.
      // friendlyError keeps short 4xx messages ("Invalid credentials") and hides raw 5xx/network text.
      setError(friendlyError(err, authError || 'Login failed. Please try again.'));
    }
  };

  return (
    <div className="container-centered">
      <h2 className="mb-4">Login</h2>
      {nextParam && !error && (
        <div className="alert alert-info" role="status">Please log in to continue.</div>
      )}
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
            required
          />
        </div>
        <button type="submit" className="btn btn-primary w-100" disabled={loading} aria-busy={loading}>
          {loading ? <LoadingBar inline label="Signing in…" /> : 'Log In'}
        </button>
      </form>
      <p className="mt-3 text-center auth-links">
        Don't have an account? <Link to="/register">Register</Link>
        <span className="mx-2" aria-hidden="true">·</span>
        <Link to="/forgot-password">Forgot password?</Link>
      </p>
    </div>
  );
}

export default Login; 