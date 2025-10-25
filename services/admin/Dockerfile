FROM python:3.10-slim

WORKDIR /app

# Install Docker CLI and docker-compose for restart functionality
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    curl && \
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc && \
    chmod a+r /etc/apt/keyrings/docker.asc && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian bookworm stable" > /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends docker-ce-cli docker-compose-plugin && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy lib and config files (from project root)
COPY lib/ ./lib/
COPY config/ ./config/

# Copy service-specific files
COPY services/admin/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/admin/src/ .

ENV PYTHONPATH=/app:$PYTHONPATH

EXPOSE 8005

CMD ["uvicorn", "admin:app", "--host", "0.0.0.0", "--port", "8005"]