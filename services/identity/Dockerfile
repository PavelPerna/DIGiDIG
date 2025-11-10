FROM ghcr.io/pavelperna/digidig-base:latest

WORKDIR /app

# Copy lib and config files (from project root)
COPY digidig/ ./digidig/
COPY config/ ./config/

# Copy service-specific requirements and install ONLY service-specific dependencies
COPY services/identity/requirements.txt .
RUN pip install --quiet --no-cache-dir -r requirements.txt

COPY services/identity/src/ ./src/
COPY services/identity/scripts/ ./scripts/

ENV PYTHONPATH=/app

RUN chmod +x /app/scripts/start.sh

EXPOSE 9101 9201

ENV ADMIN_EMAIL=admin@example.com \
    ADMIN_PASSWORD=admin

CMD ["/app/scripts/start.sh"]