#!/bin/bash
# DIGiDIG Volume Management Script

set -e

COMPOSE_PROJECT="digidig"
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_help() {
    echo "DIGiDIG Volume Management Script"
    echo
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo
    echo "Commands:"
    echo "  list                 List all DIGiDIG volumes"
    echo "  inspect [VOLUME]     Inspect volume details"
    echo "  backup [SERVICE]     Backup service data (or 'all' for everything)"
    echo "  restore [BACKUP]     Restore from backup file"
    echo "  clean               Remove all DIGiDIG volumes (WARNING: destructive!)"
    echo "  browse [VOLUME]     Browse volume contents"
    echo "  logs                Show contents of logs volume"
    echo "  status              Show volume usage statistics"
    echo
    echo "Examples:"
    echo "  $0 list"
    echo "  $0 backup smtp"
    echo "  $0 backup all"
    echo "  $0 browse digidig_smtp_data"
    echo "  $0 restore ./backups/20231024_152030/smtp_backup.tar.gz"
}

list_volumes() {
    echo -e "${BLUE}DIGiDIG Volumes:${NC}"
    docker volume ls | grep "^local.*${COMPOSE_PROJECT}_" | sort
}

inspect_volume() {
    local volume=$1
    if [[ ! $volume =~ ^${COMPOSE_PROJECT}_ ]]; then
        volume="${COMPOSE_PROJECT}_${volume}"
    fi
    
    echo -e "${BLUE}Inspecting volume: ${volume}${NC}"
    docker volume inspect "$volume"
}

backup_service() {
    local service=$1
    
    if [ "$service" = "all" ]; then
        backup_all_services
        return
    fi
    
    mkdir -p "$BACKUP_DIR"
    local volume="${COMPOSE_PROJECT}_${service}_data"
    local backup_file="${BACKUP_DIR}/${service}_backup.tar.gz"
    
    echo -e "${YELLOW}Backing up ${service} data...${NC}"
    docker run --rm \
        -v "${volume}:/data" \
        -v "$(pwd)/${BACKUP_DIR}:/backup" \
        alpine sh -c "tar czf /backup/${service}_backup.tar.gz -C /data ."
    
    echo -e "${GREEN}Backup created: ${backup_file}${NC}"
}

backup_all_services() {
    mkdir -p "$BACKUP_DIR"
    
    local services=("identity" "smtp" "imap" "storage" "client" "admin" "apidocs")
    
    echo -e "${YELLOW}Backing up all service data...${NC}"
    
    for service in "${services[@]}"; do
        local volume="${COMPOSE_PROJECT}_${service}_data"
        if docker volume inspect "$volume" >/dev/null 2>&1; then
            backup_service "$service"
        else
            echo -e "${RED}Volume $volume not found, skipping${NC}"
        fi
    done
    
    # Backup shared volumes
    echo -e "${YELLOW}Backing up shared volumes...${NC}"
    
    # App logs
    docker run --rm \
        -v "${COMPOSE_PROJECT}_app_logs:/data" \
        -v "$(pwd)/${BACKUP_DIR}:/backup" \
        alpine tar czf "/backup/app_logs_backup.tar.gz" -C /data .
    
    # Test data
    docker run --rm \
        -v "${COMPOSE_PROJECT}_test_data:/data" \
        -v "$(pwd)/${BACKUP_DIR}:/backup" \
        alpine tar czf "/backup/test_data_backup.tar.gz" -C /data .
    
    # Database volumes
    docker run --rm \
        -v "${COMPOSE_PROJECT}_postgres_data:/data" \
        -v "$(pwd)/${BACKUP_DIR}:/backup" \
        alpine tar czf "/backup/postgres_backup.tar.gz" -C /data .
    
    docker run --rm \
        -v "${COMPOSE_PROJECT}_mongo_data:/data" \
        -v "$(pwd)/${BACKUP_DIR}:/backup" \
        alpine tar czf "/backup/mongo_backup.tar.gz" -C /data .
    
    echo -e "${GREEN}All backups created in: ${BACKUP_DIR}${NC}"
}

restore_backup() {
    local backup_file=$1
    
    if [ ! -f "$backup_file" ]; then
        echo -e "${RED}Backup file not found: $backup_file${NC}"
        exit 1
    fi
    
    # Extract service name from backup filename
    local filename=$(basename "$backup_file")
    local service=$(echo "$filename" | sed 's/_backup\.tar\.gz$//')
    local volume="${COMPOSE_PROJECT}_${service}_data"
    
    echo -e "${YELLOW}Restoring $service from $backup_file...${NC}"
    echo -e "${RED}WARNING: This will overwrite existing data in volume $volume${NC}"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker run --rm \
            -v "${volume}:/data" \
            -v "$(dirname "$(realpath "$backup_file")"):/backup" \
            alpine sh -c "cd /data && tar xzf /backup/$(basename "$backup_file")"
        
        echo -e "${GREEN}Restore completed for $service${NC}"
    else
        echo "Restore cancelled"
    fi
}

clean_volumes() {
    echo -e "${RED}WARNING: This will delete ALL DIGiDIG volumes and data!${NC}"
    echo "This action cannot be undone!"
    read -p "Type 'DELETE' to confirm: " confirmation
    
    if [ "$confirmation" = "DELETE" ]; then
        echo -e "${YELLOW}Stopping all services...${NC}"
        docker compose down
        
        echo -e "${YELLOW}Removing volumes...${NC}"
        docker compose down -v
        
        echo -e "${GREEN}All volumes cleaned${NC}"
    else
        echo "Clean cancelled"
    fi
}

browse_volume() {
    local volume=$1
    if [[ ! $volume =~ ^${COMPOSE_PROJECT}_ ]]; then
        volume="${COMPOSE_PROJECT}_${volume}"
    fi
    
    echo -e "${BLUE}Contents of volume: ${volume}${NC}"
    docker run --rm -v "${volume}:/data" alpine find /data -type f -exec ls -la {} \;
}

show_logs() {
    echo -e "${BLUE}Application logs:${NC}"
    docker run --rm -v "${COMPOSE_PROJECT}_app_logs:/data" alpine find /data -name "*.log" -exec echo "=== {} ===" \; -exec cat {} \;
}

show_status() {
    echo -e "${BLUE}Volume usage statistics:${NC}"
    
    # Overall Docker system stats
    docker system df
    
    echo
    echo -e "${BLUE}DIGiDIG volume details:${NC}"
    
    # Get DIGiDIG volumes and their sizes
    docker volume ls | grep "^local.*${COMPOSE_PROJECT}_" | while read -r driver volume; do
        echo -n "$volume: "
        docker run --rm -v "${volume}:/data" alpine du -sh /data | cut -f1
    done
}

# Main script logic
case "${1:-}" in
    "list")
        list_volumes
        ;;
    "inspect")
        if [ -z "${2:-}" ]; then
            echo "Usage: $0 inspect [VOLUME_NAME]"
            exit 1
        fi
        inspect_volume "$2"
        ;;
    "backup")
        if [ -z "${2:-}" ]; then
            echo "Usage: $0 backup [SERVICE_NAME|all]"
            exit 1
        fi
        backup_service "$2"
        ;;
    "restore")
        if [ -z "${2:-}" ]; then
            echo "Usage: $0 restore [BACKUP_FILE]"
            exit 1
        fi
        restore_backup "$2"
        ;;
    "clean")
        clean_volumes
        ;;
    "browse")
        if [ -z "${2:-}" ]; then
            echo "Usage: $0 browse [VOLUME_NAME]"
            exit 1
        fi
        browse_volume "$2"
        ;;
    "logs")
        show_logs
        ;;
    "status")
        show_status
        ;;
    *)
        print_help
        ;;
esac