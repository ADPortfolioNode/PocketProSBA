#!/bin/sh
# Default port is 80 for Render, 8080 for local
PORT=${PORT:-80}

# Substitute environment variables in Nginx config template
envsubst '$PORT $REACT_APP_BACKEND_URL' < /etc/nginx/conf.d/nginx.render.conf.template > /etc/nginx/conf.d/default.conf

# Print config for debugging
echo "Using Nginx config:" && cat /etc/nginx/conf.d/default.conf
echo "Serving on port $PORT"

# Start Nginx
nginx -g 'daemon off;'