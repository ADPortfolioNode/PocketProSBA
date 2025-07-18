### Multi-stage build: React frontend + Flask backend unified for production

# Stage 1: Build React frontend
FROM node:18 AS build_frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install --legacy-peer-deps
COPY frontend ./
# All files are copied before build; just run build
RUN npm run build

# Stage 2: Build Flask backend
FROM python:3.11-slim AS backend
WORKDIR /app
RUN apt-get update && apt-get install -y gcc g++ curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN pip install --upgrade pip setuptools wheel && pip install --no-cache-dir -r requirements.txt
# Copy backend code
COPY . .
# Copy React build output to Flask static folder (for production serving)
COPY --from=build_frontend /app/frontend/build ./static
# Expose port
ENV PORT=5000
ENV FLASK_ENV=production
ENV FLASK_APP=app_full.py
ENV PYTHONUNBUFFERED=1
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Start Flask backend (serves React build from /static)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app_full:app"]
