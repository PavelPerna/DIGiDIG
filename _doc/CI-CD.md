# CI/CD Pipeline Documentation

## Overview

DIGiDIG implements a CI/CD pipeline using GitHub Actions, providing automated building, deployment, and release management for all microservices.

## Architecture

The CI/CD system consists of two main workflows:

1. **Continuous Deployment (CD)** - Docker registry and deployment automation
2. **Release Management** - Automated releases with changelog generation

## Workflows

### 1. Continuous Deployment (.github/workflows/cd.yml)

**Triggers:**
- Pushes to `main` branch (staging deployment)
- Git tags matching `v*` pattern (production deployment)

**Jobs:**

#### Build and Push
- **Strategy:** Matrix build for all 7 services
- **Services:** identity, storage, smtp, imap, client, admin, apidocs
- **Registry:** GitHub Container Registry (GHCR)
- **Tagging:** 
  - `latest` for main branch
  - `${{ github.ref_name }}` for tagged releases
  - Short SHA for all builds

#### Deploy Staging
- **Trigger:** Automatic on main branch pushes
- **Environment:** staging
- **Health Checks:** Post-deployment validation
- **Notification:** Slack integration (optional)

#### Deploy Production
- **Trigger:** Manual approval required for tagged releases
- **Environment:** production
- **Safety:** Backup creation before deployment
- **Rollback:** Automatic on health check failure

#### Cleanup
- **Image Cleanup:** Removes old container images (keeps last 10)
- **Trigger:** Weekly schedule and after deployments

**Example Production Deploy:**
```bash
git tag v1.2.3
git push origin v1.2.3
# Triggers production deployment (requires manual approval)
```

### 2. Release Management (.github/workflows/release.yml)

**Triggers:**
- Git tags matching `v*` pattern

**Jobs:**

#### Create Release
- **Changelog:** Generated from commits since last tag
- **Assets:** References to Docker images in GHCR
- **Format:** Semantic versioning (v1.2.3)
- **Notes:** Automated release notes with commit details

#### Update Documentation
- **Version References:** Updates documentation with new version
- **Pull Request:** Creates automated PR for version updates
- **Files Updated:** README.md, docs/*.md

**Example Release Creation:**
```bash
git tag v1.2.3 -m "Release version 1.2.3"
git push origin v1.2.3
# Creates GitHub release with changelog
```

## Docker Registry

### GitHub Container Registry (GHCR)

All Docker images are stored in GitHub Container Registry with the following naming convention:

```
ghcr.io/YOUR_USERNAME/digidig-SERVICE:TAG
```

**Available Services:**
- `ghcr.io/YOUR_USERNAME/digidig-identity:latest`
- `ghcr.io/YOUR_USERNAME/digidig-storage:latest`
- `ghcr.io/YOUR_USERNAME/digidig-smtp:latest`
- `ghcr.io/YOUR_USERNAME/digidig-imap:latest`
- `ghcr.io/YOUR_USERNAME/digidig-client:latest`
- `ghcr.io/YOUR_USERNAME/digidig-admin:latest`
- `ghcr.io/YOUR_USERNAME/digidig-apidocs:latest`

**Tagging Strategy:**
- `latest` - Latest stable version from main branch
- `v1.2.3` - Specific release versions
- `sha-abc1234` - Specific commit builds

## Deployment Scripts

### Production Deployment (scripts/deployment/deploy.sh)

Comprehensive deployment automation with safety features:

```bash
# Deploy to staging
./scripts/deployment/deploy.sh staging main

# Deploy to production
./scripts/deployment/deploy.sh production v1.2.3
```

**Features:**
- **Environment Validation:** Ensures correct environment setup
- **Backup Creation:** PostgreSQL and MongoDB automatic backup
- **Health Checks:** Post-deployment service validation
- **Rollback:** Automatic rollback on deployment failure
- **Docker Management:** Image cleanup and optimization

**Safety Checks:**
- Production deployments require explicit version tags
- Backup verification before proceeding
- Health checks with timeout and retry logic
- Rollback triggers on any failure

### Health Monitoring (scripts/deployment/health-check.sh)

Standalone health monitoring for all environments:

```bash
# Quick health check
./scripts/deployment/health-check.sh local

# Detailed health information
./scripts/deployment/health-check.sh production --details
```

**Checks:**
- All 7 microservices availability
- API endpoints responsiveness
- Service health endpoints
- Critical functionality validation

## Environment Configuration

### Required Secrets

Configure these secrets in GitHub repository settings:

```bash
# GitHub Container Registry
REGISTRY_USERNAME=your-github-username
REGISTRY_PASSWORD=your-github-token

# Deployment (if using remote deployment)
DEPLOY_SSH_KEY=your-ssh-private-key
DEPLOY_HOST=your-production-server
DEPLOY_USER=deployment-user

# Notifications (optional)
SLACK_WEBHOOK=your-slack-webhook-url
```

### Environment Variables

**Staging Environment:**
```env
DIGIDIG_ENV=staging
DATABASE_URL=postgresql://staging_db
MONGODB_URL=mongodb://staging_mongo
```

**Production Environment:**
```env
DIGIDIG_ENV=production
DATABASE_URL=postgresql://prod_db
MONGODB_URL=mongodb://prod_mongo
```

## Monitoring and Notifications

### GitHub Actions Dashboard

Monitor workflow status at:
```
https://github.com/YOUR_USERNAME/DIGiDIG/actions
```

### Security Scanning Results

View security scan results at:
```
https://github.com/YOUR_USERNAME/DIGiDIG/security
```

### Container Registry

Manage container images at:
```
https://github.com/YOUR_USERNAME/DIGiDIG/pkgs/container/digidig-SERVICE
```

## Troubleshooting

### Common Issues

#### 1. Docker Registry Push Failures
```bash
# Verify GHCR permissions
echo $REGISTRY_PASSWORD | docker login ghcr.io -u $REGISTRY_USERNAME --password-stdin

# Check repository settings for package permissions
```

#### 2. Deployment Health Check Failures
```bash
# Run health check manually
./scripts/deployment/health-check.sh staging --details

# Check service logs
docker-compose -f docker-compose.staging.yml logs SERVICE_NAME
```

#### 3. Release Creation Issues
```bash
# Verify tag format
git tag -l
# Tags must match v*.*.* pattern

# Check release workflow permissions
# Ensure GITHUB_TOKEN has write permissions
```

### Debug Commands

```bash
# Local development
make install          # Setup local environment

# Docker operations
docker-compose up -d  # Start all services
docker-compose ps     # Check service status
docker-compose logs   # View all logs

# Health monitoring
./scripts/deployment/health-check.sh local
./scripts/deployment/health-check.sh local --details

# Deployment testing
./scripts/deployment/deploy.sh staging main --dry-run
```

### Log Analysis

**GitHub Actions Logs:**
- Access detailed logs for each workflow step
- Download logs for offline analysis
- Monitor resource usage and timing

**Application Logs:**
```bash
# View service logs
docker-compose logs identity
docker-compose logs storage
docker-compose logs smtp

# Follow logs in real-time
docker-compose logs -f
```

**Deployment Logs:**
```bash
# Check deployment script output
./scripts/deployment/deploy.sh staging main 2>&1 | tee deploy.log
```

## Performance Metrics

### CI/CD Pipeline Performance

**Typical Execution Times:**
- CD Workflow: 3-7 minutes per service
- Release Workflow: 2-5 minutes
- Deployment Script: 2-15 minutes (depending on environment)

**Resource Usage:**
- GitHub Actions minutes consumption
- Container registry storage usage
- Network bandwidth for image transfers

### Optimization Recommendations

1. **Parallel Builds:** Matrix strategy reduces build time
2. **Docker Layer Caching:** Speeds up subsequent builds
3. **Image Optimization:** Multi-stage builds reduce image size

## Best Practices

### Development Workflow

1. **Feature Development:**
   ```bash
   git checkout -b feature/my-feature
   # Make changes
   git commit -m "feat: add new feature"
   git push origin feature/my-feature
   # Create PR for review
   ```

2. **Release Process:**
   ```bash
   git checkout main
   git pull origin main
   git tag v1.2.3 -m "Release version 1.2.3"
   git push origin v1.2.3
   # Triggers CD to production
   ```

3. **Hotfix Process:**
   ```bash
   git checkout -b hotfix/critical-fix
   # Make urgent changes
   git commit -m "fix: critical security issue"
   git push origin hotfix/critical-fix
   # Create PR for fast-track review
   ```

### Code Quality

- **Pre-commit Hooks:** Consider adding local pre-commit hooks
- **Code Review:** All changes require PR review
- **Documentation:** Update docs with code changes

### Security

- **Secret Management:** Never commit secrets to repository
- **Dependency Updates:** Regular security updates
- **Image Scanning:** Automatic vulnerability detection
- **Access Control:** Proper GitHub repository permissions

## Migration Guide

### From Manual Deployment

1. **Backup Current Setup:**
   ```bash
   # Create backup of current deployment
   ./scripts/deployment/deploy.sh production backup-only
   ```

2. **Setup GitHub Secrets:**
   - Configure required secrets in repository settings
   - Test deployment script in staging environment

3. **Gradual Migration:**
   - Start with staging environment automation
   - Validate production deployment in maintenance window
   - Switch to automated releases after testing

### Future Enhancements

- **Multi-region Deployment:** Support for multiple production regions
- **Blue-Green Deployment:** Zero-downtime deployment strategy
- **Canary Releases:** Gradual rollout for production releases
- **Infrastructure as Code:** Terraform/Ansible integration
- **Monitoring Integration:** Prometheus/Grafana setup