import React from 'react';
import { createRoot } from 'react-dom/client';
import 'bootstrap/dist/css/bootstrap.min.css';
import App from './App';
import './index.css';
import { AppProvider } from './context/AppProvider'; // Add this line

const container = document.getElementById('root');
const root = createRoot(container);

root.render(
  <React.StrictMode>
    <AppProvider> {/* Wrap App with AppProvider */}
      <App />
    </AppProvider>
  </React.StrictMode>
);