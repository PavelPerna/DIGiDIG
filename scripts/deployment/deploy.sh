#!/bin/bash

# DIGiDIG Deployment Script
# Usage: ./deploy.sh [staging|production] [version]

set -e

ENVIRONMENT=${1:-staging}
VERSION=${2:-main}
PROJECT_NAME="digidig"
REGISTRY="ghcr.io/pavelperna/digidig"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Validate inputs
if [[ ! "$ENVIRONMENT" =~ ^(staging|production)$ ]]; then
    error "Environment must be 'staging' or 'production'"
    exit 1
fi

if [[ -z "$VERSION" ]]; then
    error "Version must be specified"
    exit 1
fi

log "🚀 Starting deployment of DIGiDIG $VERSION to $ENVIRONMENT"

# Set environment-specific configuration
if [[ "$ENVIRONMENT" == "production" ]]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    ENV_FILE=".env.prod"
    BACKUP_DIR="/opt/backups/digidig"
    
    # Production safety checks
    if [[ ! "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        error "Production requires semantic version (e.g., v1.0.0)"
        exit 1
    fi
    
    # Confirm production deployment
    read -p "⚠️  Are you sure you want to deploy $VERSION to PRODUCTION? (yes/no): " confirm
    if [[ "$confirm" != "yes" ]]; then
        log "Deployment cancelled"
        exit 0
    fi
else
    COMPOSE_FILE="docker-compose.staging.yml"
    ENV_FILE=".env.staging"
    BACKUP_DIR="/opt/backups/digidig-staging"
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Function to create backup
create_backup() {
    log "📦 Creating backup..."
    
    BACKUP_NAME="backup-$(date +%Y%m%d-%H%M%S)"
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
    
    mkdir -p "$BACKUP_PATH"
    
    # Backup database
    if docker-compose ps postgres | grep -q "Up"; then
        log "Backing up PostgreSQL database..."
        docker-compose exec -T postgres pg_dumpall -U postgres > "$BACKUP_PATH/postgres.sql"
    fi
    
    # Backup MongoDB
    if docker-compose ps mongo | grep -q "Up"; then
        log "Backing up MongoDB..."
        docker-compose exec -T mongo mongodump --archive > "$BACKUP_PATH/mongo.archive"
    fi
    
    # Backup configuration
    cp -r . "$BACKUP_PATH/app" 2>/dev/null || true
    
    success "Backup created at $BACKUP_PATH"
    echo "$BACKUP_PATH" > "$BACKUP_DIR/latest"
}

# Function to rollback
rollback() {
    error "Deployment failed! Rolling back..."
    
    if [[ -f "$BACKUP_DIR/latest" ]]; then
        LATEST_BACKUP=$(cat "$BACKUP_DIR/latest")
        log "Rolling back to $LATEST_BACKUP"
        
        # Restore from backup
        docker-compose down
        
        # Restore database if exists
        if [[ -f "$LATEST_BACKUP/postgres.sql" ]]; then
            docker-compose up -d postgres
            sleep 10
            docker-compose exec -T postgres psql -U postgres < "$LATEST_BACKUP/postgres.sql"
        fi
        
        if [[ -f "$LATEST_BACKUP/mongo.archive" ]]; then
            docker-compose up -d mongo
            sleep 10
            docker-compose exec -T mongo mongorestore --archive < "$LATEST_BACKUP/mongo.archive"
        fi
        
        docker-compose up -d
    fi
    
    exit 1
}

# Trap errors for rollback
trap rollback ERR

# Main deployment process
main() {
    # Pre-deployment checks
    log "🔍 Running pre-deployment checks..."
    
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        error "Compose file $COMPOSE_FILE not found"
        exit 1
    fi
    
    if [[ ! -f "$ENV_FILE" ]]; then
        error "Environment file $ENV_FILE not found"
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        error "Docker is not running"
        exit 1
    fi
    
    # Check available disk space (minimum 2GB)
    AVAILABLE_SPACE=$(df . | awk 'NR==2 {print $4}')
    if [[ $AVAILABLE_SPACE -lt 2097152 ]]; then
        warning "Low disk space: ${AVAILABLE_SPACE}KB available"
    fi
    
    # Create backup (only for production)
    if [[ "$ENVIRONMENT" == "production" ]]; then
        create_backup
    fi
    
    # Pull latest images
    log "📥 Pulling Docker images for version $VERSION..."
    
    export DIGIDIG_VERSION="$VERSION"
    
    # Update image tags in compose file
    sed -i.bak "s|${REGISTRY}/\([^:]*\):.*|${REGISTRY}/\1:${VERSION}|g" "$COMPOSE_FILE"
    
    # Pull images
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull
    
    # Stop services
    log "🛑 Stopping current services..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
    
    # Start services
    log "🚀 Starting services with version $VERSION..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    # Wait for services to be ready
    log "⏳ Waiting for services to be ready..."
    sleep 30
    
    # Health checks
    log "🩺 Running health checks..."
    
    MAX_RETRIES=12
    RETRY_COUNT=0
    
    while [[ $RETRY_COUNT -lt $MAX_RETRIES ]]; do
        if curl -f "${IDENTITY_HEALTH_URL:-http://localhost:9101/api/health}" >/dev/null 2>&1; then
            success "Identity service is healthy"
            break
        fi
        
        RETRY_COUNT=$((RETRY_COUNT + 1))
        log "Health check attempt $RETRY_COUNT/$MAX_RETRIES..."
        sleep 10
    done
    
    if [[ $RETRY_COUNT -eq $MAX_RETRIES ]]; then
        error "Health checks failed after $MAX_RETRIES attempts"
        exit 1
    fi
    
    # Run integration tests
    log "🧪 Running integration tests..."
    if command -v make >/dev/null 2>&1; then
        make test || {
            error "Integration tests failed"
            exit 1
        }
    else
        warning "Make not available, skipping integration tests"
    fi
    
    # Cleanup old images
    log "🧹 Cleaning up old Docker images..."
    docker image prune -f
    
    success "🎉 Deployment of DIGiDIG $VERSION to $ENVIRONMENT completed successfully!"
    
    # Show deployment info
    log "📊 Deployment Summary:"
    echo "  Environment: $ENVIRONMENT"
    echo "  Version: $VERSION"
    echo "  Deployed at: $(date)"
    echo "  Services:"
    docker-compose -f "$COMPOSE_FILE" ps
}

# Run main function
main "$@"