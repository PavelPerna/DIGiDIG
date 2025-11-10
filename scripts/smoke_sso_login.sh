#!/usr/bin/env bash
# Simple smoke test to exercise SSO -> service token redirect and cookie set.
# It reads config/config.yaml to find sso.external_url and admin.external_url and tries a login.
# Usage: ./scripts/smoke_sso_login.sh [target=admin]

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CFG="$REPO_ROOT/config/config.yaml"

if [ ! -f "$CFG" ]; then
  echo "config/config.yaml not found" >&2
  exit 1
fi

SERVICE_SSO_EXTERNAL=$(grep -A5 "^\s*sso:\s*$" "$CFG" | grep "external_url" | sed -E "s/.*external_url:\s*//; s/\"//g; s/'//g" | tr -d '\r' | head -1)
SERVICE_ADMIN_EXTERNAL=$(grep -A5 "^\s*admin:\s*$" "$CFG" | grep "external_url" | sed -E "s/.*external_url:\s*//; s/\"//g; s/'//g" | tr -d '\r' | head -1)

# For local development, use environment variables or defaults
SERVICE_SSO_EXTERNAL="${SERVICE_SSO_EXTERNAL:-http://localhost:9106}"
SERVICE_ADMIN_EXTERNAL="${SERVICE_ADMIN_EXTERNAL:-http://localhost:9105}"

echo "Using SSO URL: $SERVICE_SSO_EXTERNAL"
echo "Using target (admin) URL: $SERVICE_ADMIN_EXTERNAL"

auth_email=$(grep -E "^\s*admin:\s*$" -n "$CFG" -n || true)
# Use default admin credentials from config if present
ADMIN_EMAIL=$(grep -A2 "^\s*admin:\s*$" "$CFG" | grep "email" | head -1 | sed -E 's/.*:\s*"([^"]*)".*/\1/' || true)
ADMIN_PASSWORD=$(grep -A2 "^\s*admin:\s*$" "$CFG" | grep "password" | head -1 | sed -E 's/.*:\s*"([^"]*)".*/\1/' || true)

ADMIN_EMAIL=${ADMIN_EMAIL:-admin@example.com}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin}

COOKIE_JAR="/tmp/digidig_sso_cookies.txt"
rm -f "$COOKIE_JAR"

# Perform login POST. Adjust params if your SSO accepts 'username' or 'email' field.
echo "POSTing credentials to SSO to simulate login and redirect..."

# SSO expects username and password - don't follow redirects
HTTP_CODE=$(curl -s -S -c "$COOKIE_JAR" -X POST -d "username=$ADMIN_EMAIL&password=$ADMIN_PASSWORD&redirect_to=$SERVICE_ADMIN_EXTERNAL" "$SERVICE_SSO_EXTERNAL/login" -w "%{http_code}" -o /dev/null)

echo "SSO login response code: $HTTP_CODE"

if [ "$HTTP_CODE" = "302" ]; then
    echo "✅ SSO login successful (redirect received)"
else
    echo "❌ SSO login failed (expected 302, got $HTTP_CODE)"
    exit 1
fi

echo "Cookies saved to $COOKIE_JAR"
cat "$COOKIE_JAR" || true

# Check if we got an access_token cookie
if grep -q "access_token" "$COOKIE_JAR"; then
    echo "✅ Access token cookie received"
else
    echo "❌ No access token cookie found"
    exit 1
fi

echo "Smoke test finished. SSO authentication is working correctly."
