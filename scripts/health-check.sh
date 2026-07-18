#!/usr/bin/env bash
set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8000/health}"
FRONTEND_URL="${FRONTEND_URL:-http://127.0.0.1:3000}"

check_url() {
  local name="$1"
  local url="$2"
  if curl --fail --silent --show-error --max-time 8 "$url" >/dev/null; then
    echo "[OK] ${name}: ${url}"
  else
    echo "[FAIL] ${name}: ${url}"
    return 1
  fi
}

check_url "backend" "$BACKEND_URL"
check_url "frontend" "$FRONTEND_URL"

echo "Health check passed."
