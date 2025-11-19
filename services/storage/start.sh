#!/bin/sh
HTTP_PORT=${STORAGE_HTTP_PORT:-9102}
HTTPS_PORT=${STORAGE_HTTPS_PORT:-9202}
SSL_HOSTNAME=${DIGIDIG_HOSTNAME:-digidig.cz}

# Start HTTP server in background
echo "Starting HTTP server on port ${HTTP_PORT}"
uvicorn storage:app --host 0.0.0.0 --port ${HTTP_PORT} &

# Check if SSL certificates exist and start HTTPS server
if [ -f "/app/ssl/${SSL_HOSTNAME}.pem" ] && [ -f "/app/ssl/${SSL_HOSTNAME}-key.pem" ]; then
    echo "Starting HTTPS server on port ${HTTPS_PORT} with ${SSL_HOSTNAME} certificates"
    exec uvicorn storage:app --host 0.0.0.0 --port ${HTTPS_PORT} \
        --ssl-keyfile /app/ssl/${SSL_HOSTNAME}-key.pem \
        --ssl-certfile /app/ssl/${SSL_HOSTNAME}.pem
else
    echo "SSL certificates not found at /app/ssl/${SSL_HOSTNAME}.pem, running HTTP only"
    wait
fi
