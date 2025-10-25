FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Copy common module and config files (from project root)
COPY lib/ ./lib/
COPY config/ ./config/

# Copy service-specific files
COPY services/identity/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/identity/src/ ./src/
COPY services/identity/scripts/ ./scripts/

ENV PYTHONPATH=/app

RUN chmod +x /app/scripts/start.sh

EXPOSE 8001

ENV ADMIN_EMAIL=admin@example.com \
    ADMIN_PASSWORD=admin

CMD ["/app/scripts/start.sh"]