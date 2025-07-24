import React, { useState } from 'react';
import { Link } from 'react-router-dom';

function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    if (!email) {
      setError('Email is required.');
      return;
    }

    // TODO: Implement forgot password API call here

    setMessage('If this email is registered, you will receive password reset instructions.');
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
        <button type="submit" className="btn btn-primary w-100">Send Reset Link</button>
      </form>
      <p className="mt-3 text-center">
        Remembered your password? <Link to="/login">Log in</Link>
      </p>
    </div>
  );
}

export default ForgotPassword;
