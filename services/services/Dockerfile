FROM ghcr.io/pavelperna/digidig-base:latest
WORKDIR /app

# Install the services manager package
RUN pip install --no-cache-dir -e services/services

# Copy shared library and configuration from project root
COPY digidig/ ./digidig/
COPY config/ ./config/

# Copy start script
COPY services/services/start.sh /start.sh
RUN chmod +x /start.sh

ENV PYTHONPATH=/app

# Expose both HTTP and HTTPS ports
EXPOSE 9120 9220

CMD ["/start.sh"]
