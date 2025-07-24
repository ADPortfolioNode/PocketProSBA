import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';
import Register from './Register';
import ForgotPassword from './ForgotPassword';

function Login() {
  return (
    <div className="container-centered">
      <h1 className="text-center mb-4">Welcome to PocketProSBA</h1>
      <p className="text-center text-muted mb-4">
        This is a modern, stylish greyscale Bootstrap template with mobile-first design.
      </p>
      <form>
        <div className="mb-3">
          <label htmlFor="email" className="form-label">Email address</label>
          <input type="email" className="form-control" id="email" placeholder="name@example.com" />
        </div>
        <div className="mb-3">
          <label htmlFor="password" className="form-label">Password</label>
          <input type="password" className="form-control" id="password" placeholder="Password" />
        </div>
        <button type="submit" className="btn btn-primary w-100">Sign In</button>
      </form>
      <p className="mt-3 text-center">
        <Link to="/register">Register</Link> | <Link to="/forgot-password">Forgot Password?</Link>
      </p>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
      </Routes>
    </Router>
  );
}

export default App;
