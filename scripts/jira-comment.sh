#!/usr/bin/env bash
# scripts/jira-comment.sh
# Usage: JIRA_EMAIL and JIRA_API_TOKEN must be exported in your environment.
# Example: export JIRA_EMAIL="you@example.com"; export JIRA_API_TOKEN="xxx"

set -euo pipefail

ISSUE=${1:-DIGIDIG-8}
SHIFT_COMMENT=${2-}

# Build a default comment using git metadata if not provided
if [ -n "${SHIFT_COMMENT}" ]; then
  COMMENT="$SHIFT_COMMENT"
else
  BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown-branch")
  COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown-commit")
  COMMENT="Automaticky koment: repo ${PWD##*/}, branch ${BRANCH}, commit ${COMMIT}"
fi

if [ -z "${JIRA_EMAIL:-}" ] || [ -z "${JIRA_API_TOKEN:-}" ]; then
  echo "Set JIRA_EMAIL and JIRA_API_TOKEN in environment." >&2
  exit 2
fi

# Do the request
PAYLOAD=$(printf '{"body":"%s"}' "${COMMENT//"/\"}")

curl -sS -u "${JIRA_EMAIL}:${JIRA_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  "https://pavelperna.atlassian.net/rest/api/3/issue/${ISSUE}/comment" | jq .

echo "Comment posted to ${ISSUE}"