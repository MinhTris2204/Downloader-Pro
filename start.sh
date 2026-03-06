#!/bin/bash
set -e

echo "========================================="
echo "Starting bgutil POT provider..."
echo "========================================="

# Try to start bgutil in background (optional, won't fail if not available)
if /opt/venv/bin/python -m bgutil_ytdlp_pot_provider --host 0.0.0.0 --port 4416 > /tmp/bgutil.log 2>&1 & then
    BGUTIL_PID=$!
    echo "bgutil started with PID: $BGUTIL_PID"
    sleep 2
    
    # Check if running
    if ps -p $BGUTIL_PID > /dev/null 2>&1; then
        echo "✅ bgutil is running"
    else
        echo "⚠️ bgutil failed to start (will use fallback)"
        cat /tmp/bgutil.log 2>/dev/null || true
    fi
else
    echo "⚠️ bgutil not available (will use fallback)"
fi

echo ""
echo "========================================="
echo "Starting Flask app..."
echo "========================================="

# Start Flask (foreground)
exec /opt/venv/bin/python app.py
