#!/bin/bash

# Get port configuration from environment with defaults
HTTP_PORT=${APIDOCS_HTTP_PORT:-9110}
HTTPS_PORT=${APIDOCS_HTTPS_PORT:-9210}
SSL_HOSTNAME=${DIGIDIG_HOSTNAME:-digidig.cz}

# Start HTTP server in background
echo "Starting Apidocs HTTP server on port ${HTTP_PORT}"
uvicorn apidocs:app --host 0.0.0.0 --port ${HTTP_PORT} --app-dir /app/src &

# Start HTTPS server as main process if SSL certificates exist
if [ -f "/app/ssl/${SSL_HOSTNAME}.pem" ] && [ -f "/app/ssl/${SSL_HOSTNAME}-key.pem" ]; then
    echo "Starting Apidocs HTTPS server on port ${HTTPS_PORT}"
    exec uvicorn apidocs:app --host 0.0.0.0 --port ${HTTPS_PORT} --app-dir /app/src \
        --ssl-keyfile /app/ssl/${SSL_HOSTNAME}-key.pem \
        --ssl-certfile /app/ssl/${SSL_HOSTNAME}.pem
else
    echo "SSL certificates not found at /app/ssl/${SSL_HOSTNAME}.pem, running HTTP only"
    wait
fi
