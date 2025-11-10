#!/bin/bash

# DIGiDIG Health Check Script
# Usage: ./health-check.sh [environment]

set -e

ENVIRONMENT=${1:-local}
BASE_URL=${BASE_URL:-"http://localhost"}

# Environment-specific URLs
case "$ENVIRONMENT" in
    "staging")
        BASE_URL="http://staging.digidig.local"
        ;;
    "production")
        BASE_URL="https://digidig.com"
        ;;
    "local")
        BASE_URL="http://localhost"
        ;;
    *)
        echo "\u274c Unknown environment: $ENVIRONMENT"
        echo "Usage: $0 [local|staging|production]"
        exit 1
        ;;
esac

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Service definitions
declare -A SERVICES=(
    ["identity"]="${IDENTITY_PORT:-9101}"
    ["storage"]="${STORAGE_PORT:-9102}"
    # Use REST ports for service health checks; protocol ports (e.g. 143)
    # are configured separately if needed.
    ["smtp"]="${SMTP_REST_PORT:-9100}"
    ["imap"]="${IMAP_REST_PORT:-9103}"
    ["admin"]="${ADMIN_PORT:-9105}"
    ["mail"]="${MAIL_PORT:-9107}"
    ["apidocs"]="${APIDOCS_PORT:-9110}"
)

echo -e "${BLUE}🩺 DIGiDIG Health Check - $ENVIRONMENT environment${NC}"
echo "Base URL: $BASE_URL"
echo "Time: $(date)"
echo "================================="

TOTAL_SERVICES=${#SERVICES[@]}
HEALTHY_SERVICES=0
FAILED_SERVICES=()

# Function to check service health
check_service() {
    local service=$1
    local port=$2
    local url="$BASE_URL:$port/api/health"
    
    echo -n "Checking $service ($port)... "
    
    if curl -f -s -m 10 "$url" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Healthy${NC}"
        HEALTHY_SERVICES=$((HEALTHY_SERVICES + 1))
        return 0
    else
        echo -e "${RED}❌ Failed${NC}"
        FAILED_SERVICES+=("$service")
        return 1
    fi
}

# Function to check service details
check_service_details() {
    local service=$1
    local port=$2
    local url="$BASE_URL:$port/api/health"
    
    echo "📊 $service details:"
    
    response=$(curl -s -m 10 "$url" 2>/dev/null || echo '{"error": "unreachable"}')
    
    if echo "$response" | jq . >/dev/null 2>&1; then
        echo "$response" | jq .
    else
        echo "  ⚠️  Invalid response or service unreachable"
    fi
    
    echo ""
}

# Check all services
echo ""
for service in "${!SERVICES[@]}"; do
    check_service "$service" "${SERVICES[$service]}"
done

echo ""
echo "================================="
echo -e "📊 Summary: ${GREEN}$HEALTHY_SERVICES${NC}/$TOTAL_SERVICES services healthy"

if [[ $HEALTHY_SERVICES -eq $TOTAL_SERVICES ]]; then
    echo -e "${GREEN}🎉 All services are healthy!${NC}"
    EXIT_CODE=0
else
    echo -e "${RED}⚠️  Some services are unhealthy:${NC}"
    for failed_service in "${FAILED_SERVICES[@]}"; do
        echo -e "  ${RED}- $failed_service${NC}"
    done
    EXIT_CODE=1
fi

# Detailed health information (if requested)
if [[ "$2" == "--details" ]] || [[ "$2" == "-d" ]]; then
    echo ""
    echo "================================="
    echo "🔍 Detailed Health Information"
    echo "================================="
    
    for service in "${!SERVICES[@]}"; do
        check_service_details "$service" "${SERVICES[$service]}"
    done
fi

# Additional checks for critical functionality
if [[ $HEALTHY_SERVICES -gt 0 ]]; then
    echo ""
    echo "🧪 Running functional tests..."
    
    # Test API documentation
    if curl -f -s -m 10 "$BASE_URL:9110" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅ API Documentation accessible${NC}"
    else
        echo -e "  ${RED}❌ API Documentation not accessible${NC}"
        EXIT_CODE=1
    fi
    
    # Test admin interface
    if curl -f -s -m 10 "$BASE_URL:9105" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅ Admin interface accessible${NC}"
    else
        echo -e "  ${RED}❌ Admin interface not accessible${NC}"
        EXIT_CODE=1
    fi
    
    # Test mail interface
    if curl -f -s -m 10 "$BASE_URL:9107" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅ Mail interface accessible${NC}"
    else
        echo -e "  ${RED}❌ Mail interface not accessible${NC}"
        EXIT_CODE=1
    fi
fi

echo ""
echo "================================="
if [[ $EXIT_CODE -eq 0 ]]; then
    echo -e "${GREEN}🎯 Health check PASSED${NC}"
else
    echo -e "${RED}💥 Health check FAILED${NC}"
fi

exit $EXIT_CODE