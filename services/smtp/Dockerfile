FROM ghcr.io/pavelperna/digidig-base:latest

WORKDIR /app

# Copy lib and config files (from project root)
COPY digidig/ ./digidig/
COPY config/ ./config/

# Copy and install digidig-core package
COPY lib/digidig-core/ ./digidig-core/
RUN pip install --quiet --no-cache-dir -e ./digidig-core

# Copy and install smtp service as package
COPY services/smtp/ ./smtp-service/
RUN pip install --quiet --no-cache-dir -e ./smtp-service

ENV PYTHONPATH=/app
ARG PORT=9100
ENV PORT=${PORT}

EXPOSE ${PORT}

CMD ["sh","-c","uvicorn smtp.src.smtp:app --host 0.0.0.0 --port ${PORT}"]