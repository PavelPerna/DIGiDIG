#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database..."
for i in {1..30}; do
    if pg_isready -h $DB_HOST -U $DB_USER; then
        break
    fi
    sleep 1
done

# Create default admin if it doesn't exist yet
python3 /app/scripts/create_admin.py || true

# Start the main service - now correctly referencing the module in src/
cd /app/src
exec uvicorn identity:app --host 0.0.0.0 --port 8001