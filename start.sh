#!/bin/bash
set -e

echo "========================================="
echo "Running database migrations..."
echo "========================================="

# Run migration to drop donation_messages table
if [ -f "drop_donation_messages.py" ]; then
    echo "Running drop_donation_messages.py..."
    /opt/venv/bin/python drop_donation_messages.py || echo "⚠️ Migration failed or already applied"
fi

# Run migration to remove donations table
if [ -f "migrate_remove_donations.py" ]; then
    echo "Running migrate_remove_donations.py..."
    /opt/venv/bin/python migrate_remove_donations.py || echo "⚠️ Migration failed or already applied"
fi

echo ""
echo "========================================="
echo "Starting bgutil POT provider..."
echo "========================================="

echo ""
echo "========================================="
echo "Starting bgutil POT provider..."
echo "========================================="

# Check Node.js availability (required by bgutil)
echo "Node.js: $(node --version 2>/dev/null || echo 'not found')"

# Start bgutil on localhost only
/opt/venv/bin/python -m bgutil_ytdlp_pot_provider --host 127.0.0.1 --port 4416 > /tmp/bgutil.log 2>&1 &
BGUTIL_PID=$!
echo "bgutil started with PID: $BGUTIL_PID"
sleep 3

# Check if running
if ps -p $BGUTIL_PID > /dev/null 2>&1; then
    echo "✅ bgutil is running on port 4416"
else
    echo "⚠️ bgutil failed to start (will use tv_embedded fallback)"
    cat /tmp/bgutil.log 2>/dev/null | head -30 || true
fi

echo ""
echo "========================================="
echo "Starting Flask app..."
echo "========================================="

# Start Flask (foreground)
exec /opt/venv/bin/python app.py
