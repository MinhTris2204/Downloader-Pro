"""
PLAN: Upgrade to Socket.IO (if needed in future)

Use cases that would justify Socket.IO:
1. Live chat support
2. Real-time download progress for all users
3. Live notifications
4. Admin dashboard with instant updates
5. User activity feed

Implementation plan:
"""

# 1. Install dependencies
# pip install flask-socketio

# 2. Setup Socket.IO
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 3. Track active connections
active_connections = set()

@socketio.on('connect')
def handle_connect():
    active_connections.add(request.sid)
    # Send current stats immediately
    emit('stats_update', get_current_stats())

@socketio.on('disconnect')
def handle_disconnect():
    active_connections.discard(request.sid)

# 4. Broadcast updates when stats change
def broadcast_stats_update():
    if active_connections:
        stats = get_current_stats()
        socketio.emit('stats_update', stats)

# 5. Frontend changes
"""
<script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
<script>
const socket = io();

socket.on('stats_update', (data) => {
    updateStatDisplay(data);
});

socket.on('connect', () => {
    console.log('Connected to real-time stats');
});
</script>
"""

# Pros of this approach:
# - Instant updates (0 delay)
# - More engaging user experience
# - Can add live features later

# Cons:
# - More complex
# - Higher resource usage
# - Overkill for current needs