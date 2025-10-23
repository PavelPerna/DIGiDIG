# DIGiDIG Project

## Configuration Management

**⚠️ NEW: Configuration now uses YAML files instead of environment variables!**

See [Configuration Documentation](docs/CONFIGURATION.md) for detailed guide.

### Quick Start

1. **Development** (uses default config):
   ```bash
   make install
   docker compose up
   ```

2. **Production** (customize config):
   ```bash
   # Copy and edit production config
   cp config/config.prod.example.yaml config/config.prod.yaml
   # Edit config/config.prod.yaml with your values
   
   # Set environment
   export DIGIDIG_ENV=prod
   
   # Start services
   docker compose up
   ```

### Configuration Files

```
config/
├── config.yaml                 # Default (development) config
├── config.prod.example.yaml    # Production template
├── config.test.yaml            # Test environment
└── config.local.yaml           # Local overrides (git-ignored)
```

**Benefits over ENV variables:**
- ✅ Centralized configuration
- ✅ Hierarchical structure (YAML)
- ✅ Type safety (integers, booleans, lists)
- ✅ Better secrets management (separate files)
- ✅ Easy validation and documentation

See [Migration Guide](docs/CONFIG-MIGRATION.md) for migration from ENV variables.

## Security Notes

### Identity Service

The identity service has been updated to remove hardcoded admin credentials and improve security:

1. Admin User Creation
   - No more hardcoded admin credentials in the code
   - Admin user is now created via `identity/scripts/create_admin.py` during installation
   - Required environment variables:
     - `ADMIN_EMAIL` - Email for admin account
     - `ADMIN_PASSWORD` - Password for admin account
   - Example usage:

     ```bash
     ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=secure123 python3 scripts/create_admin.py
     ```

2. JWT Security
   - JWT tokens are used for authentication
   - The secret key can be customized via `JWT_SECRET` environment variable
   - Example in docker-compose.yml:

     ```yaml
     environment:
       - JWT_SECRET=your_secure_secret_here  # Change this in production!
     ```

3. Default Values & Security
   - The system includes fallback values for development, but all sensitive values should be overridden in production:
     - Database credentials
     - JWT secret
     - Admin credentials

### Database Security

1. PostgreSQL
   - Credentials configurable via environment variables:
     - `DB_USER`
     - `DB_PASS`
     - `DB_NAME`
     - `DB_HOST`
   - Default values are for development only

## Installation

These steps will set up the project with secure configuration:

1. Configure environment variables by creating `.env` file:

   ```env
   DB_USER=your_db_user
   DB_PASS=your_db_password
   DB_NAME=your_db_name
   JWT_SECRET=your_jwt_secret
   ADMIN_EMAIL=your_admin@example.com
   ADMIN_PASSWORD=your_secure_admin_password
   ```

1. Run the installation:

   ```bash
   make install
   ```

1. Start the services:

   ```bash
   docker compose up
   ```

## Security Best Practices

1. Always change default credentials in production
2. Use strong passwords and secrets
3. Keep environment variables secure and never commit them to version control
4. Regularly rotate JWT secrets and admin credentials

## Testing

The project includes comprehensive integration and unit tests located in `tests/integration/`.

### Running Tests

Tests run in a dedicated Docker container to ensure consistency:

```bash
# Run all tests
make test

# Build test container only
make test-build

# Run all tests with fresh installation
make test-all
```

### Available Tests

- **Identity Tests** (`test_identity_integration.py`, `test_identity_unit.py`)
  - Domain CRUD operations
  - User management
  - Authentication flows
  
- **SMTP/IMAP Tests** (`test_smtp_imap_flow.py`)
  - Local delivery mechanism
  - Email sending via SMTP protocol
  - Email sending via REST API
  - Complete email flow (SMTP → Storage → IMAP)
  - External domain handling

### Test Structure

```
tests/
├── Dockerfile              # Test container definition
├── requirements-test.txt   # Test dependencies
└── integration/
    ├── test_identity_integration.py  # Identity integration tests
    ├── test_identity_unit.py         # Identity unit tests
    └── test_smtp_imap_flow.py        # Email flow tests
```

### Test Results

Example test run:
```
✅ 9 passed in 3.90s
   - 2 Identity integration tests
   - 2 Identity unit tests
   - 5 SMTP/IMAP flow tests
⚠️  1 warning (deprecation in identity.py)
```

All tests run in isolated Docker container with access to service network.
