# PocketPro:SBA Render.com Deployment Testing Checklist

This document provides a step-by-step checklist for testing the PocketPro:SBA application deployment on Render.com.

## Local Testing (Pre-Deployment)

### Docker Image Testing
- [ ] Run the test script: `./test-render-deployment.sh` (Linux/Mac) or `.\test-render-deployment.ps1` (Windows)
- [ ] Verify the Docker image builds successfully
- [ ] Confirm the health check endpoint responds with status 200
- [ ] Check logs for any errors or warnings

### Application Functionality Testing
- [ ] Manually test the Docker image:
  ```
  docker build -t pocketpro-sba-render -f Dockerfile.render .
  docker run -p 10000:10000 -e PORT=10000 -e FLASK_ENV=production -e GEMINI_API_KEY=your_actual_key pocketpro-sba-render
  ```
- [ ] Open browser to http://localhost:10000
- [ ] Test chat functionality
- [ ] Test document upload (will use simple vector store)
- [ ] Verify proper error handling for missing dependencies

## Render.com Deployment Testing

### Backend Deployment
- [ ] Fork/clone the repository to your GitHub account
- [ ] Connect your GitHub account to Render.com
- [ ] Create a new Blueprint deployment using the repository
- [ ] Set required environment variables:
  - `GEMINI_API_KEY` - Your Google Gemini API key
  - `SECRET_KEY` - A secure random string (or let Render generate one)
- [ ] Monitor the build logs for any errors
- [ ] Verify the backend service is running

### Frontend Deployment
- [ ] Verify the frontend static site is deployed
- [ ] Check the build logs for any errors
- [ ] Confirm the frontend can connect to the backend

### End-to-End Testing
- [ ] Open the frontend URL in a browser
- [ ] Test chat functionality
- [ ] Upload a document
- [ ] Ask questions about the uploaded document
- [ ] Verify real-time updates work

## Performance and Reliability Testing

- [ ] Check response times
- [ ] Monitor memory usage in the Render dashboard
- [ ] Test application after periods of inactivity (free tier spins down)
- [ ] Verify cold start behavior

## Security Testing

- [ ] Verify API key is not exposed in frontend
- [ ] Check CORS settings
- [ ] Test authentication if implemented
- [ ] Verify proper error handling doesn't leak sensitive information

## Troubleshooting Common Issues

### Build Failures
- [ ] Check for Rust compilation errors
- [ ] Verify Python version compatibility
- [ ] Check for memory limitations during build

### Runtime Errors
- [ ] Monitor application logs
- [ ] Verify all environment variables are set correctly
- [ ] Check for network connectivity issues

### Frontend Issues
- [ ] Verify REACT_APP_BACKEND_URL is set correctly
- [ ] Check browser console for errors
- [ ] Verify static files are being served correctly

## Final Verification

- [ ] Health check endpoint returns 200
- [ ] API endpoints function correctly
- [ ] User experience is smooth and responsive
- [ ] Application recovers properly from errors

## Sign-Off

- [ ] All critical functionality works as expected
- [ ] Performance is acceptable
- [ ] No security issues identified
- [ ] Documentation is updated to reflect any changes

Date: ___________________

Tester: __________________

Signature: _______________
