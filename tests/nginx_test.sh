#!/bin/bash

# Test health endpoint
echo "Testing health endpoint..."
curl -v http://localhost/health

# Test rate limiting
echo "Testing rate limiting..."
for i in {1..12}; do
    curl -w "Response: %{http_code}\n" http://localhost/health
    sleep 1
done

# Test WebSocket connection
echo "Testing WebSocket..."
wscat -c ws://localhost/socket.io/

# Test API endpoints
echo "Testing API endpoints..."
curl -v http://localhost/api/health

# Test compression
echo "Testing compression..."
curl -H "Accept-Encoding: gzip" -I http://localhost/api/health

# Test maximum file upload
echo "Testing file upload limit..."
dd if=/dev/zero of=test.file bs=60M count=1
curl -F "file=@test.file" http://localhost/api/upload
rm test.file

# Monitor nginx status
echo "Checking nginx status..."
curl http://localhost/nginx_status

# Test HTTPS and HTTP/2
echo "Testing HTTPS and HTTP/2..."
curl -v --http2 https://localhost/health
curl -v --http2 https://localhost/api/health

# Test SSL configuration
echo "Testing SSL configuration..."
openssl s_client -connect localhost:443 -tls1_2
