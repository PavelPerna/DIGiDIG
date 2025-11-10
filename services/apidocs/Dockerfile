FROM ghcr.io/pavelperna/digidig-base:latest

WORKDIR /app

# Copy requirements first for better layer caching
COPY services/apidocs/requirements.txt .
RUN pip install --quiet --no-cache-dir -r requirements.txt

# Copy source code
COPY services/apidocs/src/ ./src/

# Copy shared package so `import digidig` works
COPY digidig/ ./digidig/

# Copy configuration files
COPY config/ ./config/

# Add common module to path
ENV PYTHONPATH=/app

# Copy start script
COPY services/apidocs/start.sh /start.sh
RUN chmod +x /start.sh

# Expose both HTTP and HTTPS ports
EXPOSE 9110 9210

CMD ["/start.sh"]
