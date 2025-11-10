FROM ghcr.io/pavelperna/digidig-base:latest
WORKDIR /app

# Install service-specific requirements
COPY services/services/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared library and configuration from project root
COPY digidig/ ./digidig/
COPY config/ ./config/

# Copy service-specific files from repository
COPY services/services/src/ /app/

# Copy start script
COPY services/services/start.sh /start.sh
RUN chmod +x /start.sh

ENV PYTHONPATH=/app

# Expose both HTTP and HTTPS ports
EXPOSE 9120 9220

CMD ["/start.sh"]
