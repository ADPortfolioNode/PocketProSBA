# Production Dockerfile for PocketPro:SBA Frontend
FROM node:16-alpine as build

WORKDIR /app

# Install dependencies only (leverage Docker cache)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --omit=dev

# Copy source code
COPY frontend/ ./

# Build the application
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

# Copy built files
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.prod.conf /etc/nginx/conf.d/default.conf

# Add health check
RUN apk add --no-cache curl
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
# Copy nginx configuration
COPY nginx.prod.conf /etc/nginx/conf.d/default.conf

# Add health check
RUN apk add --no-cache curl
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

# Set ChromaDB Server URL
ENV CHROMADB_URL=http://chromadb:8000

# Install Python and pip
RUN apk add --no-cache python3 py3-pip

# Install ChromaDB client
RUN pip install chromadb

# Copy backend code
COPY backend/ /app/backend

# Expose ChromaDB port
EXPOSE 8000

# Start ChromaDB server
CMD ["chromadb", "serve", "--host", "0.0.0.0", "--port", "8000"]