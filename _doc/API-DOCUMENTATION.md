# API Documentation System

## Overview

DIGiDIG provides comprehensive REST API documentation through a dedicated API Documentation Service. This service aggregates OpenAPI specifications from all microservices and presents them in an intuitive, unified interface.

## Access

**API Documentation Portal**: http://localhost:8010

## Features

### 1. Unified Documentation Hub

- **Service Overview**: Visual cards for each microservice
- **Health Monitoring**: Real-time service status indicators
- **Quick Navigation**: Direct links to Swagger UI and ReDoc for each service

### 2. Interactive Documentation

#### Swagger UI
- Interactive API testing
- Request/response examples
- Schema exploration
- Try-it-out functionality

#### ReDoc
- Clean, readable format
- Comprehensive schema documentation
- Searchable interface
- Code samples

### 3. Combined API Specification

Access all services in a single OpenAPI document:
```
GET http://localhost:8010/api/openapi/combined
```

## Services Documented

### Identity Service (Port 8001)
- **Authentication**: Login, logout, token verification
- **Users**: CRUD operations for user management
- **Domains**: Multi-domain support

**Docs**: http://localhost:8010/docs/identity

### Storage Service (Port 8002)
- **Email Storage**: Store and retrieve emails
- **Folders**: Manage email folders
- **Search**: Find emails by criteria

**Docs**: http://localhost:8010/docs/storage

### SMTP Service (Port 8003)
- **Send Email**: SMTP protocol support
- **Queue Management**: Email delivery queue
- **Status Tracking**: Delivery status

**Docs**: http://localhost:8010/docs/smtp

### IMAP Service (Port 8007)
- **Email Retrieval**: IMAP protocol
- **Mailbox Operations**: List, select, manage mailboxes
- **Message Flags**: Read/unread status

**Docs**: http://localhost:8010/docs/imap

### Admin Service (Port 8005)
- **Service Management**: Start, stop, restart services
- **Monitoring**: System health and metrics
- **Configuration**: System settings

**Docs**: http://localhost:8010/docs/admin

## API Endpoints

### Documentation Service API

#### List All Services
```http
GET /api/services
```

Response:
```json
{
  "services": [
    {
      "id": "identity",
      "name": "Identity Service",
      "description": "User authentication and authorization",
      "url": "http://identity:8001",
      "icon": "🔐",
      "tags": ["Authentication", "Users", "Domains"]
    },
    ...
  ]
}
```

#### Get Service OpenAPI Spec
```http
GET /api/services/{service_id}/spec
```

Example:
```http
GET /api/services/identity/spec
```

#### Check Service Health
```http
GET /api/services/{service_id}/health
```

Response:
```json
{
  "status": "healthy",
  "message": "Service is running"
}
```

#### Get All Services Health
```http
GET /api/health
```

Response:
```json
{
  "services": {
    "identity": {
      "status": "healthy",
      "message": "Service is running"
    },
    "storage": {
      "status": "healthy",
      "message": "Service is running"
    },
    ...
  },
  "overall": "healthy"
}
```

#### Get Combined OpenAPI Spec
```http
GET /api/openapi/combined
```

Returns a unified OpenAPI 3.0 specification combining all services.

## Using the Documentation

### 1. Browse Services

Visit http://localhost:8010 to see all available services with:
- Service description
- Health status (green = healthy, red = down)
- Quick links to documentation

### 2. Explore APIs

Click "Swagger UI" or "ReDoc" for any service to:
- See all available endpoints
- View request/response schemas
- Read detailed descriptions
- See example payloads

### 3. Test APIs Interactively

In Swagger UI:

1. **Select an endpoint** to expand details
2. **Click "Try it out"**
3. **Fill in parameters** (path, query, body)
4. **Add Authorization header** if needed:
   ```
   Authorization: Bearer your-jwt-token
   ```
5. **Click "Execute"**
6. **View the response**

### 4. Authentication

Most endpoints require JWT authentication:

1. **Get Token**: Call `/login` on Identity service
   ```bash
   curl -X POST http://localhost:8001/login \
     -H "Content-Type: application/json" \
     -d '{
       "username": "admin",
       "domain": "example.com",
       "password": "your-password"
     }'
   ```

2. **Use Token**: Add to Authorization header
   ```bash
   curl -X GET http://localhost:8002/emails \
     -H "Authorization: Bearer your-jwt-token"
   ```

## OpenAPI Metadata

All services provide rich OpenAPI metadata:

### Service Information
- Title and description
- Version number
- Contact information
- License

### Endpoint Documentation
- Operation summary
- Detailed description
- Parameters (path, query, body)
- Request body schemas
- Response schemas
- Example payloads
- Security requirements

### Tags and Organization
Endpoints are grouped by tags:
- **Authentication**: Login, logout, verify
- **Users**: User CRUD operations
- **Emails**: Email operations
- **Admin**: Administrative functions

## Development

### Adding New Service

1. **Create Service**: Develop FastAPI application
2. **Add OpenAPI Metadata**: Use FastAPI decorators
3. **Register in apidocs**: Update `SERVICES` dict in `apidocs.py`
4. **Update docker-compose**: Add service configuration

Example service registration:

```python
SERVICES = {
    "new_service": {
        "name": "New Service",
        "description": "Description of new service",
        "url": "http://new_service:8020",
        "openapi_path": "/openapi.json",
        "icon": "🆕",
        "tags": ["Tag1", "Tag2"]
    }
}
```

### Enhancing Endpoint Documentation

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(
    title="Service Name",
    description="Detailed service description",
    version="1.0.0"
)

class User(BaseModel):
    username: str = Field(..., description="User's login name", example="john_doe")
    email: str = Field(..., description="User's email address", example="john@example.com")

@app.post(
    "/users",
    summary="Create new user",
    description="Create a new user account with the provided information",
    response_description="Newly created user object",
    tags=["Users"],
    responses={
        201: {
            "description": "User created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123",
                        "username": "john_doe",
                        "email": "john@example.com"
                    }
                }
            }
        },
        400: {"description": "Invalid input"},
        409: {"description": "User already exists"}
    }
)
async def create_user(user: User):
    """
    Create a new user with all the details:
    
    - **username**: Unique username (3-50 characters)
    - **email**: Valid email address
    - **password**: Strong password (min 8 characters)
    """
    pass
```

## Health Monitoring

The API docs service monitors health of all services:

- **Real-time status**: Updated every 30 seconds
- **Visual indicators**: 
  - 🟢 Green = Healthy
  - 🔴 Red = Unhealthy/Down
  - 🟠 Orange = Unreachable

## Examples

### Get All Emails (Storage Service)

```bash
curl -X GET "http://localhost:8002/emails" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Send Email (SMTP Service)

```bash
curl -X POST "http://localhost:8003/send" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "sender": "user@example.com",
    "recipient": "recipient@example.com",
    "subject": "Test Email",
    "body": "This is a test email"
  }'
```

### Create User (Identity Service)

```bash
curl -X POST "http://localhost:8001/users" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "domain": "example.com",
    "password": "SecurePass123"
  }'
```

### Restart Service (Admin Service)

```bash
curl -X POST "http://localhost:8005/api/services/smtp/restart" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

## Best Practices

### For API Consumers

1. **Read the docs first**: Understand endpoints before integration
2. **Use examples**: Copy-paste working examples
3. **Handle errors**: Check response status codes
4. **Authentication**: Always include valid JWT token
5. **Rate limiting**: Respect service limits

### For API Developers

1. **Document everything**: Every endpoint, parameter, response
2. **Provide examples**: Real-world request/response examples
3. **Describe errors**: Document all possible error responses
4. **Use tags**: Group related endpoints
5. **Version APIs**: Use semantic versioning

## Troubleshooting

### Service Not Showing in Docs

1. Check service is running: `docker ps`
2. Verify OpenAPI endpoint: `curl http://service:port/openapi.json`
3. Check service registration in `apidocs.py`
4. Review logs: `docker logs apidocs`

### Cannot Test API in Swagger

1. **CORS issues**: Ensure service allows requests from docs service
2. **Authentication**: Get valid JWT token first
3. **Network**: Services must be on same Docker network
4. **URL**: Check service URL in environment variables

### Spec Not Loading

1. Service must expose `/openapi.json` endpoint
2. FastAPI auto-generates this (enabled by default)
3. Check service health: http://localhost:8010/api/health
4. View raw spec: http://localhost:8010/api/services/SERVICE_ID/spec

## References

- [OpenAPI Specification](https://swagger.io/specification/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Swagger UI](https://swagger.io/tools/swagger-ui/)
- [ReDoc](https://redocly.com/redoc)

## Future Enhancements

- [ ] API versioning support
- [ ] Rate limiting documentation
- [ ] Authentication flow diagrams
- [ ] Code generation (client SDKs)
- [ ] API testing suite
- [ ] Performance metrics
- [ ] Changelog tracking
- [ ] Deprecation notices
