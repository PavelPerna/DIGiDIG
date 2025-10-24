FROM python:3.12-slim

WORKDIR /app

# Copy test dependencies
COPY _test/requirements-test.txt ./_test/
RUN pip install --no-cache-dir -r _test/requirements-test.txt

# Copy common module and config files
COPY lib/ ./lib/
COPY config/ ./config/

# Copy all service modules for comprehensive testing
COPY services/ ./services/

# Create empty static directories for services that need them during import
# These need to be in the service src directories where the services expect them
RUN mkdir -p /app/services/admin/src/static /app/services/client/src/static

# Copy all test files (integration and unit)
COPY _test/integration/ ./_test/integration/
COPY _test/unit/ ./_test/unit/
COPY _test/conftest.py ./_test/
COPY _test/pytest.ini ./_test/

# Set environment variables for tests
ENV PYTHONPATH=/app:/app/services/identity/src:/app/services/smtp/src:/app/services/imap/src:/app/services/storage/src:/app/services/client/src:/app/services/admin/src:/app/services/apidocs/src
ENV SKIP_COMPOSE=1

WORKDIR /app/_test

# Default command runs all integration tests
CMD ["pytest", "integration/", "-v", "--tb=short"]
