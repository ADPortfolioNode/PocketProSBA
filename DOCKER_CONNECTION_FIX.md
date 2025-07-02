# Docker Backend Connection Issues and Solutions

## Symptoms
You may see connection errors in your browser console like these:

```
App.js:96 GET http://localhost:10000/api/models 502 (Bad Gateway)
App.js:80 GET http://localhost:10000/api/greeting 502 (Bad Gateway)
App.js:127 GET http://localhost:10000/api/collections/stats 502 (Bad Gateway)
App.js:141 GET http://localhost:10000/api/search/filters 502 (Bad Gateway)
App.js:155 GET http://localhost:10000/api/assistants 502 (Bad Gateway)
App.js:113 GET http://localhost:10000/api/documents 502 (Bad Gateway)
App.js:169 GET http://localhost:10000/api/info 502 (Bad Gateway)
```

And JSON parsing errors like these:

```
App.js:106 Error fetching models: SyntaxError: Unexpected token '<', "<html>
<h"... is not valid JSON
```

## Cause
When running in Docker mode, the Nginx configuration didn't correctly proxy the `/health` endpoint to the backend service, causing it to return an HTML error page instead of the expected JSON response.

## Solutions

### 1. Updated Nginx Configuration
The nginx.conf file has been updated to properly proxy the `/health` endpoint to the backend service:

```nginx
# Proxy health check endpoint to backend
location /health {
    proxy_pass http://backend:5000/health;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### 2. Diagnostic Scripts
Enhanced diagnostic scripts have been added to help identify connection issues:

- **check-backend.bat / check-backend.ps1**: Checks if the backend API is running on both port 5000 (local development) and port 10000 (Docker)
- **diagnose-connection.bat / diagnose-connection.ps1**: Comprehensive diagnostic tools that check the backend, frontend configuration, Docker status, and network connectivity

### How to Use

1. **Restart Docker containers to apply Nginx changes:**
   ```
   docker-compose down
   docker-compose up -d
   ```

2. **Run diagnostics to verify connections:**
   ```
   .\check-backend.bat
   ```
   or
   ```
   .\diagnose-connection.ps1
   ```

3. **Check frontend environment configuration:**
   - Make sure your frontend/.env file has:
     ```
     REACT_APP_BACKEND_URL=http://localhost:10000
     ```
   - For local development, you may use:
     ```
     REACT_APP_BACKEND_URL=http://localhost:5000
     ```

## Additional Configuration for Stable Front-End/Back-End Communication

### React Proxy Configuration

For local development without Docker, add a proxy configuration in your frontend/package.json:

```json
"proxy": "http://localhost:5000"
```

This allows the React development server to proxy API requests to your Flask backend without CORS issues.

### CORS Configuration for Flask Backend

Ensure your Flask backend has proper CORS configuration:

```python
# In your Flask app initialization file
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

For production, restrict origins to specific domains:

```python
CORS(app, resources={r"/api/*": {"origins": ["https://your-app.render.com", "http://localhost:3000"]}})
```

### Environment-Specific Configuration

Create environment-specific .env files:

#### For local development (frontend/.env.development):
```
REACT_APP_BACKEND_URL=http://localhost:5000
```

#### For Docker development (frontend/.env):
```
REACT_APP_BACKEND_URL=http://localhost:10000
```

#### For production on render.com (frontend/.env.production):
```
REACT_APP_BACKEND_URL=https://your-api.render.com
```

## Optimizing for Render.com Deployment

1. **Set up render.yaml for Blueprint deployment:**
   ```yaml
   services:
     - type: web
       name: frontend
       env: static
       buildCommand: cd frontend && npm install && npm run build
       staticPublishPath: frontend/build
       envVars:
         - key: REACT_APP_BACKEND_URL
           value: https://your-api.render.com

     - type: web
       name: backend
       env: python
       buildCommand: pip install -r requirements.txt
       startCommand: gunicorn app:app
       envVars:
         - key: FLASK_ENV
           value: production
   ```

2. **Configure health checks in your Flask app:**
   ```python
   @app.route('/health')
   def health():
       return jsonify({"status": "healthy"})
   ```

3. **Update your Docker configuration to match Render's environment:**
   - Use compatible base images
   - Implement proper health checks
   - Use environment variables for configuration

## Additional Troubleshooting

If you still encounter issues:

1. **Check Docker container logs:**
   ```
   docker-compose logs
   ```

2. **Verify all containers are running:**
   ```
   docker-compose ps
   ```

3. **Try accessing the API directly in a browser:**
   - http://localhost:10000/api/info
   - http://localhost:10000/health

4. **Rebuild the containers if needed:**
   ```
   docker-compose build
   docker-compose up -d
   ```

## Ensuring Front-End/Back-End Consistency

### API Route Verification

To verify all API endpoints are working correctly with the front-end, use the following checklist:

1. **Core API Endpoints Checklist:**
   - [ ] `/api/info` - Application information
   - [ ] `/api/greeting` - Welcome message
   - [ ] `/api/models` - Available models
   - [ ] `/api/documents` - Document listing
   - [ ] `/api/collections/stats` - Collection statistics
   - [ ] `/api/search/filters` - Search filters
   - [ ] `/api/assistants` - Available assistants
   - [ ] `/health` - Health check endpoint

2. **Run the API verification script:**
   ```
   .\verify-api-endpoints.ps1
   ```
   or
   ```
   .\verify-api-endpoints.bat
   ```

### UI Functionality Testing

After ensuring API connectivity, verify the following UI features work correctly:

1. **Home Page:**
   - [ ] Application loads without console errors
   - [ ] Welcome message displays correctly
   - [ ] Navigation elements are visible and functional

2. **Document Management:**
   - [ ] Document list loads correctly
   - [ ] Documents can be viewed
   - [ ] Search functionality works
   - [ ] Filters apply correctly

3. **Model Selection:**
   - [ ] Models dropdown populates
   - [ ] Model selection changes are saved
   - [ ] Model-specific features work appropriately

4. **Responsive Design:**
   - [ ] UI works on desktop browsers
   - [ ] UI adapts to mobile viewports
   - [ ] UI elements scale appropriately

### Regression Testing Procedure

To minimize regression when making changes:

1. **Capture baseline screenshots** of key UI screens before changes
2. **Document expected API responses** for comparison
3. **Perform changes** to configuration or code
4. **Re-run API verification script** to confirm endpoints still work
5. **Complete UI checklist** to verify user experience 
6. **Compare against baseline** to identify any regressions

If issues are detected, check the browser console for specific errors and verify the corresponding API endpoint directly.

## Common Build Errors and Solutions

### React Frontend Build Errors

1. **Missing catch or finally clause (ESLint error)**
   
   ```
   [eslint]
   src/App.js
   Syntax error: Missing catch or finally clause. (66:4) (66:4)
   ```
   
   **Solution:**
   Check line 66 in your App.js file for an incomplete try block. This specific error occurs at line 66 where a try block is missing its corresponding catch or finally clause.
   
   To fix this, you can:
   
   **Option 1: Add a catch block (recommended):**
   ```javascript
   // Around line 66 in App.js
   try {
     const response = await fetch(`${backendUrl}/api/endpoint`);
     const data = await response.json();
     // ...other code
   } catch (error) {
     console.error("Error fetching data:", error);
     // Handle the error appropriately
   }
   ```
   
   **Option 2: Disable ESLint temporarily:**
   If you're in a hurry and need a quick fix to make the build pass, you can modify your Docker build process to bypass ESLint:
   
   In your frontend/Dockerfile:
   ```dockerfile
   # Add this before npm run build
   ENV CI=false
   ```
   
   Or in your docker-compose.yml for the frontend service:
   ```yaml
   environment:
     - CI=false
   ```
   
   **Option 3: Fix during development:**
   Run this command to directly fix App.js:
   ```
   cd frontend
   npx eslint --fix src/App.js
   ```

2. **Build process timeout**
   
   If the build process is timing out, try increasing the memory allocation for Node.js:
   
   ```
   # In your frontend Dockerfile
   ENV NODE_OPTIONS="--max-old-space-size=4096"
   ```
   
   Or in your package.json scripts:
   ```json
   "build": "node --max-old-space-size=4096 node_modules/.bin/react-scripts build"
   ```

3. **Missing dependencies**
   
   If you see errors about missing dependencies, make sure your package.json is complete and run:
   ```
   npm install --save-exact react@version react-dom@version
   ```

### Docker Build Troubleshooting

If Docker builds continue to fail:

1. **Check Docker logs for detailed errors:**
   ```
   docker-compose logs frontend
   ```

2. **Build without caching:**
   ```
   docker-compose build --no-cache frontend
   ```

3. **Try building frontend locally first:**
   ```
   cd frontend
   npm install
   npm run build
   ```
   This can provide more detailed error messages.
