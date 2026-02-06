#!/bin/bash
# Start both bgutil POT provider and Flask app

echo "🔧 Starting DownloaderPro services..."

# Update yt-dlp to latest version
echo "📦 Updating yt-dlp..."
pip install -q --upgrade yt-dlp

# Start bgutil POT provider in background
echo "🚀 Starting bgutil POT provider..."
python -m bgutil_ytdlp_pot_provider --host 0.0.0.0 --port 4416 &
BGUTIL_PID=$!

# Wait for bgutil to start
sleep 3

# Check if bgutil is running
if ps -p $BGUTIL_PID > /dev/null; then
    echo "✅ bgutil POT provider started (PID: $BGUTIL_PID)"
else
    echo "⚠️ bgutil failed to start, continuing without it..."
fi

# Start Flask app (foreground)
echo "🌐 Starting Flask application..."
python app.py

# Cleanup on exit
trap "kill $BGUTIL_PID 2>/dev/null" EXIT
