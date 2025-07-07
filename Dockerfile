FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port - Configurable via PORT env var
# Expose port - Configurable via PORT env var
ENV PORT=5000
ENV FLASK_ENV=production
ENV FLASK_APP=minimal_app.py
ENV PYTHONUNBUFFERED=1
EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1
    
# Start command - Use minimal_app for Render.com deployment
CMD gunicorn --bind 0.0.0.0:${PORT} --timeout 60 --workers 2 minimal_app:app
