FROM ghcr.io/pavelperna/digidig-base:latest

WORKDIR /app

# Copy lib and config files (from project root)
COPY digidig/ ./digidig/
COPY config/ ./config/

# Copy service-specific files
COPY services/smtp/requirements.txt .
RUN pip install --quiet --no-cache-dir -r requirements.txt

COPY services/smtp/src/ .

ENV PYTHONPATH=/app
ARG PORT=9100
ENV PORT=${PORT}

EXPOSE ${PORT}

CMD ["sh","-c","uvicorn smtp:app --host 0.0.0.0 --port ${PORT}"]