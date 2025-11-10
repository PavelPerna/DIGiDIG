# DIGiDIG Base Docker Image

Base Docker image containing common Python dependencies shared across all DIGiDIG services.

Published to: `ghcr.io/pavelperna/digidig-base:latest`

## Purpose

Reduces build time and image size by:
- Installing common dependencies once in base image
- Service images only install service-specific packages
- Faster rebuilds when only service code changes
- Cached in GitHub Container Registry for CI/CD

## Common Dependencies Included

The base image includes packages used by most services:

- **fastapi** - Web framework (all services)
- **uvicorn** - ASGI server (all services)
- **aiohttp** - Async HTTP client (all services)
- **httpx** - Modern HTTP client (all services)
- **pydantic** - Data validation (10/11 services)
- **PyYAML** - Configuration parsing (10/11 services)
- **jinja2** - Template engine (6/11 services)
- **requests** - HTTP library (10/11 services)
- **python-multipart** - Form handling (6/11 services)

## Building

### Local build:

```bash
make build-base
```

### Pull from registry (faster):

```bash
make pull-base
```

### Push to registry (requires authentication):

```bash
docker login ghcr.io
make push-base
```

Or manually:

```bash
docker build -t digidig-base:latest -f docker/base/Dockerfile docker/base/
```

## Usage in Services

Service Dockerfiles inherit from the GHCR base image:

```dockerfile
FROM ghcr.io/pavelperna/digidig-base:latest

WORKDIR /app

# Copy shared libraries
COPY digidig/ ./digidig/
COPY config/ ./config/

# Install ONLY service-specific dependencies
COPY services/myservice/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY services/myservice/src/ .
```

## Service-Specific Dependencies

Each service's `requirements.txt` contains only packages NOT in the base image:

**identity:**
- asyncpg (PostgreSQL driver)
- pyjwt (JWT tokens)
- cryptography (encryption)

**storage:**
- pymongo (MongoDB driver)

**smtp:**
- aiosmtpd (SMTP server)

**sso:**
- cryptography (encryption)

etc.

## Benefits

1. **Faster Builds**: Base image cached, only service-specific deps installed per service
2. **Smaller Images**: Shared layers reduce total storage
3. **Consistency**: All services use same version of common dependencies
4. **Easier Updates**: Update common deps once in base image

## Maintenance

When updating common dependencies:

1. Update `docker/base/requirements-base.txt`
2. Commit and push to main branch
3. GitHub Actions automatically builds and pushes new base image
4. Pull updated image: `make pull-base`
5. Rebuild services: `make build`

For local testing before pushing:
1. Update `docker/base/requirements-base.txt`
2. Build locally: `make build-base`
3. Test with a service: `docker compose build <service>`
4. If OK, push to registry: `make push-base`

Version pinning ensures reproducible builds.

## CI/CD Integration

- Base image is automatically built and pushed to GHCR on changes to `docker/base/**`
- All service builds pull latest base image from GHCR
- No need to rebuild base image locally unless developing/testing changes
