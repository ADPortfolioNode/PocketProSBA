#!/bin/sh
set -e
# Substitute environment variables in the nginx configuration
envsubst < /etc/nginx/conf.d/nginx.render.conf.template > /etc/nginx/conf.d/default.conf
# Start nginx
nginx -g 'daemon off;'
