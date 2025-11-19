FROM ghcr.io/pavelperna/digidig-base:latest

WORKDIR /app

# Copy lib and config files (from project root)
COPY digidig/ ./digidig/
COPY config/ ./config/

# Copy and install digidig-core package
COPY lib/digidig-core/ ./digidig-core/
RUN pip install --quiet --no-cache-dir -e ./digidig-core

# Copy and install imap service as package
COPY services/imap/ ./imap-service/
RUN pip install --quiet --no-cache-dir -e ./imap-service

ENV PYTHONPATH=/app
ARG PORT=9103
ENV PORT=${PORT}

EXPOSE ${PORT}

# Use shell form so ${PORT} is expanded at container runtime
CMD ["sh","-c","uvicorn imap.src.imap:app --host 0.0.0.0 --port ${PORT}"]