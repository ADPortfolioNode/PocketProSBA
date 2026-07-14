const express = require('express');
const path = require('path');
const cors = require('cors');

const app = express();

// Enable CORS
app.use(cors());

// Serve static files from the React app build directory
app.use(express.static(path.join(__dirname, '../frontend/build')));

// API routes should go here
// app.use('/api/your-endpoints', yourRoutes);

// The "catchall" handler: for any request that doesn't
// match one above, send back React's index.html file.
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../frontend/build/index.html'));
});

// Example Express error handler (add at the end of your middleware stack)
app.use((err, req, res, next) => {
  console.error(err);
  res.status(err.status || 500).json({
    success: false,
    error: {
      message: err.message || "Internal Server Error",
      code: err.code || "SERVER_ERROR"
    }
  });
});

// For routes, always return JSON on error:
app.get('/api/registry', async (req, res) => {
  try {
    // ...existing code...
  } catch (err) {
    res.status(500).json({
      success: false,
      error: {
        message: err.message || "Registry fetch failed",
        code: "REGISTRY_ERROR"
      }
    });
  }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});