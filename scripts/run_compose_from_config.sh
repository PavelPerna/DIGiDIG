#!/usr/bin/env bash
# Generate a temporary env-file from config/config.yaml and run docker compose with it.
# This avoids requiring the user to maintain a separate .env file while letting
# docker compose receive all the port/DB values consistently from config.yaml.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR}/.."
PY_SCRIPT="$REPO_ROOT/scripts/generate_env_from_config.py"
if [ ! -f "$PY_SCRIPT" ]; then
  echo "generate_env_from_config.py not found at $PY_SCRIPT" >&2
  exit 1
fi

TMP_ENV_FILE=$(mktemp /tmp/digidig_env.XXXXXX)
trap 'rm -f "$TMP_ENV_FILE"' EXIT

python3 "$PY_SCRIPT" > "$TMP_ENV_FILE"

echo "Running docker compose with env-file $TMP_ENV_FILE"
# Run docker compose with the generated env-file. The env-file is passed explicitly
# so there is no permanent .env created in the repo.

docker compose --env-file "$TMP_ENV_FILE" "$@"
