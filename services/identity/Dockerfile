FROM ghcr.io/pavelperna/digidig-base:latest

WORKDIR /app

# Copy lib and config files (from project root)
COPY digidig/ ./digidig/
COPY config/ ./config/

# Copy and install digidig-core package
COPY lib/digidig-core/ ./digidig-core/
RUN pip install --quiet --no-cache-dir -e ./digidig-core

# Copy and install identity service as package
COPY services/identity/ ./identity-service/
RUN pip install --quiet --no-cache-dir -e ./identity-service

COPY services/identity/scripts/ ./scripts/

ENV PYTHONPATH=/app

RUN chmod +x /app/scripts/start.sh

EXPOSE 9101 9201

ENV ADMIN_EMAIL=admin@example.com \
    ADMIN_PASSWORD=admin

CMD ["/app/scripts/start.sh"]