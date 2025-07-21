FROM python:3.11-slim

LABEL maintainer="PocketPro:SBA Team"
LABEL version="1.0"
LABEL description="Production Dockerfile for PocketPro:SBA on Render.com"

# Set working directory
WORKDIR /app

## Copy requirements for better caching
COPY requirements_full.txt ./requirements-full.txt

# Install system dependencies and Python dependencies with optimizations
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements_full.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    mkdir -p /app/logs /app/static && \
    chown -R appuser:appuser /app/logs /app/static

# Switch to non-root user
USER appuser

## Environment variables
ENV PORT=10000
ENV FLASK_ENV=production
ENV FLASK_APP=app_full.py
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONIOENCODING=utf-8

## Expose port
EXPOSE 10000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

## Start command
CMD gunicorn --bind 0.0.0.0:10000 --timeout 120 --workers 1 app_full:app
