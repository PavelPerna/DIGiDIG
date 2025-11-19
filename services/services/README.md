# DIGiDIG Services Manager

This service provides a REST API to manage, monitor, and restart DIGiDIG services using Docker Compose and Makefile targets.

## Installation

### As a Python Package
```bash
pip install -e .
```

### Dependencies
- `digidig-core>=1.0.0` - Shared DIGiDIG infrastructure
- `fastapi>=0.104.0` - Web framework
- `uvicorn[standard]>=0.24.0` - ASGI server
- `pydantic>=2.5.0` - Data validation

## Usage

### As a package
```bash
digidig-services
```

### As a module
```python
from main import main
main()
```

### Configuration
The service uses the DIGiDIG configuration system. Key settings:
- `services.services.http_port` - Service port (default: 9120)

---

# DIGiDIG Services Manager

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
