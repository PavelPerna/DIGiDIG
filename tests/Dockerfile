FROM python:3.12-slim

WORKDIR /app

# Install test dependencies
COPY tests/requirements-test.txt ./tests/
RUN pip install --no-cache-dir -r tests/requirements-test.txt

# Copy common module and config files
COPY common/ ./common/
COPY config/ ./config/

# Copy identity module for unit tests
COPY identity/src/ ./identity/src/

# Copy test files
COPY tests/integration/ ./tests/integration/

# Set environment variables for tests
ENV PYTHONPATH=/app:/app/identity/src
ENV SKIP_COMPOSE=1

WORKDIR /app/tests

# Default command runs all tests
CMD ["pytest", "integration/", "-v", "--tb=short"]
