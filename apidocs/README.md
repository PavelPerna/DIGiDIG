# API Documentation Service

Centralized API documentation hub for all DIGiDIG microservices.

## Overview

The API Documentation Service aggregates OpenAPI specifications from all DIGiDIG services and presents them through:

- **Interactive Swagger UI** - Test APIs in your browser
- **ReDoc Documentation** - Clean, readable API reference
- **Service Health Monitoring** - Real-time status of all services
- **Combined Specifications** - All services in one unified API spec

## Access

- **Main Portal**: http://localhost:8010
- **Individual Services**:
  - Identity: http://localhost:8010/docs/identity
  - Storage: http://localhost:8010/docs/storage
  - SMTP: http://localhost:8010/docs/smtp
  - IMAP: http://localhost:8010/docs/imap
  - Client: http://localhost:8010/docs/client
  - Admin: http://localhost:8010/docs/admin

## Features

### 1. Service Discovery

Visual cards showing:
- Service name and description
- Health status (real-time)
- Quick links to documentation
- Service tags

### 2. Interactive Documentation

**Swagger UI**:
- Try API endpoints directly
- View request/response schemas
- See example payloads
- Test with authentication

**ReDoc**:
- Clean documentation layout
- Comprehensive schema details
- Code samples
- Searchable content

### 3. Health Monitoring

Real-time health checks for all services:
- 🟢 Healthy - Service running normally
- 🔴 Unhealthy - Service error
- 🟠 Unreachable - Cannot connect

Auto-refreshes every 30 seconds.

### 4. Combined API Specification

Access unified OpenAPI spec:
```
GET http://localhost:8010/api/openapi/combined
```

Merges all service specifications into one document.

## API Endpoints

### List Services
```http
GET /api/services
```

Returns all registered services with metadata.

### Get Service Specification
```http
GET /api/services/{service_id}/spec
```

Returns OpenAPI 3.0 specification for a specific service.

### Check Service Health
```http
GET /api/services/{service_id}/health
```

Returns health status of a specific service.

### Get All Services Health
```http
GET /api/health
```

Returns health status of all services.

## Configuration

Service discovery via environment variables:

```env
IDENTITY_URL=http://identity:8001
STORAGE_URL=http://storage:8002
SMTP_URL=http://smtp:8000
IMAP_URL=http://imap:8003
CLIENT_URL=http://client:8004
ADMIN_URL=http://admin:8005
```

## Development

### Running Standalone

```bash
cd apidocs
pip install -r requirements.txt
python src/apidocs.py
```

Access at http://localhost:8010

### Docker

```bash
docker build -t apidocs -f apidocs/Dockerfile .
docker run -p 8010:8010 apidocs
```

### Adding New Service

Update `SERVICES` dict in `src/apidocs.py`:

```python
SERVICES = {
    "new_service": {
        "name": "New Service",
        "description": "Service description",
        "url": "http://new_service:8020",
        "openapi_path": "/openapi.json",
        "icon": "🆕",
        "tags": ["Tag1", "Tag2"]
    }
}
```

## Architecture

```
apidocs/
├── Dockerfile              # Docker image definition
├── requirements.txt        # Python dependencies
├── src/
│   ├── apidocs.py         # Main FastAPI application
│   └── templates/
│       ├── index.html     # Service overview page
│       ├── swagger.html   # Swagger UI template
│       └── redoc.html     # ReDoc template
└── README.md
```

## Technologies

- **FastAPI**: Web framework
- **aiohttp**: Async HTTP client for service discovery
- **Swagger UI**: Interactive API documentation
- **ReDoc**: Alternative documentation format
- **Jinja2**: Template engine

## Usage Examples

### View Service Documentation

1. Open http://localhost:8010
2. Click on a service card
3. Choose "Swagger UI" or "ReDoc"
4. Explore API endpoints

### Test an API

1. Open Swagger UI for a service
2. Expand an endpoint
3. Click "Try it out"
4. Fill in parameters
5. Add authentication if needed
6. Click "Execute"
7. View response

### Monitor Service Health

1. Open http://localhost:8010
2. Check colored dots on service cards:
   - Green = Healthy
   - Red = Down/Error
   - Orange = Unreachable
3. Health auto-updates every 30 seconds

## Troubleshooting

### Service Not Appearing

1. Check service is running: `docker ps`
2. Verify OpenAPI endpoint: `curl http://service:port/openapi.json`
3. Check environment variables in docker-compose.yml
4. View logs: `docker logs apidocs`

### Cannot Test APIs

1. Ensure services are on same Docker network
2. Check CORS configuration on target service
3. Verify authentication token is valid
4. Check service health status

### Spec Not Loading

1. Service must expose `/openapi.json`
2. FastAPI generates this automatically
3. Check service health: http://localhost:8010/api/health
4. View raw spec: http://localhost:8010/api/services/SERVICE_ID/spec

## See Also

- [API Documentation Guide](../docs/API-DOCUMENTATION.md)
- [OpenAPI Specification](https://swagger.io/specification/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Swagger UI](https://swagger.io/tools/swagger-ui/)
- [ReDoc](https://redocly.com/redoc)
