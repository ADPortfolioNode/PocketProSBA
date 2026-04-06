# 🚀 Render.com Deployment Guide for PocketPro:SBA

## Quick Deployment Steps

### 1. Repository Setup
```bash
# Make sure your code is in a Git repository
git add .
git commit -m "Render deployment ready"
git push origin main
```

### 2. Render.com Deployment Options

#### Option A: Blueprint Deployment (Recommended)
1. Go to [render.com](https://render.com) and sign up/login
2. Click "New" → "Blueprint"
3. Connect your GitHub repository
4. Render will automatically use the `render.yaml` configuration
5. Add environment variables:
   - `GEMINI_API_KEY`: Your Google Gemini API key
6. Click "Deploy"

#### Option B: Manual Service Creation
1. **Backend Service:**
   - Type: Web Service
   - Runtime: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 run:app`
   - Environment Variables:
     - `GEMINI_API_KEY`: Your API key
     - `PYTHON_VERSION`: 3.11.4

2. **Frontend Service:**
   - Type: Static Site
   - Build Command: `cd frontend && npm install --legacy-peer-deps && npm run build`
   - Publish Directory: `frontend/build`
   - Environment Variables:
     - `REACT_APP_BACKEND_URL`: Your backend URL from step 1

### 3. Required Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini API key for AI features |
| `SECRET_KEY` | ⚠️ Auto-generated | Flask session secret |
| `PYTHON_VERSION` | ⚠️ Optional | Set to 3.11.4 for best compatibility |

### 4. Expected Results

After deployment:
- **Backend**: `https://your-backend-name.onrender.com`
- **Frontend**: `https://your-frontend-name.onrender.com`
- **Health Check**: `https://your-backend-name.onrender.com/health`

## Troubleshooting

### Common Issues and Solutions

1. **Build Timeout**
   ```yaml
   # In render.yaml, reduce dependencies:
   buildCommand: pip install --no-cache-dir -r requirements.txt
   ```

2. **Memory Issues**
   ```yaml
   # Use fewer workers:
   startCommand: gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 run:app
   ```

3. **Import Errors**
   - Check that all dependencies are in requirements.txt
   - Verify PYTHONPATH is set correctly in render.yaml

4. **Frontend Build Fails**
   ```bash
   # Use legacy peer deps:
   cd frontend && npm install --legacy-peer-deps && npm run build
   ```

### Health Check Endpoints

Your application provides several health check endpoints:

- `/health` - Basic health status
- `/api/info` - API information
- `/` - Application welcome message

### Performance Tips

1. **Use Free Tier Efficiently:**
   - Services sleep after 15 minutes of inactivity
   - First request after sleep takes ~30 seconds
   - Keep services warm with external monitoring

2. **Optimize for RAG Performance:**
   - ChromaDB data persists in memory only on free tier
   - Consider upgrading for persistent vector storage
   - Use smaller embedding models for faster startup

3. **Monitor Resource Usage:**
   - Free tier: 512MB RAM, 0.1 CPU
   - Monitor logs for memory/CPU usage
   - Optimize dependencies as needed

## Production Considerations

### Vector Database
- **Free Tier**: In-memory ChromaDB (data lost on restart)
- **Production**: Consider external vector database service
- **Alternative**: Use Pinecone, Weaviate, or Qdrant cloud services

### File Storage
- **Free Tier**: Ephemeral file system
- **Production**: Use cloud storage (AWS S3, Google Cloud Storage)

### Scaling
- **Start**: Single service with basic features
- **Scale**: Add Redis for session storage, external DB for vectors
- **Enterprise**: Microservices architecture with load balancing

## Support and Monitoring

### Logs and Debugging
```bash
# View logs in Render dashboard or via CLI
render logs --service your-service-name --tail
```

### Performance Monitoring
- Use Render's built-in metrics
- Set up external monitoring (UptimeRobot, etc.)
- Monitor /health endpoint for service status

### Getting Help
1. Check Render documentation: https://render.com/docs
2. Review deployment logs in Render dashboard
3. Test locally with production settings first
4. Use health check script: `python health_check_render.py`

---

**🎯 Your PocketPro:SBA RAG application is now ready for Render.com deployment!**
