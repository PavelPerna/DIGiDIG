FROM ghcr.io/pavelperna/digidig-base:latest

WORKDIR /app

# Copy lib and config files (from project root)
COPY digidig/ ./digidig/
COPY config/ ./config/

# Copy service-specific files
COPY services/storage/requirements.txt .
RUN pip install --quiet --no-cache-dir -r requirements.txt

COPY services/storage/src/storage.py .
COPY services/storage/start.sh /start.sh
RUN chmod +x /start.sh

ENV PYTHONPATH=/app

EXPOSE 9102 9202

CMD ["/start.sh"]