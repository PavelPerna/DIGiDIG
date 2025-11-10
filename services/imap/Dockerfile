FROM ghcr.io/pavelperna/digidig-base:latest

WORKDIR /app

# Copy lib and config files (from project root)
COPY digidig/ ./digidig/
COPY config/ ./config/

# Copy service-specific files
COPY services/imap/requirements.txt .
RUN pip install --quiet --no-cache-dir -r requirements.txt

COPY services/imap/src/imap.py .

ENV PYTHONPATH=/app
ARG PORT=9103
ENV PORT=${PORT}

EXPOSE ${PORT}

# Use shell form so ${PORT} is expanded at container runtime
CMD ["sh","-c","uvicorn imap:app --host 0.0.0.0 --port ${PORT}"]