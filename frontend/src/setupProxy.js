const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: process.env.REACT_APP_BACKEND_URL || 'http://localhost:10000',
      changeOrigin: true,
    })
  );
  app.use(
    '/health',
    createProxyMiddleware({
      target: process.env.REACT_APP_BACKEND_URL || 'http://localhost:10000',
      changeOrigin: true,
    })
  );
  app.use(
    '/ws',
    createProxyMiddleware({
      target: process.env.REACT_APP_BACKEND_URL ? process.env.REACT_APP_BACKEND_URL.replace(/^http/, 'ws') : 'ws://localhost:10000',
      ws: true,
      changeOrigin: true,
    })
  );
};
