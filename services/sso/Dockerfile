FROM ghcr.io/pavelperna/digidig-base:latest

WORKDIR /app

# Copy shared library code first
COPY digidig/ /app/digidig/

# Copy shared components
COPY lib/ /app/lib/

# Install the SSO service package
RUN pip install --no-cache-dir -e services/sso

# Copy configuration files
COPY config/ /app/config/

# Copy start script
COPY services/sso/start.sh /start.sh
RUN chmod +x /start.sh

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose both HTTP and HTTPS ports
EXPOSE 9106 9206

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:9106/health')" || exit 1

# Run the application
CMD ["/start.sh"]