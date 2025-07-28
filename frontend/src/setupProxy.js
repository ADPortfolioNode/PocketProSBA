const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Hardcode remote backend URL for testing
  const backendUrl = 'https://pocketprosba-backend.onrender.com';
  
  console.log('Setting up proxy to:', backendUrl);
  
  // Only set up proxy if using localhost backend
  // If using remote backend (like Render), let the frontend make direct requests
  if (backendUrl.includes('localhost')) {
    app.use(
      '/api',
      createProxyMiddleware({
        target: backendUrl,
        changeOrigin: true,
        secure: false,
        logLevel: 'debug'
      })
    );
  } else {
    console.log('Using remote backend, skipping proxy setup');
  }
};
