# Identity Service - Configuration Migration Example

## Before (Using ENV Variables)

```python
# identity/src/identity.py
import os

# Database configuration
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "strategos")
DB_PASS = os.getenv("DB_PASS", "password")
DB_NAME = os.getenv("DB_NAME", "strategos_db")

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "default_secret")
TOKEN_EXPIRY = int(os.getenv("TOKEN_EXPIRY", "3600"))

# Build connection URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
```

## After (Using Config Files with Fallback)

### Step 1: Create config_loader.py wrapper

```python
# identity/src/config_loader.py
"""
Configuration wrapper with backward compatibility
"""
try:
    from common.config import get_config, get_db_config, get_jwt_secret
    USE_CONFIG_FILE = True
except ImportError:
    USE_CONFIG_FILE = False

class IdentityConfig:
    def __init__(self):
        if USE_CONFIG_FILE:
            self._load_from_config()
        else:
            self._load_from_env()
    
    def _load_from_config(self):
        config = get_config()
        db = get_db_config("postgres")
        
        self.DB_HOST = db["host"]
        self.DB_PORT = db["port"]
        self.DB_USER = db["user"]
        self.DB_PASS = db["password"]
        self.DB_NAME = db["database"]
        
        self.JWT_SECRET = get_jwt_secret()
        self.TOKEN_EXPIRY = config.get("security.jwt.access_token_expire_minutes", 30) * 60
    
    def _load_from_env(self):
        import os
        self.DB_HOST = os.getenv("DB_HOST", "postgres")
        self.DB_PORT = int(os.getenv("DB_PORT", "5432"))
        # ... etc
    
    @property
    def database_url(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

config = IdentityConfig()
```

### Step 2: Update identity.py to use wrapper

```python
# identity/src/identity.py
from config_loader import config

# Now use config instead of os.getenv()
DATABASE_URL = config.database_url
JWT_SECRET = config.JWT_SECRET
TOKEN_EXPIRY = config.TOKEN_EXPIRY

# Initialize database
async def init_db():
    return await asyncpg.create_pool(config.database_url)
```

## Migration Process

### Phase 1: Add Config Support (Backward Compatible)
✅ Services work with both ENV and config files
✅ No breaking changes
✅ Can test gradually

```bash
# Still works with ENV
DB_HOST=postgres docker compose up

# Also works with config files
DIGIDIG_ENV=prod docker compose up
```

### Phase 2: Update Services One by One
1. Identity service ✅
2. SMTP service
3. Storage service
4. IMAP service
5. Admin service
6. Client service

### Phase 3: Remove ENV Fallback (Future)
Once all services migrated and tested, remove ENV fallback code.

## Testing Migration

```bash
# Test with config files
make rebuild identity
docker compose up identity

# Verify it's using config
docker compose logs identity | grep "Using YAML"

# Test backward compatibility
docker compose down
docker compose up  # Should work with dev config
```

## Benefits

1. **Gradual Migration**: Services can be migrated one at a time
2. **No Downtime**: Backward compatible during transition
3. **Easy Rollback**: If issues occur, still works with ENV
4. **Clear Path**: Documented migration steps
5. **Testable**: Can verify each service individually
