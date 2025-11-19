FROM ghcr.io/pavelperna/digidig-base:latest

WORKDIR /app

# Copy lib and config files (from project root)
COPY digidig/ ./digidig/
COPY config/ ./config/

# Copy and install digidig-core package
COPY lib/digidig-core/ ./digidig-core/
RUN pip install --quiet --no-cache-dir -e ./digidig-core

# Copy and install storage service as package
COPY services/storage/ ./storage-service/
RUN pip install --quiet --no-cache-dir -e ./storage-service

COPY services/storage/start.sh /start.sh
RUN chmod +x /start.sh

ENV PYTHONPATH=/app

EXPOSE 9102 9202

CMD ["/start.sh"]