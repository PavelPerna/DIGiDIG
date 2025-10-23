FROM python:3.12-slim

WORKDIR /app

# Install system deps needed for asyncpg and building wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy test requirements and install both test and runtime deps
COPY tests/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir fastapi asyncpg PyJWT

# Copy the project (only identity subtree to keep image small)
COPY src /app/identity/src
COPY tests /app/identity/tests

WORKDIR /app

CMD ["pytest", "-q", "identity/tests"]
