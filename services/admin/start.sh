#!/bin/bash

# Get port configuration from environment with defaults
HTTP_PORT=${ADMIN_HTTP_PORT:-9105}
HTTPS_PORT=${ADMIN_HTTPS_PORT:-9205}
SSL_HOSTNAME=${DIGIDIG_HOSTNAME:-digidig.cz}

# Start HTTP server in background
echo "Starting Admin HTTP server on port ${HTTP_PORT}"
uvicorn admin:app --host 0.0.0.0 --port ${HTTP_PORT} &

# Start HTTPS server as main process if SSL certificates exist
if [ -f "/app/ssl/${SSL_HOSTNAME}.pem" ] && [ -f "/app/ssl/${SSL_HOSTNAME}-key.pem" ]; then
    echo "Starting Admin HTTPS server on port ${HTTPS_PORT}"
    exec uvicorn admin:app --host 0.0.0.0 --port ${HTTPS_PORT} \
        --ssl-keyfile /app/ssl/${SSL_HOSTNAME}-key.pem \
        --ssl-certfile /app/ssl/${SSL_HOSTNAME}.pem
else
    echo "SSL certificates not found at /app/ssl/${SSL_HOSTNAME}.pem, running HTTP only"
    wait
fi
