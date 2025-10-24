FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Copy common module and config files (from project root)
COPY common/ ./common/
COPY config/ ./config/

# Copy service-specific files
COPY identity/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY identity/src/ ./src/
COPY identity/scripts/ ./scripts/

ENV PYTHONPATH=/app:$PYTHONPATH

RUN chmod +x /app/scripts/start.sh

EXPOSE 8001

ENV ADMIN_EMAIL=admin@example.com \
    ADMIN_PASSWORD=admin

CMD ["/app/scripts/start.sh"]