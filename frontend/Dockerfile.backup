FROM node:16-alpine as build

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy source files
COPY . .

# Set environment variables - prevent ESLint errors from failing the build
ENV CI=false
ENV ESLINT_NO_DEV_ERRORS=true
ENV NODE_OPTIONS=--max-old-space-size=4096

# Build the application
RUN npm run build

# Production environment
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
