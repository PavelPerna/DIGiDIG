FROM ghcr.io/pavelperna/digidig-base:latest

WORKDIR /app

# Copy lib and config files (from project root)
COPY digidig/ ./digidig/
COPY lib/ ./lib/
COPY config/ ./config/

# Install the mail service package
RUN pip install --quiet --no-cache-dir -e services/mail

# Copy start script
COPY services/mail/start.sh /start.sh
RUN chmod +x /start.sh

ENV PYTHONPATH=/app

# Expose both HTTP and HTTPS ports
EXPOSE 9107 9207

CMD ["/start.sh"]
