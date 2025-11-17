# REST API Documentation - DIGiDIG Services

## Overview
This document describes the REST API endpoints added to all DIGiDIG services (SMTP, IMAP, Storage, Identity) for service management and monitoring.

## Common Endpoints (All Services)

### Health Check
**Endpoint:** `GET /api/health`  
**Description:** Returns the health status of the service  
**Authentication:** None required  
**Response:**
```json
{
  "service_name": "smtp",
  "status": "healthy|unhealthy|degraded",
  "timestamp": "2025-10-23T15:30:00.000Z",
  "uptime_seconds": 3600.5,
  "details": {
    "enabled": true,
    "controller_running": true
  }
}
```

### Get Configuration
**Endpoint:** `GET /api/config`  
**Description:** Returns the current service configuration  
**Authentication:** None required  
**Response:**
```json
{
  "service_name": "smtp",
  "config": {
    "hostname": "0.0.0.0",
    "port": 8000,
    "max_workers": 4,
    "pool_size": 10,
    "enabled": true,
    "timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 2
  }
}
```

### Update Configuration
**Endpoint:** `PUT /api/config`  
**Description:** Updates service configuration (admin only for Identity)  
**Authentication:** Bearer token (admin role for Identity service)  
**Request Body:**
```json
{
  "max_workers": 8,
  "pool_size": 20,
  "timeout": 60
}
```
**Response:**
```json
{
  "status": "success",
  "message": "Configuration updated",
  "config": { ... }
}
```

### Get Statistics
**Endpoint:** `GET /api/stats`  
**Description:** Returns service statistics and metrics  
**Authentication:** None required  
**Response:**
```json
{
  "service_name": "smtp",
  "uptime_seconds": 3600.5,
  "requests_total": 1500,
  "requests_successful": 1450,
  "requests_failed": 50,
  "last_request_time": "2025-10-23T15:30:00.000Z",
  "custom_stats": {
    "queue_length": 5,
    "max_queue_size": 100,
    "max_workers": 4
  }
}
```

## SMTP Service Specific Endpoints

### Get SMTP Status
**Endpoint:** `GET /api/smtp/status`  
**Description:** Returns SMTP server status  
**Response:**
```json
{
  "controller_running": true,
  "hostname": "0.0.0.0",
  "port": 8000,
  "auth_required": true,
  "enabled": true
}
```

### Restart SMTP Server
**Endpoint:** `POST /api/smtp/restart`  
**Description:** Restarts the SMTP server  
**Response:**
```json
{
  "status": "success",
  "message": "SMTP server restarted"
}
```

### Get Email Queue
**Endpoint:** `GET /api/smtp/queue`  
**Description:** Returns email queue status  
**Response:**
```json
{
  "queue_length": 5,
  "max_queue_size": 100,
  "emails": [
    {
      "sender": "user@example.com",
      "recipient": "admin@example.com",
      "subject": "Test",
      "timestamp": "2025-10-23T15:30:00.000Z"
    }
  ]
}
```

## IMAP Service Specific Endpoints

### Get Active Connections
**Endpoint:** `GET /api/imap/connections`  
**Description:** Returns active IMAP connections  
**Response:**
```json
{
  "active_connections": [],
  "count": 0,
  "max_connections": 50
}
```

### Get Active Sessions
**Endpoint:** `GET /api/imap/sessions`  
**Description:** Returns active IMAP sessions  
**Response:**
```json
{
  "active_sessions": [
    {
      "session_id": "user1_1729695000",
      "user_id": "user1",
      "started_at": "2025-10-23T15:30:00.000Z"
    }
  ],
  "count": 1
}
```

## Storage Service Specific Endpoints

### Get Storage Statistics
**Endpoint:** `GET /api/storage/stats`  
**Description:** Returns detailed storage statistics  
**Response:**
```json
{
  "total_emails": 1500,
  "database": "strategos",
  "collections": ["emails"],
  "storage_size_bytes": 10485760,
  "index_size_bytes": 102400,
  "total_size_bytes": 10588160
}
```

## Identity Service Specific Endpoints

### Get Active Sessions
**Endpoint:** `GET /api/identity/sessions`  
**Description:** Returns active identity sessions (admin only)  
**Authentication:** Bearer token (admin role required)  
**Response:**
```json
{
  "active_sessions": [
    {
      "username": "admin",
      "logged_in_at": "2025-10-23T15:30:00.000Z",
      "roles": ["admin"]
    }
  ],
  "count": 1
}
```

## Admin Service Endpoints

### Services Management Page
**Endpoint:** `GET /services`  
**Description:** Web UI for service management  
**Authentication:** Cookie-based or query token  

### Get Service Health
**Endpoint:** `GET /api/services/{service_name}/health`  
**Description:** Get health status of specific service  
**Parameters:** 
- `service_name`: smtp|imap|storage|identity

### Get Service Stats
**Endpoint:** `GET /api/services/{service_name}/stats`  
**Description:** Get statistics of specific service  
**Authentication:** Cookie-based token required  

### Get Service Config
**Endpoint:** `GET /api/services/{service_name}/config`  
**Description:** Get configuration of specific service  
**Authentication:** Cookie-based token required  

### Update Service Config
**Endpoint:** `PUT /api/services/{service_name}/config`  
**Description:** Update configuration of specific service  
**Authentication:** Cookie-based token required  
**Request Body:** JSON configuration object

### Restart SMTP Service
**Endpoint:** `POST /api/services/smtp/restart`  
**Description:** Restart SMTP service  
**Authentication:** Cookie-based token required  

## Configuration Model

All services support the following base configuration options:

```python
{
  "service_name": "string",
  "hostname": "string",           # Default: "0.0.0.0"
  "port": "integer",              # Service port
  "max_workers": "integer",       # Default: 4
  "pool_size": "integer",         # Default: 10
  "enabled": "boolean",           # Default: true
  "timeout": "integer",           # Default: 30
  "retry_attempts": "integer",    # Default: 3
  "retry_delay": "integer"        # Default: 2
}
```

### Service-Specific Configuration

**SMTP:**
- `auth_required`: boolean (default: true)
- `auth_require_tls`: boolean (default: false)
- `max_message_size`: integer (default: 10485760 - 10MB)
- `queue_size`: integer (default: 100)

**IMAP:**
- `max_connections`: integer (default: 50)
- `idle_timeout`: integer (default: 300)

**Storage:**
- `mongo_uri`: string (default: "mongodb://mongo:9302")
- `database_name`: string (default: "strategos")
- `max_document_size`: integer (default: 16777216 - 16MB)

**Identity:**
- `jwt_secret`: string (not exposed via API)
- `token_expiry`: integer (default: 3600)
- `refresh_token_expiry`: integer (default: 1209600 - 14 days)
- `db_host`: string (default: "postgres")
- `db_name`: string (default: "strategos")
- `db_user`: string

## Environment Variables

Services can be configured via environment variables:

### Common Variables
- `{SERVICE}_HOSTNAME`: Service hostname (e.g., SMTP_HOSTNAME)
- `{SERVICE}_PORT`: Service port
- `{SERVICE}_MAX_WORKERS`: Maximum worker threads
- `{SERVICE}_POOL_SIZE`: Connection pool size
- `{SERVICE}_TIMEOUT`: Request timeout
- `{SERVICE}_RETRY_ATTEMPTS`: Retry attempts
- `{SERVICE}_RETRY_DELAY`: Delay between retries

### SMTP Specific
- `SMTP_MAX_MESSAGE_SIZE`: Maximum message size in bytes
- `SMTP_QUEUE_SIZE`: Email queue size

### IMAP Specific
- `IMAP_MAX_CONNECTIONS`: Maximum concurrent connections
- `IMAP_IDLE_TIMEOUT`: Idle connection timeout

### Storage Specific
- `MONGO_URI`: MongoDB connection URI
- `STORAGE_MAX_DOC_SIZE`: Maximum document size

### Identity Specific
- `JWT_SECRET`: JWT secret key
- `TOKEN_EXPIRY`: Token expiry in seconds
- `REFRESH_TOKEN_EXPIRY`: Refresh token expiry in seconds

## Multithreading Implementation

### SMTP Service
- Uses `ThreadPoolExecutor` for email processing
- Configurable via `max_workers` parameter
- Email processing happens in separate threads
- Automatic retry mechanism with configurable attempts and delays

### IMAP Service
- Uses `ThreadPoolExecutor` for email fetching
- Configurable via `max_workers` parameter
- Session tracking for active connections
- Thread-safe email retrieval

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200 OK`: Success
- `400 Bad Request`: Invalid request
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses follow the format:
```json
{
  "error": "Error message",
  "detail": "Detailed error description"
}
```

## Testing

To test the API endpoints:

```bash
# Health check
curl http://localhost:8000/api/health

# Get configuration
curl http://localhost:8000/api/config

# Update configuration
curl -X PUT http://localhost:8000/api/config \
  -H "Content-Type: application/json" \
  -d '{"max_workers": 8}'

# Get statistics
curl http://localhost:8000/api/stats

# SMTP specific
curl http://localhost:8000/api/smtp/status
curl http://localhost:8000/api/smtp/queue
curl -X POST http://localhost:8000/api/smtp/restart
```

## Admin UI

The admin interface provides a web-based UI for managing all services:

1. Navigate to `http://admin:8004/services?token={your_token}`
2. View health status of all services
3. Click "Statistiky" to view service statistics
4. Click "Konfigurace" to view/edit service configuration
5. Click "Restart" to restart SMTP service (other services coming soon)

The UI automatically refreshes service status and provides real-time updates.
