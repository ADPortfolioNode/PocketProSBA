# PocketPro:SBA Production Deployment Guide

## Quick Deploy to Render.com

### Option 1: Using render.yaml (Recommended)

1. **Fork/Clone this repository to your GitHub account**

2. **Connect to Render.com:**
   - Go to [render.com](https://render.com)
   - Connect your GitHub account
   - Create a new "Blueprint" deployment
   - Select this repository

3. **Set Environment Variables:**
   ```
   GEMINI_API_KEY=your_google_gemini_api_key_here
   SECRET_KEY=your_secret_key_here
   ```

4. **Deploy:**
   - Render will automatically deploy both frontend and backend
   - The backend will be available at: `https://your-backend-name.onrender.com`
   - The frontend will be available at: `https://your-frontend-name.onrender.com`

### Option 2: Manual Deployment

#### Backend Deployment
1. Create a new Web Service on Render
2. Connect your repository
3. Set the following:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn --bind 0.0.0.0:$PORT app:app`
   - **Environment:** Python 3.9

#### Frontend Deployment  
1. Create a new Static Site on Render
2. Connect your repository
3. Set the following:
   - **Build Command:** `cd frontend && npm install && npm run build`
   - **Publish Directory:** `frontend/build`
   - **Environment Variable:** `REACT_APP_BACKEND_URL=https://your-backend-url.onrender.com`

## Local Development Setup

### Using Docker (Simplified)
```bash
# Start the simplified production setup
docker-compose -f docker-compose.simple.yml up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:5000
```

### Traditional Development
```bash
# Backend
pip install -r requirements.txt
python run.py

# Frontend (in another terminal)
cd frontend
npm install
npm start
```

## Key Features

✅ **RAG (Retrieval-Augmented Generation)**
- Document upload and processing
- Vector search with ChromaDB
- AI-powered question answering

✅ **SBA Business Resources**
- Pre-loaded SBA program information
- Loan and grant guidance
- Business development resources

✅ **Task Decomposition**
- Break down complex business tasks
- Step-by-step guidance
- Progress tracking

✅ **Real-time Chat Interface**
- WebSocket-powered chat
- Multiple AI assistants
- Document-aware conversations

## Environment Variables

### Required
- `GEMINI_API_KEY`: Your Google Gemini API key
- `SECRET_KEY`: Flask secret key for sessions

### Optional
- `FLASK_ENV`: Set to 'production' for production
- `CHROMA_HOST`: ChromaDB host (default: localhost)
- `CHROMA_PORT`: ChromaDB port (default: 8000)

## Troubleshooting

### Common Issues

1. **Frontend Build Fails**
   - Ensure Node.js 16+ is installed
   - Clear npm cache: `npm cache clean --force`
   - Delete node_modules and reinstall

2. **Backend Import Errors**
   - Check Python path in environment
   - Ensure all dependencies are installed
   - Verify GEMINI_API_KEY is set

3. **ChromaDB Connection Issues**
   - For production, consider using external vector DB
   - Ensure ChromaDB service is running
   - Check network connectivity

### Production Considerations

1. **Database:** ChromaDB data persistence
2. **Security:** Environment variable management
3. **Scaling:** Consider load balancing for high traffic
4. **Monitoring:** Set up health checks and logging

## Support

For issues or questions:
- Check the logs: `docker-compose logs`
- Review the health endpoint: `/health`
- Verify environment variables are set correctly
