#!/bin/bash
set -e

# Add src to Python path for config_loader
export PYTHONPATH=/app/src:/app:$PYTHONPATH

# Wait for database to be ready
echo "Waiting for database..."
for i in {1..30}; do
    # Get DB credentials from Python config
    DB_HOST=$(python3 -c "from config_loader import config; print(config.DB_HOST)")
    DB_USER=$(python3 -c "from config_loader import config; print(config.DB_USER)")
    
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