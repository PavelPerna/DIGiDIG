# DIGiDIG Persistent Volumes Documentation

## Overview

DIGiDIG uses Docker volumes for persistent data storage across service restarts. This ensures that application configurations, logs, and data are preserved.

## Volume Structure

### Database Volumes
- **postgres_data**: PostgreSQL database data for Identity service
- **mongo_data**: MongoDB database data for Storage service

### Application Data Volumes
Each service has its own dedicated data volume for configurations and service-specific data:

- **identity_data**: Identity service configurations and JWT keys
- **smtp_data**: SMTP service configurations (e.g., `/app/data/smtp_config.json`)
- **imap_data**: IMAP service configurations and cached data
- **storage_data**: Storage service configurations and temporary files
- **admin_data**: Admin service configurations and cached data
- **mail_data**: Mail service configurations and user preferences
- **apidocs_data**: API docs service configurations and generated docs

### Shared Volumes
- **app_logs**: Centralized logging for all services (`/app/logs`)
- **test_data**: Test results and temporary test files (`/app/tests`)

## Volume Locations

### Inside Containers
Each service has these mount points:
```
/app/data        # Service-specific persistent data
/app/logs        # Shared logging directory
/app/tests       # Shared test data directory
```

### Host System
Docker manages volumes automatically. To inspect volume locations:
```bash
# List all volumes
docker volume ls

# Inspect volume location and details
docker volume inspect digidig_smtp_data
docker volume inspect digidig_app_logs
```

## Volume Management

### Backup Volumes
```bash
# Backup specific service data
docker run --rm -v digidig_smtp_data:/data -v $(pwd):/backup alpine tar czf /backup/smtp_backup.tar.gz -C /data .

# Backup all app logs
docker run --rm -v digidig_app_logs:/data -v $(pwd):/backup alpine tar czf /backup/logs_backup.tar.gz -C /data .
```

### Restore Volumes
```bash
# Restore service data
docker run --rm -v digidig_smtp_data:/data -v $(pwd):/backup alpine tar xzf /backup/smtp_backup.tar.gz -C /data

# Restore logs
docker run --rm -v digidig_app_logs:/data -v $(pwd):/backup alpine tar xzf /backup/logs_backup.tar.gz -C /data
```

### Clean Up Volumes
```bash
# Remove all DIGiDIG volumes (WARNING: This deletes all persistent data!)
docker compose down -v

# Remove specific volume
docker volume rm digidig_smtp_data
```

### Inspect Volume Contents
```bash
# Browse SMTP configuration files
docker run --rm -v digidig_smtp_data:/data alpine ls -la /data

# View SMTP config
docker run --rm -v digidig_smtp_data:/data alpine cat /data/smtp_config.json

# Browse logs
docker run --rm -v digidig_app_logs:/data alpine ls -la /data
```

## Configuration Examples

### SMTP Service Configuration Persistence
When you change SMTP settings via Admin UI:
- Changes are saved to `/app/data/smtp_config.json` in the `smtp_data` volume
- Configuration persists across container restarts
- Service loads saved configuration on startup

### Logging Configuration
All services log to `/app/logs` which is mounted from the shared `app_logs` volume:
- Centralized log collection
- Logs persist across service restarts
- Can be analyzed with external log management tools

### Test Data Persistence
Test results and temporary files are stored in the shared `test_data` volume:
- Test coverage reports
- Integration test artifacts
- Performance test results

## Development vs Production

### Development
- Volumes are created automatically when running `docker compose up`
- Data persists across container rebuilds
- Easy to reset by running `docker compose down -v`

### Production
- Consider using named external volumes for better control
- Regular backup strategy for critical data
- Monitor volume disk usage
- Consider using specific volume drivers for performance

### Example Production Volume Override
```yaml
# docker-compose.prod.yml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/digidig/data/postgres
  
  app_logs:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/digidig/logs
```

## Troubleshooting

### Volume Permission Issues
If services can't write to volumes:
```bash
# Fix permissions for app data
docker run --rm -v digidig_smtp_data:/data alpine chown -R 1000:1000 /data

# Fix permissions for logs
docker run --rm -v digidig_app_logs:/data alpine chown -R 1000:1000 /data
```

### Volume Space Issues
```bash
# Check volume disk usage
docker system df

# Clean up unused volumes
docker volume prune
```

### Missing Volumes
If volumes are accidentally deleted:
1. Services will create new empty volumes
2. Configuration will reset to defaults
3. Restore from backup if available
4. Reconfigure services via Admin UI