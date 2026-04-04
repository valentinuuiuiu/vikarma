#!/bin/bash
# Vikarma Stop Script

echo "🔱 Stopping Vikarma..."

if [ -f /tmp/vikarma-backend.pid ]; then
    kill $(cat /tmp/vikarma-backend.pid) 2>/dev/null && echo "✓ Backend stopped" || echo "Backend already stopped"
    rm -f /tmp/vikarma-backend.pid
fi

if [ -f /tmp/vikarma-frontend.pid ]; then
    kill $(cat /tmp/vikarma-frontend.pid) 2>/dev/null && echo "✓ Frontend stopped" || echo "Frontend already stopped"
    rm -f /tmp/vikarma-frontend.pid
fi
