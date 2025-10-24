# Configuration Management

## Overview

DIGiDIG uses YAML-based configuration files instead of environment variables for better:
- **Maintainability**: All settings in one place
- **Validation**: YAML syntax checking
- **Version Control**: Easy to track changes
- **Environment Management**: Separate configs for dev/test/prod
- **Type Safety**: Structured configuration with clear hierarchy

## Configuration Files

```
config/
├── config.yaml                 # Main configuration (development defaults)
├── config.prod.example.yaml    # Production template (copy & customize)
├── config.test.yaml            # Test environment overrides
└── config.local.yaml           # Local overrides (git-ignored)
```

## Usage in Services

### Basic Usage

```python
from common.config import get_config

config = get_config()

# Access values using dot notation
db_host = config.get("database.postgres.host")
jwt_secret = config.get("security.jwt.secret")
smtp_url = config.get("services.smtp.rest_url")
```

### Convenience Functions

```python
from common.config import (
    get_db_config,
    get_service_url,
    get_jwt_secret,
    get_admin_credentials
)

# Get entire database config
db_config = get_db_config("postgres")
# Returns: {"host": "postgres", "port": 5432, "user": "...", ...}

# Get service URL
storage_url = get_service_url("storage")
# Returns: "http://storage:8002"

# Get JWT secret
secret = get_jwt_secret()

# Get admin credentials
admin = get_admin_credentials()
# Returns: {"email": "admin@example.com", "password": "..."}
```

## Environment-Specific Configuration

Set `DIGIDIG_ENV` environment variable to load environment-specific overrides:

```bash
# Development (default)
DIGIDIG_ENV=dev python app.py

# Testing
DIGIDIG_ENV=test python app.py

# Production
DIGIDIG_ENV=prod python app.py
```

The system loads configs in this order:
1. `config.yaml` (base configuration)
2. `config.{env}.yaml` (environment override)
3. `config.local.yaml` (local overrides, if exists)

## Configuration Structure

### Database Configuration
```yaml
database:
  postgres:
    host: postgres
    port: 5432
    user: strategos
    password: secure_password
    database: strategos_db
  
  mongodb:
    host: mongo
    port: 27017
    database: strategos_storage
```

### Service URLs
```yaml
services:
  identity:
    url: http://identity:8001
  smtp:
    rest_url: http://smtp:8000
  storage:
    url: http://storage:8002
  # ... other services
```

### Security Settings
```yaml
security:
  jwt:
    secret: "your_secret_here"
    algorithm: HS256
    access_token_expire_minutes: 30
  
  admin:
    email: "admin@example.com"
    password: "secure_password"
```

## Production Deployment

1. Copy production template:
   ```bash
   cp config/config.prod.example.yaml config/config.prod.yaml
   ```

2. Edit `config/config.prod.yaml` with your values:
   - Change all passwords and secrets
   - Update domain names
   - Enable TLS/SSL settings
   - Set appropriate logging levels

3. Set environment:
   ```bash
   export DIGIDIG_ENV=prod
   ```

4. Keep `config.prod.yaml` secure (not in git):
   ```bash
   # Already in .gitignore
   config/config.prod.yaml
   config/config.local.yaml
   ```

## Migration from ENV Variables

Replace ENV variable access with config access:

### Before (ENV variables):
```python
import os

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_USER = os.getenv("DB_USER", "strategos")
JWT_SECRET = os.getenv("JWT_SECRET", "default")
```

### After (Config file):
```python
from common.config import get_config, get_db_config

config = get_config()
db = get_db_config("postgres")

DB_HOST = db["host"]
DB_USER = db["user"]
JWT_SECRET = config.get("security.jwt.secret")
```

## Testing

Test configuration is automatically loaded when `DIGIDIG_ENV=test`:

```python
# In tests
from common.config import load_config

config = load_config(env="test")
assert config.get("test.enabled") == True
```

## Validation

Add validation in your service startup:

```python
from common.config import get_config

config = get_config()

# Validate required settings
required_keys = [
    "database.postgres.host",
    "security.jwt.secret",
    "services.storage.url"
]

for key in required_keys:
    value = config.get(key)
    if not value:
        raise ValueError(f"Missing required configuration: {key}")
```

## Best Practices

1. **Never commit secrets**: Use `config.prod.yaml` and `config.local.yaml` (git-ignored)
2. **Use strong defaults**: Development config should work out-of-box
3. **Document changes**: Update `config.prod.example.yaml` when adding new options
4. **Validate on startup**: Check required configuration keys exist
5. **Use type hints**: Access config values with clear types
6. **Environment separation**: Keep dev/test/prod configs separate

## Advantages over ENV Variables

| Aspect | ENV Variables | Config Files |
|--------|--------------|--------------|
| Organization | Scattered across docker-compose | Centralized in YAML |
| Validation | None | YAML syntax checking |
| Type Safety | Strings only | Structured data |
| Defaults | Hardcoded in code | In config file |
| Documentation | Inline comments only | Structured sections |
| Secrets Management | Exposed in docker-compose | External file (git-ignored) |
| Change Tracking | Difficult | Easy with git |
| Testing | Override each ENV var | Single config override |
