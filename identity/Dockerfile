FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY scripts/ ./scripts/

RUN chmod +x /app/scripts/start.sh

EXPOSE 8001

ENV ADMIN_EMAIL=admin@example.com \
    ADMIN_PASSWORD=admin

CMD ["/app/scripts/start.sh"]