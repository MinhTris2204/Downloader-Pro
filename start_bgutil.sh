#!/bin/bash
# Start bgutil POT provider HTTP server
# This server generates PO Tokens for YouTube bypass

echo "🚀 Starting bgutil POT provider server on port 4416..."

# Run bgutil server in background
python -m bgutil_ytdlp_pot_provider --host 0.0.0.0 --port 4416 &

# Save PID for cleanup
BGUTIL_PID=$!
echo "✅ bgutil server started with PID: $BGUTIL_PID"

# Wait a moment for server to start
sleep 3

# Check if server is running
if ps -p $BGUTIL_PID > /dev/null; then
    echo "✅ bgutil server is running successfully"
    echo "📡 POT provider available at: http://127.0.0.1:4416"
else
    echo "❌ Failed to start bgutil server"
    exit 1
fi

# Keep script running (for Docker)
wait $BGUTIL_PID
