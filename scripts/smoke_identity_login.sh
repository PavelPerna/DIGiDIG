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
ADMIN_EMAIL=$(grep -E "^\s*admin:\s*$" -n "$CFG" >/dev/null 2>&1 && grep -A2 "^\s*admin:\s*$" "$CFG" | grep "email" | sed -E "s/.*email:\s*//; s/[\"' ]//g" || true)
ADMIN_PASSWORD=$(grep -A2 "^\s*admin:\s*$" "$CFG" | grep "password" | sed -E "s/.*password:\s*//; s/[\"' ]//g" || true)

ADMIN_EMAIL=${ADMIN_EMAIL:-admin@example.com}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin}

COOKIE_JAR="/tmp/digidig_sso_cookies.txt"
rm -f "$COOKIE_JAR"

# Perform login POST. Adjust params if your SSO accepts 'username' or 'email' field.
echo "POSTing credentials to SSO to simulate login and redirect..."

# SSO expects username and password
HTTP_RESP=$(curl -s -S -L -c "$COOKIE_JAR" -d "username=$ADMIN_EMAIL&password=$ADMIN_PASSWORD&redirect_to=$SERVICE_ADMIN_EXTERNAL" "$SERVICE_SSO_EXTERNAL/login" -w "\n%{http_code}" )

echo "--- Response (truncated) ---"
echo "$HTTP_RESP" | sed -n '1,200p'
echo "---------------------------"

echo "Cookies saved to $COOKIE_JAR"
cat "$COOKIE_JAR" || true

# Call admin debug endpoint to verify session
echo "Calling $SERVICE_ADMIN_EXTERNAL/debug/whoami with cookies..."
curl -s -S -b "$COOKIE_JAR" "$SERVICE_ADMIN_EXTERNAL/debug/whoami" || true

echo "Smoke test finished. If the debug/whoami returned user info, /api/session should also work for frontends."
