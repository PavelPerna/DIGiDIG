FROM ghcr.io/pavelperna/digidig-base:latest

WORKDIR /app

# Copy lib and config files (from project root)
COPY digidig/ ./digidig/
COPY config/ ./config/

# Copy service-specific files
COPY services/admin/requirements.txt .
RUN pip install --quiet --no-cache-dir -r requirements.txt

COPY services/admin/src/ .

# Copy start script
COPY services/admin/start.sh /start.sh
RUN chmod +x /start.sh

ENV PYTHONPATH=/app

# Expose both HTTP and HTTPS ports
EXPOSE 9105 9205

CMD ["/start.sh"]
