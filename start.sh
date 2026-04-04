#!/bin/bash
# Vikarma Production Launcher
# 🔱 Om Namah Shivaya — For All Humanity

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "🔱 Starting Vikarma in production mode..."

# Load .env if present
if [ -f "$ROOT/.env" ]; then
    export $(grep -v '^#' "$ROOT/.env" | xargs)
    echo "✓ .env loaded"
fi

# ── Backend (gunicorn + uvicorn workers) ──────────────────────────────────────
echo "→ Starting backend on :8765 ..."
cd "$ROOT"
gunicorn server.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers "${WORKERS:-2}" \
    --bind "0.0.0.0:${BACKEND_PORT:-8765}" \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level "${LOG_LEVEL:-info}" \
    --daemon \
    --pid /tmp/vikarma-backend.pid
echo "✓ Backend running (pid $(cat /tmp/vikarma-backend.pid))"

# ── Frontend (next start) ──────────────────────────────────────────────────────
echo "→ Building frontend..."
cd "$ROOT"
npm run build 2>&1 | tail -5

echo "→ Starting frontend on :${FRONTEND_PORT:-3000} ..."
nohup npx next start src --port "${FRONTEND_PORT:-3000}" \
    > /tmp/vikarma-frontend.log 2>&1 &
echo $! > /tmp/vikarma-frontend.pid
echo "✓ Frontend running (pid $(cat /tmp/vikarma-frontend.pid))"

echo ""
echo "🔱 Vikarma is live!"
echo "   Backend  → http://localhost:${BACKEND_PORT:-8765}"
echo "   Frontend → http://localhost:${FRONTEND_PORT:-3000}"
echo ""
echo "To stop: bash stop.sh"
