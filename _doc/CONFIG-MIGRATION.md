# Configuration Migration Guide

## Comparison: ENV Variables vs Config Files

### Example: Identity Service Configuration

#### OLD WAY - Environment Variables (docker-compose.yml)

```yaml
services:
  identity:
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_USER=strategos
      - DB_PASS=strategos_password
      - DB_NAME=strategos_db
      - JWT_SECRET=b8_XYZ123abc456DEF789ghiJKL0mnoPQ
      - ADMIN_EMAIL=admin@example.com
      - ADMIN_PASSWORD=admin
      - STORAGE_URL=http://storage:8002
      - SMTP_URL=http://smtp:8000
```

**In Python code:**
```python
import os

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "strategos")
DB_PASS = os.getenv("DB_PASS", "password")
DB_NAME = os.getenv("DB_NAME", "strategos_db")
JWT_SECRET = os.getenv("JWT_SECRET", "default_secret")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
```

#### NEW WAY - Config Files

**config/config.yaml:**
```yaml
database:
  postgres:
    host: postgres
    port: 5432
    user: strategos
    password: strategos_password
    database: strategos_db

security:
  jwt:
    secret: "b8_XYZ123abc456DEF789ghiJKL0mnoPQ"
  admin:
    email: "admin@example.com"
    password: "admin"

services:
  storage:
    url: http://storage:8002
  smtp:
    rest_url: http://smtp:8000
```

**In Python code:**
```python
from common import get_config, get_db_config

config = get_config()
db = get_db_config("postgres")

# Simple access
DB_HOST = db["host"]
DB_PORT = db["port"]
DB_USER = db["user"]
DB_PASS = db["password"]
DB_NAME = db["database"]

# Or build connection string
DATABASE_URL = f"postgresql://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}"

# Security settings
JWT_SECRET = config.get("security.jwt.secret")
admin = config.get_section("security.admin")
```

## Migration Steps

### 1. Install Dependencies

Add to service `requirements.txt`:
```
PyYAML>=6.0
```

### 2. Add Common Module Import

Update service Dockerfile:
```dockerfile
# Copy lib module
COPY lib/ /app/lib/

# Or add to Python path
ENV PYTHONPATH=/app:$PYTHONPATH
```

### 3. Update Service Code

Replace ENV access with config access:

```python
# Before
import os
SECRET = os.getenv("JWT_SECRET")

# After  
from common import get_jwt_secret
SECRET = get_jwt_secret()
```

### 4. Remove ENV Variables from docker-compose.yml

```yaml
# Before
services:
  identity:
    environment:
      - DB_HOST=postgres
      - JWT_SECRET=secret
      # ... 15 more variables

# After
services:
  identity:
    volumes:
      - ./config:/app/config:ro  # Mount config as read-only
    environment:
      - DIGIDIG_ENV=prod  # Only environment selector
```

### 5. Create Environment-Specific Configs

```bash
# Development (default)
config/config.yaml

# Production
cp config/config.prod.example.yaml config/config.prod.yaml
# Edit with production values

# Test
config/config.test.yaml
```

## Benefits Summary

| Aspect | ENV Variables | Config Files | Winner |
|--------|--------------|--------------|--------|
| **Maintainability** | Scattered across multiple files | Centralized in YAML | ✅ Config |
| **Readability** | Flat key=value | Hierarchical structure | ✅ Config |
| **Validation** | Runtime errors | YAML syntax checking | ✅ Config |
| **Documentation** | Comments in compose file | Structured sections | ✅ Config |
| **Secrets** | Exposed in compose | Separate file (git-ignored) | ✅ Config |
| **Type Safety** | Strings only | Typed values (int, bool, list) | ✅ Config |
| **Defaults** | Hardcoded in code | In config file | ✅ Config |
| **Testing** | Override many vars | One config file | ✅ Config |
| **Versioning** | Difficult to track | Git-friendly YAML | ✅ Config |
| **Complexity** | Simple key lookup | Requires config loader | ENV |

## Practical Examples

### Database Connection

**Before:**
```python
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "user")
DB_PASS = os.getenv("DB_PASS", "pass")
DB_NAME = os.getenv("DB_NAME", "db")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
```

**After:**
```python
from common import get_db_config

db = get_db_config("postgres")
DATABASE_URL = f"postgresql://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}"
```

### Service URLs

**Before:**
```python
IDENTITY_URL = os.getenv("IDENTITY_URL", "http://localhost:8001")
STORAGE_URL = os.getenv("STORAGE_URL", "http://localhost:8002")
SMTP_URL = os.getenv("SMTP_URL", "http://localhost:8000")
```

**After:**
```python
from common import get_service_url

IDENTITY_URL = get_service_url("identity")
STORAGE_URL = get_service_url("storage")
SMTP_URL = get_service_url("smtp").replace(":8000", ":8000")  # Or use smtp.rest_url
```

### JWT Configuration

**Before:**
```python
JWT_SECRET = os.getenv("JWT_SECRET", "default")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
TOKEN_EXPIRE = int(os.getenv("TOKEN_EXPIRE_MINUTES", "30"))
```

**After:**
```python
from common import get_config

config = get_config()
JWT_SECRET = config.get("security.jwt.secret")
JWT_ALGORITHM = config.get("security.jwt.algorithm")
TOKEN_EXPIRE = config.get("security.jwt.access_token_expire_minutes")
```

## Rollback Plan

If needed, you can support both approaches temporarily:

```python
from common import get_config
import os

# Try config first, fallback to ENV
try:
    config = get_config()
    DB_HOST = config.get("database.postgres.host")
except Exception:
    DB_HOST = os.getenv("DB_HOST", "postgres")
```

## Recommendations

1. ✅ **Use Config Files** for:
   - All application settings
   - Service URLs
   - Database connections
   - Security settings (JWT, passwords)
   - Feature flags
   - Logging configuration

2. ✅ **Keep ENV Variables** for:
   - Environment selector (`DIGIDIG_ENV=prod`)
   - Container-level settings (Docker only)
   - CI/CD pipeline variables

3. ✅ **Best Practices**:
   - Never commit `config.prod.yaml` or `config.local.yaml`
   - Use `config.prod.example.yaml` as template
   - Validate required config on startup
   - Document all config options
   - Use type hints in config access code
