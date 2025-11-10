# DIGiDIG Services Manager

This service provides a REST API to manage, monitor, and restart DIGiDIG services using Docker Compose and Makefile targets.

## Endpoints
- `GET /services` — List all services
- `GET /services/{service_name}` — Get service details
- `GET /services/{service_name}/status` — Get service status (docker compose ps)
- `POST /services/{service_name}/restart` — Restart a service (via Makefile target)

## Models
- `ServiceBaseModel` — Base model for all services
- `ServiceModel` — Derived for backend services
- `ClientAppModel` — Derived for client apps

## Usage
Build and run:
```bash
docker build -t digidig-services ./services/services
# Or with compose:
docker compose up -d services
```

## Configuration
- Exposes port 9120 by default
- Requires Docker and Makefile in project root
