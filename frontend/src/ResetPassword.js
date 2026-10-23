import React, { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import LoadingBar from './components/LoadingBar';
import { friendlyError } from './utils/friendlyError';
import { MIN_PASSWORD_LENGTH } from './Register';

/** /reset-password?token=... — sets a new password with the emailed reset token. */
function ResetPassword() {
  const [searchParams] = useSearchParams();
  const tokenFromUrl = (searchParams.get('token') || '').trim();
  const [token, setToken] = useState(tokenFromUrl);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);

  const { resetPassword, loading, error: authError } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!token.trim()) {
      setError('Reset token is missing. Use the link from your email or request a new one.');
      return;
    }
    if (!password || !confirmPassword) {
      setError('All fields are required.');
      return;
    }
    if (password.length < MIN_PASSWORD_LENGTH) {
      setError(`Password must be at least ${MIN_PASSWORD_LENGTH} characters.`);
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    try {
      await resetPassword(token.trim(), password);
      setDone(true);
      setPassword('');
      setConfirmPassword('');
    } catch (err) {
      setError(friendlyError(err, authError || 'Password reset failed. Please try again.'));
    }
  };

  if (done) {
    return (
      <div className="container-centered">
        <h2 className="mb-4">Reset Password</h2>
        <div className="alert alert-success" role="status">
          Your password has been updated.
        </div>
        <p className="mt-3 text-center auth-links">
          <Link to="/login">Log in with your new password</Link>
        </p>
      </div>
    );
  }

  return (
    <div className="container-centered">
      <h2 className="mb-4">Reset Password</h2>
      {error && <div className="alert alert-danger">{error}</div>}
      <form onSubmit={handleSubmit} noValidate>
        {!tokenFromUrl && (
          <div className="mb-3">
            <label htmlFor="token" className="form-label">Reset token</label>
            <input
              type="text"
              className="form-control"
              id="token"
              placeholder="Paste the token from your email"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              autoComplete="off"
              required
            />
          </div>
        )}
        <div className="mb-3">
          <label htmlFor="password" className="form-label">New password</label>
          <input
            type="password"
            className="form-control"
            id="password"
            placeholder="New password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={MIN_PASSWORD_LENGTH}
            aria-describedby="passwordHelp"
            autoComplete="new-password"
            required
          />
          <div id="passwordHelp" className="form-text">Use {MIN_PASSWORD_LENGTH} or more characters.</div>
        </div>
        <div className="mb-3">
          <label htmlFor="confirmPassword" className="form-label">Confirm new password</label>
          <input
            type="password"
            className="form-control"
            id="confirmPassword"
            placeholder="Confirm new password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            autoComplete="new-password"
            required
          />
        </div>
        <button type="submit" className="btn btn-primary w-100" disabled={loading} aria-busy={loading}>
          {loading ? <LoadingBar inline label="Updating…" /> : 'Update Password'}
        </button>
      </form>
      <p className="mt-3 text-center auth-links">
        Need a new link? <Link to="/forgot-password">Request a reset</Link>
        {' · '}
        <Link to="/login">Log in</Link>
      </p>
    </div>
  );
}

export default ResetPassword;
