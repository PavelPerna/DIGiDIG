FROM ghcr.io/pavelperna/digidig-base:latest

WORKDIR /app

# Copy requirements first for better caching
COPY services/test-suite/requirements.txt .
# Install minimal tooling; use Python requests for HTTP checks
RUN pip install --quiet --no-cache-dir -r requirements.txt

# Copy shared libraries
COPY digidig/ ./digidig/
COPY config/ ./config/

# Copy service code
COPY services/test-suite/src/ .
COPY services/test-suite/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 9108 9208

CMD ["/start.sh"]