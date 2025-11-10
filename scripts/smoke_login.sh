#!/usr/bin/env bash
# Unified smoke test for login functionality
# Usage: ./scripts/smoke_login.sh [service_name] [test_endpoint]
#   service_name: identity, sso (default: sso)
#   test_endpoint: admin, client, etc. (default: admin)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CFG="$REPO_ROOT/config/config.yaml"

# Parameters
AUTH_SERVICE="${1:-sso}"
TARGET_SERVICE="${2:-admin}"

if [ ! -f "$CFG" ]; then
  echo "config/config.yaml not found" >&2
  exit 1
fi

# Extract service URLs from config
get_service_url() {
    local service=$1
    grep -A5 "^\s*${service}:\s*$" "$CFG" | grep "external_url" | sed -E "s/.*external_url:\s*//; s/\"//g; s/'//g" | tr -d '\r' | head -1
}

# Get port from config
get_service_port() {
    local service=$1
    grep -A5 "^\s*${service}:\s*$" "$CFG" | grep "http_port" | sed -E "s/.*http_port:\s*//; s/\"//g; s/'//g" | tr -d '\r' | head -1
}

AUTH_DOMAIN=$(get_service_url "$AUTH_SERVICE")
TARGET_DOMAIN=$(get_service_url "$TARGET_SERVICE")
AUTH_PORT=$(get_service_port "$AUTH_SERVICE")
TARGET_PORT=$(get_service_port "$TARGET_SERVICE")

# Build full URLs
AUTH_URL="http://${AUTH_DOMAIN}:${AUTH_PORT}"
TARGET_URL="http://${TARGET_DOMAIN}:${TARGET_PORT}"

# Fallback to defaults if config parsing fails
AUTH_URL="${AUTH_URL:-http://localhost:9106}"
TARGET_URL="${TARGET_URL:-http://localhost:9105}"

echo "================================================"
echo "DIGiDIG Smoke Test - Login Flow"
echo "================================================"
echo "Auth Service:   $AUTH_SERVICE ($AUTH_URL)"
echo "Target Service: $TARGET_SERVICE ($TARGET_URL)"
echo "================================================"

# Get admin credentials from config
ADMIN_EMAIL=$(grep -A3 "^\s*admin:\s*$" "$CFG" | grep "email" | head -1 | sed -E 's/.*:\s*"?([^"]*)"?.*/\1/' | tr -d ' ' || echo "admin@example.com")
ADMIN_PASSWORD=$(grep -A3 "^\s*admin:\s*$" "$CFG" | grep "password" | head -1 | sed -E 's/.*:\s*"?([^"]*)"?.*/\1/' | tr -d ' ' || echo "admin")

ADMIN_EMAIL=${ADMIN_EMAIL:-admin@example.com}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin}

COOKIE_JAR="/tmp/digidig_smoke_cookies_${AUTH_SERVICE}.txt"
rm -f "$COOKIE_JAR"

echo ""
echo "Step 1/3: Sending login credentials to $AUTH_SERVICE..."
echo "         Username: $ADMIN_EMAIL"

# Perform login POST
if [ "$AUTH_SERVICE" = "identity" ]; then
    # Identity service uses /login endpoint
    HTTP_CODE=$(curl -s -S -c "$COOKIE_JAR" -X POST \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASSWORD\"}" \
        "$AUTH_URL/login" -w "%{http_code}" -o /tmp/login_response.txt)
else
    # SSO service uses form data
    HTTP_CODE=$(curl -s -S -c "$COOKIE_JAR" -X POST \
        -d "username=$ADMIN_EMAIL&password=$ADMIN_PASSWORD&redirect_to=$TARGET_URL" \
        "$AUTH_URL/login" -w "%{http_code}" -o /tmp/login_response.txt)
fi

echo "         Response Code: $HTTP_CODE"

# Check response
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "         ✅ Login successful"
else
    echo "         ❌ Login failed (expected 200 or 302, got $HTTP_CODE)"
    echo ""
    echo "Response body:"
    cat /tmp/login_response.txt
    exit 1
fi

echo ""
echo "Step 2/3: Checking cookies..."

if [ -f "$COOKIE_JAR" ] && [ -s "$COOKIE_JAR" ]; then
    echo "         Cookies received:"
    grep -v "^#" "$COOKIE_JAR" | awk '{print "         - " $6 "=" substr($7,1,20) "..."}' || true
    
    # Check for access token
    if grep -q "access_token" "$COOKIE_JAR"; then
        echo "         ✅ Access token cookie found"
    else
        echo "         ⚠️  No access_token cookie (may be in response body)"
    fi
else
    echo "         ⚠️  No cookies saved to jar"
fi

echo ""
echo "Step 3/3: Testing authenticated request to $TARGET_SERVICE..."

# Call target service with cookies
WHOAMI_RESPONSE=$(curl -s -S -b "$COOKIE_JAR" "$TARGET_URL/debug/whoami" 2>&1 || echo "ERROR")

if echo "$WHOAMI_RESPONSE" | grep -q "email\|user\|admin"; then
    echo "         ✅ Authenticated request successful"
    echo ""
    echo "Response:"
    echo "$WHOAMI_RESPONSE" | head -n 20
else
    echo "         ❌ Authenticated request failed or returned unexpected data"
    echo ""
    echo "Response:"
    echo "$WHOAMI_RESPONSE"
fi

echo ""
echo "================================================"
echo "Smoke test complete!"
echo "================================================"
echo "Cookie jar saved at: $COOKIE_JAR"
echo ""

# Cleanup
rm -f /tmp/login_response.txt

exit 0
