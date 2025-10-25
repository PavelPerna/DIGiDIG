FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy common module and config files (from project root)
COPY lib/ /app/lib/
COPY config/ /app/config/
COPY locales/ /app/locales/

# Copy service requirements and install
COPY services/sso/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service application code
COPY services/sso/src/ /app/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8006

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8006/health')" || exit 1

# Run the application
CMD ["python", "sso.py"]