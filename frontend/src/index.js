import React from 'react';
import { createRoot } from 'react-dom/client';
import 'bootstrap/dist/css/bootstrap.min.css';
import App from './App';
import './index.css';

// Using createRoot API from React 18 instead of the deprecated ReactDOM.render
// This fixes the warning: "ReactDOM.render is no longer supported in React 18"
const container = document.getElementById('root');
const root = createRoot(container);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

