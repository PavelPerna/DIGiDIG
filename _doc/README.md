# DIGiDIG Project

[![CI Status](https://github.com/YOUR_USERNAME/DIGiDIG/workflows/CI/badge.svg)](https://github.com/YOUR_USERNAME/DIGiDIG/actions/workflows/ci.yml)
[![CD Status](https://github.com/YOUR_USERNAME/DIGiDIG/workflows/CD/badge.svg)](https://github.com/YOUR_USERNAME/DIGiDIG/actions/workflows/cd.yml)
[![Security Scan](https://github.com/YOUR_USERNAME/DIGiDIG/workflows/Security%20Scan/badge.svg)](https://github.com/YOUR_USERNAME/DIGiDIG/security)

**Distributed Email System with Multi-Language Support, Comprehensive API Documentation & Full CI/CD Pipeline**

## 🌟 Features

- **🚀 Full CI/CD Pipeline**: Automated building, deployment with GitHub Actions
- **🐳 Container Registry**: Docker images automatically built and published to GHCR
- **🌍 Multi-Environment**: Staging and production deployment automation
- **🔄 Health Monitoring**: Comprehensive health checks and automated rollback
- **🌐 Multi-Language Support (i18n)**: English and Czech with easy extensibility
- **📚 Comprehensive API Documentation**: Interactive Swagger UI and ReDoc for all services
- **🏗️ Microservices Architecture**: Identity, Storage, SMTP, IMAP, Mail, Admin
- **⚖️ Load-Balanced Reverse Proxy**: Distributed connection handling across multiple ports
- **🔐 JWT Authentication**: Secure token-based authentication
- **⚙️ YAML Configuration**: Centralized, type-safe configuration management
- **🐳 Docker-Based Deployment**: Easy setup with Docker Compose
- **💊 Service Health Monitoring**: Real-time status of all services
- **👥 Role-Based Access Control**: Admin and user roles

## 📚 Documentation

### Development & Workflow
- **[Delegation Guide](_doc/DELEGATION-GUIDE.md)** - Understanding GitHub Copilot delegation & custom agents

### CI/CD & Deployment
- **[CI/CD Pipeline](_doc/CI-CD.md)** - Complete CI/CD automation guide

### Localization & APIs
- **[Localization Guide](_doc/LOCALIZATION.md)** - Multi-language support
- **[API Documentation](_doc/API-DOCUMENTATION.md)** - Complete API reference
- **[API Endpoints Reference](_doc/API-ENDPOINTS.md)** - REST API endpoint structure & examples

### Configuration
- **[Configuration Guide](_doc/CONFIGURATION.md)** - YAML configuration system
- **[Migration Guide](_doc/CONFIG-MIGRATION.md)** - Migrate from ENV to YAML

## 🚀 Quick Start

### Development Environment

1. **Local Development** (uses default config):
   ```bash
   make install
   docker compose up
   ```

2. **Production Deployment** (customize config):
   ```bash
   # Copy and edit production config
   cp config/config.prod.example.yaml config/config.prod.yaml
   # Edit config/config.prod.yaml with your values
   
   # Set environment
   export DIGIDIG_ENV=prod
   
   # Start services
   docker compose up
   ```

### CI/CD Automated Deployment

The project includes a complete CI/CD pipeline for automated deployment:

```bash
# Trigger staging deployment
git push origin main

# Trigger production deployment
git tag v1.2.3
git push origin v1.2.3
```

**📖 See [CI/CD Pipeline Documentation](docs/CI-CD.md) for complete automation guide.**

### Health Monitoring

Check service health across environments:

```bash
# Local environment
./scripts/deployment/health-check.sh local

# Production with details
./scripts/deployment/health-check.sh production --details
```

## 🌐 Services & Load Balancing

DIGiDIG uses **load-balanced reverse proxies** for optimal scalability:

### Production Access (Load Balanced)
| Service Group | Port | Services | Access URLs |
|---------------|------|----------|-------------|
| **Core** | 443 | Admin, SSO, Identity | `https://admin.digidig.cz`, `https://sso.digidig.cz`, `https://identity.digidig.cz` |
| **Communication** | 444 | SMTP, IMAP, Mail | `https://smtp.digidig.cz:444`, `https://imap.digidig.cz:444`, `https://mail.digidig.cz:444` |
| **Data & API** | 445 | Storage, Client, API Docs, Test Suite, Services | `https://storage.digidig.cz:445`, `https://client.digidig.cz:445`, `https://apidocs.digidig.cz:445` |

### Development Access (Direct)
| Service | Internal Port | Description | Documentation |
|---------|---------------|-------------|---------------|
| **Identity** | 9101 | Authentication & user management | [Swagger](http://localhost:9110/docs/identity) |
| **Storage** | 9102 | Email storage & retrieval | [Swagger](http://localhost:9110/docs/storage) |
| **SMTP** | 9100 | Email sending service | [Swagger](http://localhost:9110/docs/smtp) |
| **IMAP** | 9103 | Email retrieval protocol | [Swagger](http://localhost:9110/docs/imap) |
| **Mail** | 9107 | Web-based email client | [Swagger](http://localhost:9110/docs/mail) |
| **Admin** | 9105 | Administration panel | [Swagger](http://localhost:9110/docs/admin) |
| **Test Suite** | 9108 | Automated test runner | [Swagger](http://localhost:9110/docs/test-suite) |
| **API Docs** | 9110 | **API Documentation Hub** | [Open](http://localhost:9110) |

## 🎨 Multi-Language Support

DIGiDIG supports multiple languages with easy language switching:

- **Supported Languages**: English (en), Czech (cs)
- **Language Selector**: Available in all web interfaces
- **Persistent Preference**: Language choice saved in cookies
- **Easy Extension**: Add new languages by creating translation files

See [Localization Guide](docs/LOCALIZATION.md) for details.

## 📖 API Documentation

Access comprehensive API documentation at **http://localhost:9110**

Features:
- **Interactive API**: Try APIs directly in the browser
- **Service Health**: Real-time status monitoring
- **Combined Specs**: View all APIs in one place
- **Swagger UI & ReDoc**: Choose your preferred format

### API Endpoint Structure

All REST API endpoints follow consistent structure under `/api/`:

```
/api/{service}/{resource}/{id}/{sub-resource}
```

**Examples:**
- `/api/identity/register` - User registration
- `/api/identity/users/{username}/preferences` - User preferences
- `/api/smtp/send` - Send email
- `/api/storage/emails` - List emails

**Client Services** (mail, admin, client, sso, test-suite) have built-in proxy at `/api/{service}/*` that routes to backend services.

**📖 See [API Endpoints Reference](_doc/API-ENDPOINTS.md) for complete endpoint listing.**

**📖 See [API Documentation Guide](_doc/API-DOCUMENTATION.md) for interactive API details.**

## ⚙️ Configuration Management

**⚠️ YAML Configuration System**

Configuration uses YAML files instead of environment variables:

### Configuration Files

```
config/
├── config.yaml                 # Default (development) config
├── config.prod.example.yaml    # Production template
└── config.local.yaml           # Local overrides (git-ignored)
```

**Benefits over ENV variables:**
- ✅ Centralized configuration
- ✅ Hierarchical structure (YAML)
- ✅ Type safety (integers, booleans, lists)
- ✅ Better secrets management (separate files)
- ✅ Easy validation and documentation

See [Configuration Guide](docs/CONFIGURATION.md) and [Migration Guide](docs/CONFIG-MIGRATION.md).

## 🔒 Security Notes

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

## 🚀 CI/CD Pipeline

DIGiDIG includes a comprehensive CI/CD pipeline with GitHub Actions:

### Continuous Integration
- **Code Quality**: Black, isort, Flake8 validation
- **Security Scanning**: Trivy vulnerability scanning with GitHub Security integration

### Continuous Deployment
- **Docker Registry**: Automatic image builds and push to GitHub Container Registry (GHCR)
- **Multi-Environment**: Staging (automatic) and production (manual approval) deployments
- **Health Checks**: Post-deployment validation with automatic rollback

### Container Images

All services are available as Docker images:

```bash
# Pull specific service
docker pull ghcr.io/YOUR_USERNAME/digidig-identity:latest
docker pull ghcr.io/YOUR_USERNAME/digidig-client:latest

# Available services: identity, storage, smtp, imap, mail, admin, apidocs
```

### Deployment Automation

```bash
# Deploy to staging
./scripts/deployment/deploy.sh staging main

# Deploy to production with backup and rollback
./scripts/deployment/deploy.sh production v1.2.3

# Health monitoring
./scripts/deployment/health-check.sh production
```

**📖 Complete CI/CD documentation: [CI/CD Pipeline Guide](docs/CI-CD.md)**
