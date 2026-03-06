#!/bin/bash
set -e

echo "========================================="
echo "Starting bgutil POT provider..."
echo "========================================="

# Start bgutil in background
python -m bgutil_ytdlp_pot_provider --host 0.0.0.0 --port 4416 > /tmp/bgutil.log 2>&1 &
BGUTIL_PID=$!

echo "bgutil started with PID: $BGUTIL_PID"
sleep 3

# Check if running
if ps -p $BGUTIL_PID > /dev/null 2>&1; then
    echo "✅ bgutil is running"
else
    echo "⚠️ bgutil failed to start"
    cat /tmp/bgutil.log 2>/dev/null || true
fi

echo ""
echo "========================================="
echo "Starting Flask app..."
echo "========================================="

# Start Flask (foreground)
exec python app.py
