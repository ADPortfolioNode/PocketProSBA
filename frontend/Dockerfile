FROM node:22-alpine AS build

WORKDIR /app

# Install exactly what package-lock.json pins
COPY package.json package-lock.json ./
RUN npm ci

# Copy source files
COPY . .

# CI=false until the ESLint warnings are cleared (react-scripts treats
# warnings as errors when CI is truthy).
ENV CI=false
ENV NODE_OPTIONS=--max-old-space-size=4096

# Build the application
RUN npm run build

# Production environment
FROM nginx:1.27-alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80

# nginx:alpine ships busybox wget, not curl.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -q --spider http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
