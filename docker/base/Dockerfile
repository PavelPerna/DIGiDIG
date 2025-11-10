FROM python:3.10-slim

LABEL maintainer="DIGiDIG Project"
LABEL description="Base image with common Python dependencies for all DIGiDIG services"

WORKDIR /app

# Install common dependencies used across all services
COPY requirements-base.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements-base.txt \
    && rm /tmp/requirements-base.txt

# Set Python path
ENV PYTHONPATH=/app

# Default command (will be overridden by service images)
CMD ["python", "--version"]
