#!/bin/bash
# Start both bgutil POT provider and Flask app

set -e  # Exit on error

echo "========================================="
echo "🔧 Starting DownloaderPro services..."
echo "========================================="

# Update yt-dlp to latest version
echo "📦 Updating yt-dlp..."
pip install -q --upgrade yt-dlp
echo "✅ yt-dlp updated"

# Start bgutil POT provider in background
echo ""
echo "🚀 Starting bgutil POT provider on port 4416..."
python -m bgutil_ytdlp_pot_provider --host 0.0.0.0 --port 4416 > /tmp/bgutil.log 2>&1 &
BGUTIL_PID=$!
echo "bgutil PID: $BGUTIL_PID"

# Wait for bgutil to start
echo "⏳ Waiting for bgutil to initialize..."
sleep 5

# Check if bgutil is running
if ps -p $BGUTIL_PID > /dev/null 2>&1; then
    echo "✅ bgutil POT provider started successfully (PID: $BGUTIL_PID)"
    echo "📡 bgutil server: http://127.0.0.1:4416"
    
    # Show first few lines of bgutil log
    if [ -f /tmp/bgutil.log ]; then
        echo "📋 bgutil log (first 5 lines):"
        head -n 5 /tmp/bgutil.log
    fi
else
    echo "⚠️ WARNING: bgutil failed to start!"
    echo "📋 bgutil error log:"
    cat /tmp/bgutil.log 2>/dev/null || echo "No log file found"
    echo "⚠️ Continuing without bgutil (will use fallback strategies)..."
fi

echo ""
echo "========================================="
echo "🌐 Starting Flask application on port 8080..."
echo "========================================="

# Start Flask app (foreground)
python app.py

# Cleanup on exit
trap "echo 'Stopping bgutil...'; kill $BGUTIL_PID 2>/dev/null" EXIT
