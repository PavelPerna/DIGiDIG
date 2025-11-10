#!/bin/bash
set -e

# Set Python path
export PYTHONPATH=/app:$PYTHONPATH

# Wait for database to be ready
echo "Waiting for database..."
for i in {1..30}; do
    # Get DB config from environment or defaults
    DB_HOST="${DB_HOST:-postgres}"
    DB_USER="${DB_USER:-postgres}"
    DB_PASSWORD="${DB_PASS:-securepassword}"
    DB_NAME="${DB_NAME:-digidig}"

    # Use Python asyncpg to check postgres connection
    if python3 -c "import asyncio, asyncpg; asyncio.run((lambda: asyncpg.connect(host='${DB_HOST}', user='${DB_USER}', password='${DB_PASSWORD}', database='${DB_NAME}'))())" 2>/dev/null; then
        echo "Database is ready!"
        break
    fi
    sleep 1
done

# Create default admin if it doesn't exist yet
python3 /app/scripts/create_admin.py || true

# Start the main service
cd /app
HTTP_PORT=${IDENTITY_HTTP_PORT:-9101}
HTTPS_PORT=${IDENTITY_HTTPS_PORT:-9201}
SSL_HOSTNAME=${DIGIDIG_HOSTNAME:-digidig.cz}

# Start HTTP server in background
echo "Starting HTTP server on port ${HTTP_PORT}"
uvicorn src.identity:app --host 0.0.0.0 --port ${HTTP_PORT} &

# Check if SSL certificates exist and start HTTPS server
if [ -f "/app/ssl/${SSL_HOSTNAME}.pem" ] && [ -f "/app/ssl/${SSL_HOSTNAME}-key.pem" ]; then
    echo "Starting HTTPS server on port ${HTTPS_PORT} with ${SSL_HOSTNAME} certificates"
    exec uvicorn src.identity:app --host 0.0.0.0 --port ${HTTPS_PORT} \
        --ssl-keyfile /app/ssl/${SSL_HOSTNAME}-key.pem \
        --ssl-certfile /app/ssl/${SSL_HOSTNAME}.pem
else
    echo "SSL certificates not found at /app/ssl/${SSL_HOSTNAME}.pem, running HTTP only"
    wait
fi