FROM node:16-alpine as build

WORKDIR /app/frontend

# Copy package files and install dependencies
COPY frontend/package*.json ./
RUN npm install
RUN npm install react-bootstrap@2.8.0 --save

# Copy source files
COPY frontend/. .

# Set environment variables - prevent ESLint errors from failing the build
ENV CI=false
ENV ESLINT_NO_DEV_ERRORS=true
ENV NODE_OPTIONS=--max-old-space-size=4096

# Build the application
RUN npm run build

# Production environment
FROM nginx:alpine
COPY --from=build /app/frontend/build /usr/share/nginx/html
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
