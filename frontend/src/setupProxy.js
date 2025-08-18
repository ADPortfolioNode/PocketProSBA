const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Dynamic backend URL based on environment
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 
                    process.env.REACT_APP_API_BASE || 
                    'http://localhost:5000';

  console.log('Proxy configuration - Backend URL:', backendUrl);

  // API endpoints
  app.use(
    '/api',
    createProxyMiddleware({
      target: backendUrl,
      changeOrigin: true,
      secure: false,
      logLevel: 'debug',
      onError: (err, req, res) => {
        console.error('Proxy error:', err);
      }
    })
  );
  
  // Health endpoints
  app.use(
    '/health',
    createProxyMiddleware({
      target: backendUrl,
      changeOrigin: true,
      secure: false,
      logLevel: 'debug'
    })
  );
  
  // WebSocket endpoints
  app.use(
    '/ws',
    createProxyMiddleware({
      target: backendUrl.replace(/^http/, 'ws'),
      ws: true,
      changeOrigin: true,
      secure: false,
      logLevel: 'debug'
    })
  );
};
