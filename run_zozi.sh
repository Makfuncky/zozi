#!/usr/bin/env bash
# ZOZI E-Commerce Platform — Development Launcher (Unix/macOS)
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "============================================================================"
echo "  ZOZI E-COMMERCE PLATFORM - DEVELOPMENT LAUNCHER"
echo "============================================================================"
echo ""
echo "[INFO] Project Root: $PROJECT_ROOT"

# Kill any leftover process on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 1

# ── 1. Backend ──────────────────────────────────────────────────────────────
echo "[1/3] Starting Backend (FastAPI on port 8000)..."
if [ ! -f "$PROJECT_ROOT/backend/venv/bin/python" ]; then
    echo "[ERROR] Virtual environment not found at backend/venv"
    echo "        Run: cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

(cd "$PROJECT_ROOT/backend" && ./venv/bin/python run_server.py) &
BACKEND_PID=$!
echo "[OK] Backend started (PID $BACKEND_PID)"

# ── Health check gate ───────────────────────────────────────────────────────
echo "[GATE] Waiting for backend health endpoint..."
MAX_WAIT=60
WAITED=0

while [ "$WAITED" -lt "$MAX_WAIT" ]; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || true)
    if [ "$STATUS" = "200" ]; then
        echo "[OK] Backend healthy after ~${WAITED}s."
        break
    fi
    sleep 2
    WAITED=$((WAITED + 2))
done

if [ "$WAITED" -ge "$MAX_WAIT" ]; then
    echo "[ERROR] Backend did not become healthy within ${MAX_WAIT}s."
    kill "$BACKEND_PID" 2>/dev/null || true
    exit 1
fi

# ── 2. Frontend Web ────────────────────────────────────────────────────────
echo "[2/3] Starting Frontend Web App (Next.js on port 3000)..."
if [ ! -f "$PROJECT_ROOT/frontend/web_app/package.json" ]; then
    echo "[ERROR] Frontend not found at frontend/web_app"
    kill "$BACKEND_PID" 2>/dev/null || true
    exit 1
fi

(cd "$PROJECT_ROOT/frontend/web_app" && npm run dev) &
FRONTEND_PID=$!
echo "[OK] Frontend started (PID $FRONTEND_PID)"

sleep 2

# ── 3. Mobile ──────────────────────────────────────────────────────────────
echo "[3/3] Checking Mobile App (Expo)..."
MOBILE_PID=""
if [ -f "$PROJECT_ROOT/frontend/mobile_app/package.json" ]; then
    (cd "$PROJECT_ROOT/frontend/mobile_app" && npx expo start) &
    MOBILE_PID=$!
    echo "[OK] Mobile App started (PID $MOBILE_PID)"
else
    echo "[INFO] Mobile app not found, skipping."
fi

# ── Summary ────────────────────────────────────────────────────────────────
echo ""
echo "============================================================================"
echo "  ZOZI E-COMMERCE PLATFORM IS RUNNING"
echo "============================================================================"
echo ""
echo "  Frontend  (Web):      http://localhost:3000"
echo "  Backend API:          http://127.0.0.1:8000"
echo "  API Docs (Swagger):   http://127.0.0.1:8000/docs"
echo ""
echo "  To stop: kill $BACKEND_PID $FRONTEND_PID ${MOBILE_PID:-}"
echo "============================================================================"

# Wait for all background processes
wait
