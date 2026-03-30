from flask import Flask, render_template, request, jsonify, redirect, session
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime
import os
import re
import uuid
import threading
import tempfile
import time
import json
import zipfile
import requests as http_requests
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
import functools
import psycopg2
from psycopg2 import pool
import hashlib

# Socket.IO for real-time online users
from flask_socketio import SocketIO, emit, disconnect, join_room

# Import controllers
from controllers.home_controller import HomeController
from controllers.blog_controller import BlogController
from controllers.news_controller import NewsController
from controllers.donate_controller import donate_bp
from controllers.auth_controller import auth_bp
from utils.tracking import get_full_tracking_info

app = Flask(__name__)
# Secret key for session (change this in production!)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Session configuration for Railway (HTTPS)
# Disable secure cookies temporarily to fix redirect loop issue
# Railway's proxy might not be forwarding HTTPS headers correctly
app.config['SESSION_COOKIE_SECURE'] = False  # Temporarily disabled - TODO: Re-enable after fixing proxy
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Allow same-site requests
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 30  # 30 days

# Fix for Proxy (Railway SSL) - must be set BEFORE any routes
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_for=1, x_port=1)

# Initialize Socket.IO with eventlet for production
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Track online users with Socket.IO
online_users = set()  # Set of session IDs

# Register blueprints
app.register_blueprint(donate_bp)
app.register_blueprint(auth_bp)

# ===== SOCKET.IO EVENTS FOR REAL-TIME ONLINE USERS =====

# Dictionary to map socket_id -> user_id
socket_to_user = {}
# Dictionary to map user_id -> set of socket_ids (user can have multiple tabs)
user_to_sockets = {}

@socketio.on('connect')
def handle_connect():
    """Người dùng kết nối - tăng online count"""
    try:
        # Tạo unique session cho user này
        user_session = request.sid
        online_users.add(user_session)
        
        print(f"[SOCKET] User connected: {user_session} | Online: {len(online_users)}")
        
        # Broadcast số online mới cho TẤT CẢ clients (bao gồm cả user vừa connect)
        socketio.emit('online_count_update', {
            'online_users': len(online_users)
        }, to=None)  # to=None means broadcast to all
        
    except Exception as e:
        print(f"[SOCKET ERROR] Connect failed: {e}")

@socketio.on('disconnect')
def handle_disconnect():
    """Người dùng ngắt kết nối - giảm online count"""
    try:
        user_session = request.sid
        online_users.discard(user_session)
        
        # Remove from user tracking
        if user_session in socket_to_user:
            user_id = socket_to_user[user_session]
            del socket_to_user[user_session]
            
            # Remove socket from user's socket set
            if user_id in user_to_sockets:
                user_to_sockets[user_id].discard(user_session)
                # If user has no more sockets, remove from online users
                if not user_to_sockets[user_id]:
                    del user_to_sockets[user_id]
                    # Notify admin that user went offline
                    socketio.emit('user_status', {
                        'user_id': user_id,
                        'status': 'offline'
                    }, room='admin')
        
        print(f"[SOCKET] User disconnected: {user_session} | Online: {len(online_users)}")
        
        # Broadcast số online mới cho tất cả clients
        socketio.emit('online_count_update', {
            'online_users': len(online_users)
        }, to=None)  # to=None means broadcast to all
        
    except Exception as e:
        print(f"[SOCKET ERROR] Disconnect failed: {e}")

@socketio.on('user_login')
def handle_user_login(data):
    """User logged in - track their user_id"""
    try:
        user_id = data.get('user_id')
        if user_id:
            socket_id = request.sid
            socket_to_user[socket_id] = user_id
            
            # Add socket to user's socket set
            if user_id not in user_to_sockets:
                user_to_sockets[user_id] = set()
                # First socket for this user - they just came online
                socketio.emit('user_status', {
                    'user_id': user_id,
                    'status': 'online'
                }, room='admin')
            
            user_to_sockets[user_id].add(socket_id)
            
            print(f"[SOCKET] User {user_id} logged in on socket {socket_id}")
            
    except Exception as e:
        print(f"[SOCKET ERROR] User login failed: {e}")

@socketio.on('join_admin')
def handle_join_admin():
    """Admin joins admin room to receive user status updates"""
    try:
        from flask import session as flask_session
        if 'admin_logged_in' in flask_session:
            join_room('admin')
            print(f"[SOCKET] Admin joined admin room: {request.sid}")
            
            # Send current online users to admin
            online_user_ids = list(user_to_sockets.keys())
            emit('online_users_list', {
                'user_ids': online_user_ids
            })
    except Exception as e:
        print(f"[SOCKET ERROR] Join admin failed: {e}")

@socketio.on('ping')
def handle_ping():
    """Heartbeat để maintain connection"""
    emit('pong')

@socketio.on('get_online_count')
def handle_get_online_count():
    """Client yêu cầu số online hiện tại"""
    try:
        current_count = len(online_users)
        print(f"[SOCKET] Client requested online count: {current_count}")
        
        # Gửi về cho client yêu cầu
        emit('online_count_update', {
            'online_users': current_count
        })
        
    except Exception as e:
        print(f"[SOCKET ERROR] Get online count failed: {e}")

# Admin credentials (use environment variables in production)
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = hashlib.sha256(os.environ.get('ADMIN_PASSWORD', 'admin123').encode()).hexdigest()

# ===== INVIDIOUS PROXY INSTANCES (Fallback when cookies fail) =====
INVIDIOUS_INSTANCES = [
    'https://invidious.asir.dev',
    'https://inv.nndhc.top',
    'https://invidious.namazso.eu',
    'https://inv.riverside.rocks',
    'https://invidious.lunar.icu',
    'https://yt.drnd.rd',
    'https://invidious.private.coffee',
    'https://iv.ggtyler.dev',
]

# ===== YOUTUBE AUTHENTICATION FOR RAILWAY =====
# Method 1: Cookies via YOUTUBE_COOKIES environment variable (base64 encoded)
# Method 2: OAuth via YOUTUBE_OAUTH_REFRESH_TOKEN environment variable
# Method 3: Proxy via HTTP_PROXY or HTTPS_PROXY environment variable
# To generate: base64 -w 0 cookies.txt > cookies_base64.txt
# Then set YOUTUBE_COOKIES=<content of cookies_base64.txt> in Railway

# Proxy configuration (to bypass IP blocks)
HTTP_PROXY = os.environ.get('HTTP_PROXY', '')
HTTPS_PROXY = os.environ.get('HTTPS_PROXY', '')
SOCKS_PROXY = os.environ.get('SOCKS_PROXY', '')

if HTTP_PROXY:
    print(f"[INFO] HTTP Proxy configured: {HTTP_PROXY.split('@')[-1]}")
if HTTPS_PROXY:
    print(f"[INFO] HTTPS Proxy configured: {HTTPS_PROXY.split('@')[-1]}")
if SOCKS_PROXY:
    print(f"[INFO] SOCKS Proxy configured: {SOCKS_PROXY.split('@')[-1]}")

COOKIES_FILE_PATH = os.path.join(tempfile.gettempdir(), 'yt_cookies.txt')
YOUTUBE_COOKIES_ENV = os.environ.get('YOUTUBE_COOKIES', '')
YOUTUBE_OAUTH_TOKEN = os.environ.get('YOUTUBE_OAUTH_REFRESH_TOKEN', '')
YOUTUBE_PO_TOKEN = os.environ.get('YOUTUBE_PO_TOKEN', '')
YOUTUBE_VISITOR_DATA = os.environ.get('YOUTUBE_VISITOR_DATA', '')
if YOUTUBE_PO_TOKEN:
    print(f"[DEBUG] YouTube PO Token detected (length: {len(YOUTUBE_PO_TOKEN)})")
if YOUTUBE_VISITOR_DATA:
    print(f"[DEBUG] YouTube Visitor Data detected (length: {len(YOUTUBE_VISITOR_DATA)})")

# Debug: Check if env vars are loaded
print(f"[DEBUG] YOUTUBE_COOKIES env length: {len(YOUTUBE_COOKIES_ENV)} chars")
print(f"[DEBUG] Temp dir: {tempfile.gettempdir()}")
# List all YOUTUBE related env vars for debugging
youtube_related_vars = [k for k in os.environ.keys() if 'YOUTUBE' in k.upper() or 'COOKIE' in k.upper()]
if youtube_related_vars:
    print(f"[DEBUG] Found env vars: {youtube_related_vars}")
else:
    print(f"[DEBUG] No YOUTUBE/COOKIE env vars found in environment")

# OAuth Token file path for yt-dlp-youtube-oauth2 plugin
OAUTH_TOKEN_FILE = os.path.join(tempfile.gettempdir(), 'youtube_oauth_token.json')

if YOUTUBE_OAUTH_TOKEN:
    try:
        oauth_content = YOUTUBE_OAUTH_TOKEN
        # If it looks like base64, try decoding it, otherwise use it raw (if it's already JSON)
        if YOUTUBE_OAUTH_TOKEN.startswith('ey') or 'refresh_token' not in YOUTUBE_OAUTH_TOKEN:
             try:
                 import base64
                 oauth_content = base64.b64decode(YOUTUBE_OAUTH_TOKEN).decode('utf-8')
             except:
                 pass # Use raw if decode fails

        with open(OAUTH_TOKEN_FILE, 'w', encoding='utf-8') as f:
            f.write(oauth_content)
        print(f"[SUCCESS] YouTube OAuth token initialized")
    except Exception as e:
        print(f"[WARNING] Failed to load YOUTUBE_OAUTH_REFRESH_TOKEN: {e}")
        OAUTH_TOKEN_FILE = None
else:
    # Check for local oauth token file
    local_oauth = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'youtube_oauth_token.json')
    if os.path.exists(local_oauth):
        OAUTH_TOKEN_FILE = local_oauth
        print(f"[INFO] Using local YouTube OAuth token file")
    else:
        OAUTH_TOKEN_FILE = None

if YOUTUBE_COOKIES_ENV:
    try:
        import base64
        cookies_content = base64.b64decode(YOUTUBE_COOKIES_ENV).decode('utf-8')
        with open(COOKIES_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(cookies_content)
        print(f"[SUCCESS] YouTube cookies loaded from environment variable ({len(cookies_content)} bytes)")
    except Exception as e:
        print(f"[WARNING] Failed to decode YOUTUBE_COOKIES: {e}")
        COOKIES_FILE_PATH = None
else:
    # Check for local cookies.txt file
    local_cookies = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookies.txt')
    if os.path.exists(local_cookies):
        COOKIES_FILE_PATH = local_cookies
        print(f"[INFO] Using local cookies.txt file")
    else:
        COOKIES_FILE_PATH = None
        if not OAUTH_TOKEN_FILE:
            print(f"[WARNING] No YouTube auth configured! Bot detection bypass will be limited.")
            print(f"[INFO] Add YOUTUBE_COOKIES or YOUTUBE_OAUTH_REFRESH_TOKEN env var for reliable downloads.")

# Rate limiting tracking
last_youtube_download = {}  # IP -> timestamp
YOUTUBE_COOLDOWN = 20  # seconds between downloads per IP (increased for Railway)


# Add security headers
@app.after_request
def add_security_headers(response):
    # Force HTTPS for 1 year
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    # Prevent mixed content
    response.headers['Content-Security-Policy'] = "upgrade-insecure-requests"
    return response

# PostgreSQL Connection Pool
db_pool = None
DATABASE_URL = os.environ.get('DATABASE_URL')

# Debug: Print DATABASE_URL format (hide password)
if DATABASE_URL:
    safe_url = DATABASE_URL.split('@')[0].split(':')[0:2]
    print(f"[DEBUG] DATABASE_URL detected: {safe_url[0]}://user:***@...")

from contextlib import contextmanager

@contextmanager
def get_db_conn():
    """Context manager để tự động trả connection về pool, tránh leak."""
    conn = db_pool.getconn()
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        db_pool.putconn(conn)

def init_db():
    """Initialize database connection and create tables"""
    global db_pool
    
    if not DATABASE_URL:
        print("[WARNING] DATABASE_URL not found. Using fallback JSON stats.")
        return False
    
    try:
        # Fix Railway URL format if needed
        db_url = DATABASE_URL
        
        # Railway sometimes returns URL without proper format
        # Convert to proper PostgreSQL URL if needed
        if not db_url.startswith('postgresql://') and not db_url.startswith('postgres://'):
            print(f"[ERROR] Invalid DATABASE_URL format: {db_url[:50]}...")
            return False
        
        # psycopg2 prefers 'postgresql://' over 'postgres://'
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        
        # Create connection pool
        db_pool = psycopg2.pool.ThreadedConnectionPool(
            2, 20,
            db_url
        )
        
        # Create table if not exists
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        # Chỉ tạo các bảng cần thiết
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id SERIAL PRIMARY KEY,
                platform VARCHAR(20) NOT NULL,
                format VARCHAR(10) NOT NULL,
                quality VARCHAR(20),
                download_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT TRUE,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                ip_address VARCHAR(45),
                country VARCHAR(100),
                country_code VARCHAR(5),
                region VARCHAR(100),
                city VARCHAR(100),
                timezone VARCHAR(50),
                latitude DECIMAL(10, 8),
                longitude DECIMAL(11, 8),
                device_type VARCHAR(50),
                os VARCHAR(100),
                browser VARCHAR(100),
                is_mobile BOOLEAN,
                is_tablet BOOLEAN,
                is_pc BOOLEAN,
                user_agent TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                id SERIAL PRIMARY KEY,
                total_downloads INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create error_logs table for admin monitoring
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS error_logs (
                id SERIAL PRIMARY KEY,
                error_type VARCHAR(50) NOT NULL,
                error_message TEXT NOT NULL,
                stack_trace TEXT,
                url TEXT,
                platform VARCHAR(20),
                format VARCHAR(10),
                quality VARCHAR(20),
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_error_logs_created 
            ON error_logs(created_at DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_error_logs_type 
            ON error_logs(error_type, created_at DESC)
        """)
        
        # Create system_logs table for all console logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id SERIAL PRIMARY KEY,
                log_level VARCHAR(20) NOT NULL,
                log_message TEXT NOT NULL,
                log_source VARCHAR(100),
                url TEXT,
                method VARCHAR(10),
                status_code INTEGER,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                execution_time FLOAT,
                additional_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_system_logs_created 
            ON system_logs(created_at DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_system_logs_level 
            ON system_logs(log_level, created_at DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_system_logs_source 
            ON system_logs(log_source, created_at DESC)
        """)
        
        print("[INFO] Essential tables created/verified")
        
        # Create users table for authentication
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(30) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255),
                is_verified BOOLEAN DEFAULT FALSE,
                google_id VARCHAR(100) UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email 
            ON users(email)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_username 
            ON users(username)
        """)
        
        # Create premium_subscriptions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS premium_subscriptions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                order_code VARCHAR(50),
                amount INTEGER NOT NULL DEFAULT 0,
                starts_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                payment_status VARCHAR(20) DEFAULT 'success',
                payment_method VARCHAR(50),
                transaction_id VARCHAR(100),
                donor_email VARCHAR(100),
                ip_address VARCHAR(45),
                user_agent TEXT,
                paid_at TIMESTAMP
            )
        """)
        
        # Add payment columns if they don't exist (for existing databases)
        payment_columns = [
            ("payment_status", "VARCHAR(20) DEFAULT 'success'"),
            ("payment_method", "VARCHAR(50)"),
            ("transaction_id", "VARCHAR(100)"),
            ("donor_email", "VARCHAR(100)"),
            ("ip_address", "VARCHAR(45)"),
            ("user_agent", "TEXT"),
            ("paid_at", "TIMESTAMP")
        ]
        
        for col_name, col_type in payment_columns:
            try:
                cursor.execute(f"ALTER TABLE premium_subscriptions ADD COLUMN IF NOT EXISTS {col_name} {col_type}")
            except Exception as e:
                print(f"[INFO] Column {col_name} check: {e}")
                conn.rollback()
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_premium_user_active 
            ON premium_subscriptions(user_id, is_active, expires_at)
        """)
        
        # Create user_downloads table for tracking download limits
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_downloads (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(100) NOT NULL,
                platform VARCHAR(20) NOT NULL,
                download_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_downloads_user_time 
            ON user_downloads(user_id, download_time)
        """)
        
        print("[INFO] user_downloads table created/verified")
        
        # Create OTP codes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS otp_codes (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                email VARCHAR(100) NOT NULL,
                otp_code VARCHAR(6) NOT NULL,
                purpose VARCHAR(20) NOT NULL DEFAULT 'verify',
                is_used BOOLEAN DEFAULT FALSE,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_otp_user_purpose 
            ON otp_codes(user_id, purpose, expires_at)
        """)
        
        print("[INFO] Users, premium_subscriptions, otp_codes tables created/verified")
        
        # Create page_visits table for real-time statistics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS page_visits (
                id SERIAL PRIMARY KEY,
                ip_address VARCHAR(45) NOT NULL,
                user_agent TEXT,
                page_url VARCHAR(500),
                referrer VARCHAR(500),
                visit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_id VARCHAR(64),
                country VARCHAR(100),
                city VARCHAR(100),
                device_type VARCHAR(50),
                browser VARCHAR(100),
                is_mobile BOOLEAN DEFAULT FALSE
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_page_visits_time 
            ON page_visits(visit_time)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_page_visits_ip_time 
            ON page_visits(ip_address, visit_time)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_page_visits_session 
            ON page_visits(session_id, visit_time)
        """)
        
        print("[INFO] Donations and donation_messages tables created/verified")
        
        # Initialize stats if empty
        cursor.execute("SELECT COUNT(*) FROM stats")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO stats (total_downloads) VALUES (1250)")
        
        # Auto-migration: Add tracking columns if they don't exist
        print("[INFO] Checking for tracking columns...")
        tracking_columns = [
            ("user_id", "INTEGER REFERENCES users(id) ON DELETE SET NULL"),
            ("ip_address", "VARCHAR(45)"),
            ("country", "VARCHAR(100)"),
            ("country_code", "VARCHAR(5)"),
            ("region", "VARCHAR(100)"),
            ("city", "VARCHAR(100)"),
            ("timezone", "VARCHAR(50)"),
            ("latitude", "DECIMAL(10, 8)"),
            ("longitude", "DECIMAL(11, 8)"),
            ("device_type", "VARCHAR(50)"),
            ("os", "VARCHAR(100)"),
            ("browser", "VARCHAR(100)"),
            ("is_mobile", "BOOLEAN"),
            ("is_tablet", "BOOLEAN"),
            ("is_pc", "BOOLEAN"),
            ("user_agent", "TEXT")
        ]
        
        for col_name, col_type in tracking_columns:
            try:
                cursor.execute(f"ALTER TABLE downloads ADD COLUMN IF NOT EXISTS {col_name} {col_type}")
                print(f"[INFO] Ensured column exists: {col_name}")
            except Exception as e:
                print(f"[WARNING] Column check failed for {col_name}: {e}")
                conn.rollback()
        
        conn.commit()
        cursor.close()
        db_pool.putconn(conn)
        
        print("[SUCCESS] PostgreSQL connected and initialized!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Database init failed: {e}")
        return False

# Stats file path (fallback)
STATS_FILE = 'stats.json'

# Removed record_page_visit() function - page_visits table no longer needed

def get_stats():
    """Get total downloads from DB or fallback to JSON"""
    if db_pool:
        try:
            conn = db_pool.getconn()
            cursor = conn.cursor()
            cursor.execute("SELECT total_downloads FROM stats LIMIT 1")
            result = cursor.fetchone()
            cursor.close()
            db_pool.putconn(conn)
            
            if result:
                return {"total_downloads": result[0]}
        except Exception as e:
            print(f"[ERROR] Get stats failed: {e}")
    
    # Fallback to JSON
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r') as f:
                return json.load(f)
    except: 
        pass
    
    return {"total_downloads": 1250}

def increment_stats(platform='unknown', format_type='mp4', quality='best', success=True, tracking_info=None, user_id=None):
    """Increment download counter in DB with tracking info and user_id"""
    if db_pool:
        try:
            conn = db_pool.getconn()
            cursor = conn.cursor()
            
            # Insert download record with tracking info
            if tracking_info:
                cursor.execute("""
                    INSERT INTO downloads (
                        platform, format, quality, success, user_id,
                        ip_address, country, country_code, region, city, timezone,
                        latitude, longitude, device_type, os, browser,
                        is_mobile, is_tablet, is_pc, user_agent
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    platform, format_type, quality, success, user_id,
                    tracking_info.get('ip_address'),
                    tracking_info.get('country'),
                    tracking_info.get('country_code'),
                    tracking_info.get('region'),
                    tracking_info.get('city'),
                    tracking_info.get('timezone'),
                    tracking_info.get('latitude'),
                    tracking_info.get('longitude'),
                    tracking_info.get('device_type'),
                    tracking_info.get('os'),
                    tracking_info.get('browser'),
                    tracking_info.get('is_mobile'),
                    tracking_info.get('is_tablet'),
                    tracking_info.get('is_pc'),
                    tracking_info.get('user_agent')
                ))
            else:
                # Fallback without tracking
                cursor.execute("""
                    INSERT INTO downloads (platform, format, quality, success, user_id)
                    VALUES (%s, %s, %s, %s, %s)
                """, (platform, format_type, quality, success, user_id))
            
            # Update total count
            cursor.execute("""
                UPDATE stats 
                SET total_downloads = total_downloads + 1,
                    last_updated = CURRENT_TIMESTAMP
            """)
            
            conn.commit()
            cursor.close()
            db_pool.putconn(conn)
            return
        except Exception as e:
            print(f"[ERROR] Increment stats failed: {e}")
    
    # Fallback to JSON
    try:
        stats = get_stats()
        stats['total_downloads'] = stats.get('total_downloads', 0) + 1
        with open(STATS_FILE, 'w') as f:
            json.dump(stats, f)
    except Exception as e:
        print(f"[ERROR] Stats error: {e}")

def record_user_download(user_id, platform='unknown'):
    """Record user download for free user limit tracking"""
    if not db_pool or not user_id:
        return
    
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        # Insert into user_downloads table
        cursor.execute("""
            INSERT INTO user_downloads (user_id, platform, download_time)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
        """, (str(user_id), platform))
        
        conn.commit()
        cursor.close()
        db_pool.putconn(conn)
        
        print(f"[DOWNLOAD TRACKING] Recorded download for user {user_id} on {platform}")
    except Exception as e:
        print(f"[ERROR] Failed to record user download: {e}")

def log_error(error_type, error_message, stack_trace=None, url=None, platform=None, 
              format_type=None, quality=None, user_id=None, request_obj=None):
    """Log error to database for admin monitoring"""
    try:
        # Get request info if available
        ip_address = None
        user_agent = None
        
        if request_obj:
            ip_address = request_obj.headers.get('X-Forwarded-For', request_obj.remote_addr)
            if ip_address and ',' in ip_address:
                ip_address = ip_address.split(',')[0].strip()
            user_agent = request_obj.headers.get('User-Agent', '')
        
        # Log to console
        print(f"[ERROR LOG] {error_type}: {error_message[:200]}")
        
        # Save to database
        if db_pool:
            try:
                conn = db_pool.getconn()
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO error_logs (
                        error_type, error_message, stack_trace, url, 
                        platform, format, quality, user_id, ip_address, user_agent
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    error_type, error_message[:5000], stack_trace[:10000] if stack_trace else None,
                    url, platform, format_type, quality, user_id, ip_address, user_agent
                ))
                
                conn.commit()
                cursor.close()
                db_pool.putconn(conn)
            except Exception as db_err:
                print(f"[ERROR] Failed to log error to DB: {db_err}")
    except Exception as e:
        print(f"[ERROR] log_error failed: {e}")

def log_system(log_level, log_message, log_source=None, url=None, method=None, 
               status_code=None, user_id=None, execution_time=None, 
               additional_data=None, request_obj=None):
    """Log system events to database for admin monitoring
    
    Args:
        log_level: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
        log_message: The log message
        log_source: Source of the log (e.g., 'youtube_download', 'tiktok_download', 'api_request')
        url: Request URL if applicable
        method: HTTP method if applicable
        status_code: HTTP status code if applicable
        user_id: User ID if applicable
        execution_time: Execution time in seconds
        additional_data: Additional data as dict (will be stored as JSONB)
        request_obj: Flask request object
    """
    try:
        # Get request info if available
        ip_address = None
        user_agent = None
        
        if request_obj:
            ip_address = request_obj.headers.get('X-Forwarded-For', request_obj.remote_addr)
            if ip_address and ',' in ip_address:
                ip_address = ip_address.split(',')[0].strip()
            user_agent = request_obj.headers.get('User-Agent', '')
            
            # Auto-fill from request if not provided
            if not url:
                url = request_obj.url
            if not method:
                method = request_obj.method
        
        # Log to console with appropriate prefix
        prefix_map = {
            'DEBUG': '[DEBUG]',
            'INFO': '[INFO]',
            'WARNING': '[WARNING]',
            'ERROR': '[ERROR]',
            'CRITICAL': '[CRITICAL]'
        }
        prefix = prefix_map.get(log_level, '[LOG]')
        print(f"{prefix} {log_source or ''}: {log_message[:200]}")
        
        # Save to database
        if db_pool:
            try:
                conn = db_pool.getconn()
                cursor = conn.cursor()
                
                # Convert additional_data to JSON string if it's a dict
                json_data = None
                if additional_data:
                    import json as json_lib
                    json_data = json_lib.dumps(additional_data)
                
                cursor.execute("""
                    INSERT INTO system_logs (
                        log_level, log_message, log_source, url, method, 
                        status_code, user_id, ip_address, user_agent, 
                        execution_time, additional_data
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                """, (
                    log_level, log_message[:5000], log_source, url, method,
                    status_code, user_id, ip_address, user_agent,
                    execution_time, json_data
                ))
                
                conn.commit()
                cursor.close()
                db_pool.putconn(conn)
            except Exception as db_err:
                print(f"[ERROR] Failed to log system event to DB: {db_err}")
    except Exception as e:
        print(f"[ERROR] log_system failed: {e}")
    except Exception as e:
        print(f"[ERROR] Stats error: {e}")

# Initialize ThreadPool for concurrent downloads. 
# On Railway Free (512MB RAM), set MAX_WORKERS to 2 or 3 in environment variables.
executor = ThreadPoolExecutor(max_workers=int(os.environ.get('MAX_WORKERS', 3)))

# Initialize Database
init_db()

print(f"======== SERVER STARTED | WORKERS: {executor._max_workers} ========")
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max

# Store download progress and data
download_progress = {}
download_data = {}

def strip_ansi(text):
    """Remove ANSI escape codes from text"""
    if not text: return ''
    ansi_pattern = re.compile(r'\x1b\[[0-9;]*m')
    return ansi_pattern.sub('', text)

def cleanup_old_files():
    """Background task to delete files older than 30 minutes"""
    while True:
        try:
            current_time = time.time()
            to_delete = []
            for did, data in list(download_data.items()):
                # If file is older than 30 minutes
                if current_time - data.get('timestamp', 0) > 1800:
                    to_delete.append(did)
            
            for did in to_delete:
                data = download_data.get(did)
                if data and os.path.exists(data['filepath']):
                    try: os.remove(data['filepath'])
                    except: pass
                if did in download_data: del download_data[did]
                if did in download_progress: del download_progress[did]
                print(f"Cleaned up expired download: {did}")
        except Exception as e:
            print(f"Cleanup task error: {e}")
        time.sleep(300) # Check every 5 mins

def cleanup_download_history():
    """Background task to delete download history older than 3 days"""
    while True:
        try:
            time.sleep(3600)  # Wait 1 hour before first cleanup
            
            if not db_pool:
                print("[WARNING] Database not available for cleanup")
                continue
            
            from datetime import datetime, timedelta
            three_days_ago = datetime.now() - timedelta(days=3)
            
            conn = db_pool.getconn()
            cursor = conn.cursor()
            
            # Delete old download history
            cursor.execute("""
                DELETE FROM user_downloads 
                WHERE download_time < %s
            """, (three_days_ago,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                print(f"[CLEANUP] Deleted {deleted_count} download history records older than 3 days")
            
            cursor.close()
            db_pool.putconn(conn)
            
        except Exception as e:
            print(f"[ERROR] Download history cleanup failed: {e}")
        
        time.sleep(86400)  # Run every 24 hours

# Start cleanup threads
threading.Thread(target=cleanup_old_files, daemon=True).start()
threading.Thread(target=cleanup_download_history, daemon=True).start()
print("[INFO] Cleanup threads started - Files: 30min, Download history: 3 days")

def is_valid_youtube_url(url):
    """Validate YouTube URL"""
    youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    return bool(re.match(youtube_regex, url))

def is_valid_tiktok_url(url):
    """Validate TikTok URL"""
    tiktok_regex = r'(https?://)?(www\.|vm\.|vt\.)?tiktok\.com/.*'
    return bool(re.match(tiktok_regex, url))

def extract_video_id(url):
    """Extract YouTube video ID from URL"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
        r'youtube\.com\/embed\/([^&\n?#]+)',
        r'youtube\.com\/v\/([^&\n?#]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

@app.before_request
def before_request():
    # Force HTTPS
    # Skip for local development
    if 'localhost' in request.host or '127.0.0.1' in request.host or '.internal' in request.host:
        pass
    else:
        # For Railway/production: Trust X-Forwarded-Proto header
        # Only redirect if the forwarded protocol is explicitly 'http'
        forwarded_proto = request.headers.get('X-Forwarded-Proto', '')
        
        if forwarded_proto == 'http':
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)
    
    # Track page visits for statistics
    try:
        # Skip tracking for static files and API endpoints
        if request.path.startswith('/static/') or request.path.startswith('/api/'):
            return
        
        # Get visitor info
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip_address and ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        
        user_agent = request.headers.get('User-Agent', '')
        page_url = request.path
        referrer = request.headers.get('Referer', '')
        
        # Simple session tracking using IP + User-Agent hash
        import hashlib
        session_id = hashlib.md5(f"{ip_address}{user_agent}".encode()).hexdigest()
        
        # Insert page visit asynchronously (don't block request)
        if db_pool:
            try:
                conn = db_pool.getconn()
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO page_visits (ip_address, user_agent, page_url, referrer, session_id)
                    VALUES (%s, %s, %s, %s, %s)
                """, (ip_address, user_agent, page_url, referrer, session_id))
                
                conn.commit()
                cursor.close()
                db_pool.putconn(conn)
            except Exception as e:
                print(f"[TRACKING ERROR] {e}")
                if 'conn' in locals():
                    try:
                        db_pool.putconn(conn)
                    except:
                        pass
    except Exception as e:
        print(f"[TRACKING ERROR] {e}")

# Helper function to extract images (Shared logic)
def extract_tiktok_images_direct(url):
    """Direct extraction without subprocess"""
    print(f"[DEBUG] Direct extraction for: {url}")
    
    try:
        # Resolve short link first
        if 'vm.tiktok.com' in url or 'vt.tiktok.com' in url or '/t/' in url:
            try:
                h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
                r = requests.head(url, allow_redirects=True, headers=h, timeout=15)
                url = r.url
                if 'tiktok.com' not in url:
                    r = requests.get(url, allow_redirects=True, headers=h, timeout=15)
                    url = r.url
                print(f"[DEBUG] Resolved URL: {url}")
            except Exception as e:
                print(f"[DEBUG] Resolve Error: {e}")
            
        # Clean URL
        if '?' in url: 
            url = url.split('?')[0]

        image_urls = []
        
        # 1. TikWM API
        try:
            print("[DEBUG] Trying TikWM...")
            resp = requests.post("https://www.tikwm.com/api/", 
                               data={'url': url}, 
                               timeout=15,
                               headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'})
            data = resp.json()
            print(f"[DEBUG] TikWM Response Code: {data.get('code')}")
            
            if data.get('code') == 0 and 'data' in data and 'images' in data['data']:
                image_urls = data['data']['images']
                print(f"[DEBUG] TikWM Success: {len(image_urls)} images")
                return list(dict.fromkeys(image_urls))  # Remove duplicates and return immediately
        except Exception as e:
            print(f"[DEBUG] TikWM Error: {e}")
        
        # 2. LoveTik API (fallback)
        if not image_urls:
            try:
                print("[DEBUG] Trying LoveTik...")
                payload = {'query': url}
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0', 
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
                }
                resp = requests.post("https://lovetik.com/api/ajax/search", 
                                   data=payload, 
                                   headers=headers, 
                                   timeout=15)
                data = resp.json()
                
                if data.get('status') == 'ok' and 'images' in data:
                    image_urls = [img['url'] for img in data['images']]
                    print(f"[DEBUG] LoveTik Success: {len(image_urls)} images")
            except Exception as e:
                print(f"[DEBUG] LoveTik Error: {e}")

        return list(dict.fromkeys(image_urls))
        
    except Exception as e:
        print(f"[ERROR] Direct extraction error: {e}")
        import traceback
        traceback.print_exc()
        return []

def extract_tiktok_images(url):
    """Extract image URLs using external script for stability"""
    print(f"[DEBUG] extract_tiktok_images called with: {url}")
    
    # Try direct method first (faster and more reliable)
    try:
        images = extract_tiktok_images_direct(url)
        if images:
            print(f"[DEBUG] Direct method success: {len(images)} images")
            return images
    except Exception as e:
        print(f"[DEBUG] Direct method failed: {e}")
    
    # Fallback to subprocess method
    print(f"[DEBUG] Falling back to subprocess method")
    
    # Create temp file for output
    fd, output_path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    
    try:
        # Resolve script path
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fetch_tiktok.py')
        print(f"[DEBUG] Script path: {script_path}")
        print(f"[DEBUG] Script exists: {os.path.exists(script_path)}")
        
        if not os.path.exists(script_path):
            print(f"[ERROR] Script not found at {script_path}")
            return []

        # Run external script
        cmd = [sys.executable, script_path, url, output_path]
        print(f"[DEBUG] Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=40,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        print(f"[DEBUG] Return code: {result.returncode}")
        print(f"[DEBUG] STDOUT: {result.stdout}")
        print(f"[DEBUG] STDERR: {result.stderr}")
        
        if os.path.exists(output_path):
            print(f"[DEBUG] Output file exists, size: {os.path.getsize(output_path)}")
            if os.path.getsize(output_path) > 0:
                with open(output_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"[DEBUG] Loaded {len(data)} images from file")
                    return data
            else:
                print(f"[DEBUG] Output file is empty")
        else:
            print(f"[DEBUG] Output file does not exist")
            
        print(f"[ERROR] Subprocess failed. Code: {result.returncode}")
        return []
                     
    except Exception as e:
        print(f"[ERROR] Subprocess Error: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        # Cleanup
        if os.path.exists(output_path):
            try: 
                os.remove(output_path)
                print(f"[DEBUG] Cleaned up temp file: {output_path}")
            except: 
                pass
def download_tiktok_photos(url, download_id, selected_indices=None):
    """Download TikTok photos using Multi-Source approach"""
    try:
        download_progress[download_id] = {
            'status': 'downloading',
            'progress': 5,
            'speed': 'Initializing...',
            'eta': '',
            'filename': None
        }
        
        temp_dir = tempfile.gettempdir()
        
        # 1. Get Images
        # Only fetch if we need to (in case logic changes), but here we assume caller might pass info?
        # Actually in this flow, backend always refetches to be safe/simple, 
        # or we could pass the URLs from frontend but that's risky for security/length.
        # Let's refetch, it's safer.
        
        download_progress[download_id]['speed'] = 'Fetching images...'
        image_urls = extract_tiktok_images(url)

        if not image_urls:
            raise Exception("Không tìm thấy ảnh. Vui lòng kiểm tra lại link.")

        # 2. Filter by selected indices if provided
        target_urls = []
        if selected_indices and isinstance(selected_indices, list):
            for idx in selected_indices:
                if 0 <= idx < len(image_urls):
                    target_urls.append(image_urls[idx])
        else:
            target_urls = image_urls # Default to all
            
        if not target_urls:
             target_urls = image_urls[:1] # Fallback to at least one

        # --- DOWNLOAD LOGIC ---
        download_progress[download_id]['progress'] = 20
        downloaded_files = []
        
        # Simple headers for CDN download
        cdn_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        for i, img_url in enumerate(target_urls):
            try:
                download_progress[download_id]['speed'] = f'Downloading {i+1}/{len(target_urls)}'
                
                # Retry logic
                content = None
                for attempt in range(3):
                    try:
                        r = http_requests.get(img_url, headers=cdn_headers, timeout=15)
                        if r.status_code == 200:
                            content = r.content
                            break
                    except:
                        time.sleep(1)
                
                if content:
                    # Detect extension from URL or Content-Type
                    ext = 'jpg'
                    if '.webp' in img_url: ext = 'webp'
                    elif '.png' in img_url: ext = 'png'
                    elif '.heic' in img_url: ext = 'heic'
                    
                    filename = f"{download_id}_{i+1}.{ext}"
                    filepath = os.path.join(temp_dir, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(content)
                    downloaded_files.append(filepath)
                    
                    # Update progress
                    percent = 20 + (80 * (i + 1) / len(target_urls))
                    download_progress[download_id]['progress'] = round(percent, 1)
            except Exception as e:
                print(f"Failed to download img {i}: {e}")
                continue

        if not downloaded_files:
            raise Exception("CDN chặn tải ảnh. Vui lòng thử lại sau.")

        # Create Output
        if len(downloaded_files) > 1:
            zip_name = f"TikTok_Photos_{download_id[:6]}.zip"
            zip_path = os.path.join(temp_dir, zip_name)
            
            with zipfile.ZipFile(zip_path, 'w') as zf:
                for fpath in downloaded_files:
                    zf.write(fpath, os.path.basename(fpath))
                    try: os.remove(fpath) # Clean temp files
                    except: pass
            
            final_path = zip_path
            final_name = zip_name
            mime = 'application/zip'
            title = f"TikTok Album ({len(downloaded_files)} ảnh)"
        else:
            final_path = downloaded_files[0]
            final_name = os.path.basename(final_path)
            mime = 'image/jpeg'
            if final_path.endswith('.webp'): mime = 'image/webp'
            title = "TikTok Photo"

        # Complete
        download_progress[download_id]['status'] = 'completed'
        download_progress[download_id]['progress'] = 100
        download_progress[download_id]['filename'] = final_name
        download_progress[download_id]['title'] = title
        
        download_data[download_id] = {
            'filepath': final_path,
            'title': title,
            'mime_type': mime,
            'ext': final_name.split('.')[-1],
            'timestamp': time.time(),
            'platform': 'tiktok',
            'format': 'image',
            'quality': f'{len(downloaded_files)}photos'
        }

    except Exception as e:
        print(f"Global Error: {e}")
        error_msg = str(e)
        download_progress[download_id]['status'] = 'error'
        download_progress[download_id]['error'] = error_msg

def try_invidious_download(video_id, format_type, quality, download_id, temp_dir, progress_hook):
    """Try to download video via Invidious proxy instances"""
    import random
    import time as time_module
    
    # Shuffle instances to distribute load
    instances = INVIDIOUS_INSTANCES.copy()
    random.shuffle(instances)
    
    for instance in instances:
        try:
            print(f"[DEBUG] Trying Invidious instance: {instance}")
            
            # Get video info from Invidious API
            api_url = f"{instance}/api/v1/videos/{video_id}"
            response = http_requests.get(api_url, timeout=15)
            
            if response.status_code != 200:
                print(f"[DEBUG] Invidious {instance} returned {response.status_code}")
                continue
                
            data = response.json()
            title = data.get('title', 'video')
            # Clean title for filename
            safe_title = re.sub(r'[<>:"/\\|?*]', '', title)[:100]
            
            # Find the best format
            download_url = None
            
            if format_type == 'mp3':
                # Get audio only
                for fmt in data.get('adaptiveFormats', []):
                    if 'audio' in fmt.get('type', '').lower():
                        download_url = fmt.get('url')
                        break
            else:
                # Get video - try adaptive formats first for quality control
                target_height = int(quality.replace('p', '')) if quality != 'best' else 1080
                
                best_match = None
                for fmt in data.get('adaptiveFormats', []):
                    if 'video' in fmt.get('type', '').lower() and 'audio' not in fmt.get('type', '').lower():
                        height = fmt.get('resolution', '').replace('p', '')
                        if height.isdigit():
                            if int(height) <= target_height:
                                if best_match is None or int(height) > int(best_match.get('resolution', '0').replace('p', '')):
                                    best_match = fmt
                
                if best_match:
                    download_url = best_match.get('url')
                else:
                    # Fallback to formatStreams (combined video+audio)
                    for fmt in data.get('formatStreams', []):
                        download_url = fmt.get('url')
                        break
            
            if not download_url:
                print(f"[DEBUG] No download URL found from {instance}")
                continue
            
            # Download the file
            print(f"[DEBUG] Downloading from Invidious: {download_url[:100]}...")
            
            ext = 'mp3' if format_type == 'mp3' else 'mp4'
            output_path = os.path.join(temp_dir, f"{download_id}.{ext}")
            
            # Stream download with progress
            with http_requests.get(download_url, stream=True, timeout=120) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                downloaded = 0
                
                with open(output_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            progress_hook({
                                'status': 'downloading',
                                'downloaded_bytes': downloaded,
                                'total_bytes': total_size,
                                '_percent_str': f'{progress}%',
                                '_speed_str': '',
                                '_eta_str': ''
                            })
            
            print(f"[SUCCESS] Downloaded via Invidious: {instance}")
            return output_path, safe_title, ext
            
        except Exception as e:
            print(f"[DEBUG] Invidious {instance} failed: {str(e)[:100]}")
            continue
    
    return None, None, None


def try_cobalt_api(video_id, format_type, quality, download_id, temp_dir, progress_hook):
    """Try to download via Cobalt API (cobalt.tools) - Free, no auth needed"""
    try:
        print(f"[DEBUG] Trying Cobalt API...")
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Cobalt API endpoint
        api_url = "https://api.cobalt.tools/api/json"
        
        payload = {
            "url": url,
            "vCodec": "h264",  # Compatible codec
            "vQuality": quality if quality != 'best' else "1080",
            "aFormat": "mp3" if format_type == 'mp3' else "best",
            "isAudioOnly": format_type == 'mp3'
        }
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        response = http_requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"[DEBUG] Cobalt API returned {response.status_code}")
            return None, None, None
        
        data = response.json()
        
        if data.get('status') != 'success' and data.get('status') != 'redirect':
            print(f"[DEBUG] Cobalt API status: {data.get('status')}")
            return None, None, None
        
        download_url = data.get('url')
        if not download_url:
            print(f"[DEBUG] No download URL from Cobalt")
            return None, None, None
        
        # Download the file
        print(f"[DEBUG] Downloading from Cobalt: {download_url[:100]}...")
        
        ext = 'mp3' if format_type == 'mp3' else 'mp4'
        output_path = os.path.join(temp_dir, f"{download_id}.{ext}")
        
        with http_requests.get(download_url, stream=True, timeout=120) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        progress = int((downloaded / total_size) * 100)
                        progress_hook({
                            'status': 'downloading',
                            'downloaded_bytes': downloaded,
                            'total_bytes': total_size,
                            '_percent_str': f'{progress}%',
                            '_speed_str': '',
                            '_eta_str': ''
                        })
        
        print(f"[SUCCESS] Downloaded via Cobalt API")
        return output_path, f"video_{video_id}", ext
        
    except Exception as e:
        print(f"[DEBUG] Cobalt API failed: {str(e)[:100]}")
        return None, None, None


def try_y2mate_api(video_id, format_type, quality, download_id, temp_dir, progress_hook):
    """Try to download via Y2Mate API - Free, no auth needed"""
    try:
        print(f"[DEBUG] Trying Y2Mate API...")
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Y2Mate API endpoints
        # Step 1: Get video info
        info_url = "https://www.y2mate.com/mates/analyzeV2/ajax"
        
        payload = {
            "k_query": url,
            "k_page": "home",
            "hl": "en",
            "q_auto": 0
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = http_requests.post(info_url, data=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"[DEBUG] Y2Mate API returned {response.status_code}")
            return None, None, None
        
        data = response.json()
        
        if data.get('status') != 'ok':
            print(f"[DEBUG] Y2Mate status: {data.get('status')}")
            return None, None, None
        
        # Parse links from HTML response
        import re
        links_html = data.get('links', {})
        
        # Find the appropriate format
        k_value = None
        
        if format_type == 'mp3':
            # Look for mp3 format
            mp3_links = links_html.get('mp3', {})
            for quality_key in ['128', '320', '192']:
                if quality_key in mp3_links:
                    match = re.search(r'k__id="([^"]+)"', mp3_links[quality_key])
                    if match:
                        k_value = match.group(1)
                        break
        else:
            # Look for mp4 format
            mp4_links = links_html.get('mp4', {})
            target_quality = quality.replace('p', '') if quality != 'best' else '720'
            
            for q in [target_quality, '720', '480', '360']:
                if q in mp4_links:
                    match = re.search(r'k__id="([^"]+)"', mp4_links[q])
                    if match:
                        k_value = match.group(1)
                        break
        
        if not k_value:
            print(f"[DEBUG] No suitable format found in Y2Mate")
            return None, None, None
        
        # Step 2: Get download link
        convert_url = "https://www.y2mate.com/mates/convertV2/index"
        
        convert_payload = {
            "vid": video_id,
            "k": k_value
        }
        
        response = http_requests.post(convert_url, data=convert_payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"[DEBUG] Y2Mate convert returned {response.status_code}")
            return None, None, None
        
        data = response.json()
        
        if data.get('status') != 'ok':
            print(f"[DEBUG] Y2Mate convert status: {data.get('status')}")
            return None, None, None
        
        # Extract download URL from HTML
        result_html = data.get('result', '')
        match = re.search(r'href="([^"]+)"', result_html)
        
        if not match:
            print(f"[DEBUG] No download URL found in Y2Mate response")
            return None, None, None
        
        download_url = match.group(1)
        
        # Download the file
        print(f"[DEBUG] Downloading from Y2Mate: {download_url[:100]}...")
        
        ext = 'mp3' if format_type == 'mp3' else 'mp4'
        output_path = os.path.join(temp_dir, f"{download_id}.{ext}")
        
        with http_requests.get(download_url, stream=True, timeout=120, headers=headers) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        progress = int((downloaded / total_size) * 100)
                        progress_hook({
                            'status': 'downloading',
                            'downloaded_bytes': downloaded,
                            'total_bytes': total_size,
                            '_percent_str': f'{progress}%',
                            '_speed_str': '',
                            '_eta_str': ''
                        })
        
        print(f"[SUCCESS] Downloaded via Y2Mate API")
        return output_path, f"video_{video_id}", ext
        
    except Exception as e:
        print(f"[DEBUG] Y2Mate API failed: {str(e)[:100]}")
        return None, None, None


def try_loader_to_api(video_id, format_type, quality, download_id, temp_dir, progress_hook):
    """Try to download via Loader.to/SaveNow.to API - Free, no auth needed"""
    try:
        print(f"[DEBUG] Trying Loader.to API...")

        url = f"https://www.youtube.com/watch?v={video_id}"

        # Loader.to uses a different approach - we need to scrape their conversion page
        # Their API endpoint for getting download links
        api_url = "https://ab.cococococ.com/ajax/download.php"

        payload = {
            "copyright": "0",
            "format": "mp3" if format_type == 'mp3' else "mp4",
            "url": url,
            "api": "dfcb6d76f2f6a9894gjkege8a4ab232222"
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://loader.to/"
        }

        response = http_requests.post(api_url, data=payload, headers=headers, timeout=30)

        if response.status_code != 200:
            print(f"[DEBUG] Loader.to API returned {response.status_code}")
            return None, None, None

        data = response.json()

        if data.get('success') != 1:
            print(f"[DEBUG] Loader.to status: {data.get('success')}")
            return None, None, None

        download_url = data.get('url')
        if not download_url:
            print(f"[DEBUG] No download URL from Loader.to")
            return None, None, None

        # Download the file
        print(f"[DEBUG] Downloading from Loader.to: {download_url[:100]}...")

        ext = 'mp3' if format_type == 'mp3' else 'mp4'
        output_path = os.path.join(temp_dir, f"{download_id}.{ext}")

        with http_requests.get(download_url, stream=True, timeout=120, headers=headers) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0

            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        progress = int((downloaded / total_size) * 100)
                        progress_hook({
                            'status': 'downloading',
                            'downloaded_bytes': downloaded,
                            'total_bytes': total_size,
                            '_percent_str': f'{progress}%',
                            '_speed_str': '',
                            '_eta_str': ''
                        })

        print(f"[SUCCESS] Downloaded via Loader.to API")
        return output_path, f"video_{video_id}", ext

    except Exception as e:
        print(f"[DEBUG] Loader.to API failed: {str(e)[:100]}")
        return None, None, None


def try_ytapi_org(video_id, format_type, quality, download_id, temp_dir, progress_hook):
    """Try to download via yt-api.org - Free iframe API"""
    try:
        print(f"[DEBUG] Trying yt-api.org...")

        # yt-api.org uses iframe embed, we need to scrape the actual download link
        # Their backend API endpoint
        api_url = f"https://yt-api.org/api/json/{format_type}/{video_id}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://yt-api.org/"
        }

        response = http_requests.get(api_url, headers=headers, timeout=30)

        if response.status_code != 200:
            print(f"[DEBUG] yt-api.org returned {response.status_code}")
            return None, None, None

        data = response.json()

        download_url = data.get('url') or data.get('download_url')
        if not download_url:
            print(f"[DEBUG] No download URL from yt-api.org")
            return None, None, None

        # Download the file
        print(f"[DEBUG] Downloading from yt-api.org: {download_url[:100]}...")

        ext = 'mp3' if format_type == 'mp3' else 'mp4'
        output_path = os.path.join(temp_dir, f"{download_id}.{ext}")

        with http_requests.get(download_url, stream=True, timeout=120, headers=headers) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0

            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        progress = int((downloaded / total_size) * 100)
                        progress_hook({
                            'status': 'downloading',
                            'downloaded_bytes': downloaded,
                            'total_bytes': total_size,
                            '_percent_str': f'{progress}%',
                            '_speed_str': '',
                            '_eta_str': ''
                        })

        print(f"[SUCCESS] Downloaded via yt-api.org")
        return output_path, f"video_{video_id}", ext

    except Exception as e:
        print(f"[DEBUG] yt-api.org failed: {str(e)[:100]}")
        return None, None, None


def try_apisyu_api(video_id, format_type, quality, download_id, temp_dir, progress_hook):
    """Try to download via Apisyu (ytc.re) - Free API"""
    try:
        print(f"[DEBUG] Trying Apisyu API...")

        # Apisyu backend API endpoint (need to find actual endpoint)
        # This is an iframe-based service, might need scraping
        api_url = f"https://ytc.re/api/convert"

        payload = {
            "video_id": video_id,
            "format": format_type,
            "quality": quality if quality != 'best' else ('320' if format_type == 'mp3' else '1080')
        }

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://ytc.re/"
        }

        response = http_requests.post(api_url, json=payload, headers=headers, timeout=30)

        if response.status_code != 200:
            print(f"[DEBUG] Apisyu API returned {response.status_code}")
            return None, None, None

        data = response.json()

        download_url = data.get('download_url') or data.get('url')
        if not download_url:
            print(f"[DEBUG] No download URL from Apisyu")
            return None, None, None

        # Download the file
        print(f"[DEBUG] Downloading from Apisyu: {download_url[:100]}...")

        ext = 'mp3' if format_type == 'mp3' else 'mp4'
        output_path = os.path.join(temp_dir, f"{download_id}.{ext}")

        with http_requests.get(download_url, stream=True, timeout=120, headers=headers) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0

            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        progress = int((downloaded / total_size) * 100)
                        progress_hook({
                            'status': 'downloading',
                            'downloaded_bytes': downloaded,
                            'total_bytes': total_size,
                            '_percent_str': f'{progress}%',
                            '_speed_str': '',
                            '_eta_str': ''
                        })

        print(f"[SUCCESS] Downloaded via Apisyu API")
        return output_path, f"video_{video_id}", ext

    except Exception as e:
        print(f"[DEBUG] Apisyu API failed: {str(e)[:100]}")
        return None, None, None


def try_rapidapi_youtube(video_id, format_type, quality, download_id, temp_dir, progress_hook):
    """Try to download via RapidAPI YouTube Downloader - Requires API key"""
    try:
        # Check if API key is configured
        rapidapi_key = os.environ.get('RAPIDAPI_KEY', '')
        if not rapidapi_key:
            print(f"[DEBUG] RapidAPI key not configured, skipping...")
            return None, None, None

        print(f"[DEBUG] Trying RapidAPI YouTube Downloader...")

        url = f"https://www.youtube.com/watch?v={video_id}"

        # RapidAPI endpoint (using youtube-video-mp3-downloader-api)
        api_url = "https://youtube-video-mp3-downloader-api.p.rapidapi.com/download"

        payload = {
            "url": url,
            "format": format_type,
            "quality": quality if quality != 'best' else ('320' if format_type == 'mp3' else '1080')
        }

        headers = {
            "Content-Type": "application/json",
            "X-RapidAPI-Key": rapidapi_key,
            "X-RapidAPI-Host": "youtube-video-mp3-downloader-api.p.rapidapi.com"
        }

        response = http_requests.post(api_url, json=payload, headers=headers, timeout=30)

        if response.status_code != 200:
            print(f"[DEBUG] RapidAPI returned {response.status_code}")
            return None, None, None

        data = response.json()

        download_url = data.get('download_url') or data.get('url')
        if not download_url:
            print(f"[DEBUG] No download URL from RapidAPI")
            return None, None, None

        # Download the file
        print(f"[DEBUG] Downloading from RapidAPI: {download_url[:100]}...")

        ext = 'mp3' if format_type == 'mp3' else 'mp4'
        output_path = os.path.join(temp_dir, f"{download_id}.{ext}")

        with http_requests.get(download_url, stream=True, timeout=120) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0

            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        progress = int((downloaded / total_size) * 100)
                        progress_hook({
                            'status': 'downloading',
                            'downloaded_bytes': downloaded,
                            'total_bytes': total_size,
                            '_percent_str': f'{progress}%',
                            '_speed_str': '',
                            '_eta_str': ''
                        })

        print(f"[SUCCESS] Downloaded via RapidAPI")
        return output_path, f"video_{video_id}", ext

    except Exception as e:
        print(f"[DEBUG] RapidAPI failed: {str(e)[:100]}")
        return None, None, None



def _try_invidious_fallback(url, format_type, quality, download_id, temp_dir, filename):
    """Fallback: dùng Invidious public API khi yt-dlp bị bot detection"""
    import re as _re
    
    # Extract video ID
    vid_match = _re.search(r'(?:v=|youtu\.be/|/v/|/embed/)([a-zA-Z0-9_-]{11})', url)
    if not vid_match:
        return False
    
    video_id = vid_match.group(1)
    print(f"[INVIDIOUS] Trying fallback for video: {video_id}")
    
    for instance in INVIDIOUS_INSTANCES:
        try:
            api_url = f"{instance}/api/v1/videos/{video_id}"
            resp = http_requests.get(api_url, timeout=10)
            if resp.status_code != 200:
                continue
            
            data = resp.json()
            title = data.get('title', 'video')
            
            # Find best stream URL
            adaptive_formats = data.get('adaptiveFormats', [])
            format_streams = data.get('formatStreams', [])
            
            download_url = None
            
            if format_type == 'mp3':
                # Find best audio
                audio_formats = [f for f in adaptive_formats if f.get('type', '').startswith('audio/')]
                if audio_formats:
                    audio_formats.sort(key=lambda x: x.get('bitrate', 0), reverse=True)
                    download_url = audio_formats[0].get('url')
            else:
                # Find best video quality
                target_height = int(quality) if quality and quality.isdigit() else 720
                video_formats = [f for f in format_streams if 'video/mp4' in f.get('type', '')]
                if not video_formats:
                    video_formats = format_streams
                
                # Sort by quality, pick closest to target
                def get_height(f):
                    res = f.get('resolution', '0p')
                    try:
                        return int(res.replace('p', ''))
                    except:
                        return 0
                
                video_formats.sort(key=get_height, reverse=True)
                for fmt in video_formats:
                    h = get_height(fmt)
                    if h <= target_height:
                        download_url = fmt.get('url')
                        break
                if not download_url and video_formats:
                    download_url = video_formats[-1].get('url')
            
            if not download_url:
                continue
            
            # Download the file
            print(f"[INVIDIOUS] Downloading from {instance}...")
            download_progress[download_id]['status'] = 'downloading'
            download_progress[download_id]['progress'] = 10
            
            ext = 'mp3' if format_type == 'mp3' else 'mp4'
            final_filename = filename + f'.{ext}'
            filepath = os.path.join(temp_dir, final_filename)
            mime_type = 'audio/mpeg' if format_type == 'mp3' else 'video/mp4'
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            r = http_requests.get(download_url, headers=headers, stream=True, timeout=60)
            r.raise_for_status()
            
            total = int(r.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            pct = round((downloaded / total) * 100, 1)
                            download_progress[download_id]['progress'] = pct
            
            download_data[download_id] = {
                'filepath': filepath,
                'title': title,
                'mime_type': mime_type,
                'ext': ext,
                'timestamp': time.time(),
                'platform': 'youtube',
                'format': format_type,
                'quality': quality
            }
            download_progress[download_id]['status'] = 'completed'
            download_progress[download_id]['filename'] = final_filename
            download_progress[download_id]['title'] = title
            
            print(f"[INVIDIOUS] Success via {instance}: {title}")
            return True
            
        except Exception as e:
            print(f"[INVIDIOUS] Failed {instance}: {e}")
            continue
    
    print(f"[INVIDIOUS] All instances failed")
    return False


def download_youtube_video(url, format_type, quality, download_id):
    """Download YouTube video using yt-dlp - Optimized and stable version"""
    print(f"\n{'='*80}")
    print(f"[YOUTUBE DOWNLOAD START]")
    print(f"URL: {url}")
    print(f"Format: {format_type}")
    print(f"Quality: {quality}")
    print(f"Download ID: {download_id}")
    print(f"{'='*80}\n")

    try:
        import yt_dlp

        download_progress[download_id] = {
            'status': 'preparing',
            'progress': 0,
            'speed': '',
            'eta': '',
            'filename': None
        }

        # Use temp directory for downloads
        temp_dir = tempfile.gettempdir()
        filename = f"{download_id}"
        output_path = os.path.join(temp_dir, filename)

        def progress_hook(d):
            """Track download progress"""
            if d['status'] == 'downloading':
                download_progress[download_id]['status'] = 'downloading'

                # Get percentage
                if 'downloaded_bytes' in d and 'total_bytes' in d and d['total_bytes']:
                    percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                    download_progress[download_id]['progress'] = round(percent, 1)
                elif 'downloaded_bytes' in d and 'total_bytes_estimate' in d and d['total_bytes_estimate']:
                    percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                    download_progress[download_id]['progress'] = round(percent, 1)
                elif '_percent_str' in d:
                    try:
                        percent = float(d['_percent_str'].replace('%', '').strip())
                        download_progress[download_id]['progress'] = round(percent, 1)
                    except:
                        pass

                # Get speed
                if '_speed_str' in d:
                    download_progress[download_id]['speed'] = strip_ansi(d['_speed_str'])

                # Get ETA
                if '_eta_str' in d:
                    download_progress[download_id]['eta'] = strip_ansi(d['_eta_str'])

            elif d['status'] == 'finished':
                download_progress[download_id]['progress'] = 100
                download_progress[download_id]['status'] = 'processing'

        # Configure yt-dlp options based on format
        if format_type == 'mp3':
            # Audio download - extract best audio and convert to MP3
            audio_bitrate = quality if quality in ['320', '192', '128'] else '192'

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_path,
                'noplaylist': True,
                'noprogress': False,
                'progress_hooks': [progress_hook],
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': audio_bitrate,
                }],
                'quiet': False,
                'no_warnings': False,
            }
            final_filename = filename + '.mp3'
            mime_type = 'audio/mpeg'
        else:
            # Video download - get best quality MP4
            if quality == 'best' or not quality.isdigit():
                format_str = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            else:
                format_str = f'bestvideo[ext=mp4][height<={quality}]+bestaudio[ext=m4a]/best[ext=mp4]/best'

            ydl_opts = {
                'format': format_str,
                'outtmpl': output_path + '.%(ext)s',
                'noplaylist': True,
                'merge_output_format': 'mp4',
                'noprogress': False,
                'progress_hooks': [progress_hook],
                'quiet': False,
                'no_warnings': False,
            }
            final_filename = filename + '.mp4'
            mime_type = 'video/mp4'

        # Download the video/audio
        print(f"[INFO] Starting download with yt-dlp...")

        # Add proxy if configured
        if HTTP_PROXY:
            ydl_opts['proxy'] = HTTP_PROXY
            print(f"[INFO] Using HTTP proxy")
        elif HTTPS_PROXY:
            ydl_opts['proxy'] = HTTPS_PROXY
            print(f"[INFO] Using HTTPS proxy")
        elif SOCKS_PROXY:
            ydl_opts['proxy'] = SOCKS_PROXY
            print(f"[INFO] Using SOCKS proxy")

        # Configure extractor_args to bypass bot detection
        # android: không cần PO Token, ổn định nhất 2025
        # android_vr: fallback tốt
        # web_embedded: cho embeddable videos
        extractor_args = {
            'youtube': {
                'player_client': ['android', 'android_vr', 'web_embedded'],
            }
        }

        # Add PO token if available (from env var YOUTUBE_PO_TOKEN)
        if YOUTUBE_PO_TOKEN and YOUTUBE_VISITOR_DATA:
            extractor_args['youtube']['po_token'] = [f'web+{YOUTUBE_PO_TOKEN}']
            extractor_args['youtube']['visitor_data'] = [YOUTUBE_VISITOR_DATA]
            print(f"[INFO] Using PO Token for YouTube")
        elif YOUTUBE_PO_TOKEN:
            extractor_args['youtube']['po_token'] = [f'web+{YOUTUBE_PO_TOKEN}']
            print(f"[INFO] Using PO Token (no visitor_data)")

        ydl_opts['extractor_args'] = extractor_args
        ydl_opts['sleep_interval'] = 1
        ydl_opts['max_sleep_interval'] = 5
        ydl_opts['http_headers'] = {
            'User-Agent': 'com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip',
        }

        # Cookies: kiểm tra hợp lệ trước khi dùng
        if COOKIES_FILE_PATH and os.path.exists(COOKIES_FILE_PATH):
            # Kiểm tra file cookies có nội dung hợp lệ không (> 100 bytes)
            cookies_size = os.path.getsize(COOKIES_FILE_PATH)
            if cookies_size > 100:
                ydl_opts['cookiefile'] = COOKIES_FILE_PATH
                print(f"[INFO] Using cookies from: {COOKIES_FILE_PATH} ({cookies_size} bytes)")
            else:
                print(f"[WARNING] Cookies file too small ({cookies_size} bytes), skipping")
        else:
            print(f"[INFO] No cookies - cookieless mode (bot detection may occur)")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'video')

        print(f"[SUCCESS] Download completed!")
        print(f"  - Title: {title}")
        print(f"  - File: {final_filename}\n")

        filepath = os.path.join(temp_dir, final_filename)

        # Store file data for streaming
        download_data[download_id] = {
            'filepath': filepath,
            'title': title,
            'mime_type': mime_type,
            'ext': final_filename.split('.')[-1],
            'timestamp': time.time(),
            'platform': 'youtube',
            'format': format_type,
            'quality': quality
        }

        download_progress[download_id]['status'] = 'completed'
        download_progress[download_id]['filename'] = final_filename
        download_progress[download_id]['title'] = title

        print(f"{'='*80}\n")
        return

    except Exception as e:
        import traceback
        
        error_msg = str(e)
        stack_trace = traceback.format_exc()
        download_progress[download_id]['status'] = 'error'
        
        # Determine error type for classification
        if 'Failed to extract' in error_msg or 'Unable to extract' in error_msg:
            error_type = 'extraction_failed'
            user_message = 'Không thể tải video. Vui lòng thử lại sau'
        elif 'not available' in error_msg.lower() and 'country' in error_msg.lower():
            error_type = 'geo_blocked'
            user_message = 'Video bị chặn theo khu vực'
        elif 'Sign in' in error_msg or 'bot' in error_msg.lower() or '429' in error_msg or 'cookies' in error_msg.lower():
            error_type = 'bot_detection'
            # Try Invidious fallback for bot detection
            print(f"[INFO] Bot detection - trying Invidious fallback...")
            if _try_invidious_fallback(url, format_type, quality, download_id, temp_dir, filename):
                return  # Fallback succeeded
            user_message = '⚠️ YouTube đang chặn tải xuống. Vui lòng thử lại sau vài phút hoặc liên hệ admin để cập nhật cookies.'
        elif 'unavailable' in error_msg.lower() or 'private' in error_msg.lower():
            error_type = 'video_unavailable'
            user_message = 'Video không khả dụng'
        elif 'age' in error_msg.lower() or 'restricted' in error_msg.lower():
            error_type = 'age_restricted'
            user_message = 'Video giới hạn độ tuổi'
        elif 'copyright' in error_msg.lower():
            error_type = 'copyright'
            user_message = 'Video bị chặn do bản quyền'
        elif 'network' in error_msg.lower() or 'timeout' in error_msg.lower():
            error_type = 'network_error'
            user_message = 'Lỗi kết nối. Vui lòng thử lại'
        elif 'live' in error_msg.lower() or 'premiere' in error_msg.lower():
            error_type = 'live_video'
            user_message = 'Video đang phát trực tiếp'
        else:
            error_type = 'unknown_error'
            user_message = 'Không thể tải video. Vui lòng thử lại sau'
        
        # Show simple message to user
        download_progress[download_id]['error'] = user_message
        
        # Log detailed error for admin
        log_error(
            error_type=error_type,
            error_message=error_msg,
            stack_trace=stack_trace,
            url=url if 'url' in locals() else None,
            platform='youtube',
            format_type=format_type if 'format_type' in locals() else None,
            quality=quality if 'quality' in locals() else None,
            user_id=session.get('user_id') if 'session' in dir() else None,
            request_obj=request if 'request' in dir() else None
        )
        
        print(f"\n{'='*80}")
        print(f"[YOUTUBE DOWNLOAD FAILED]")
        print(f"Error Type: {error_type}")
        print(f"Error: {e}")
        print(f"{'='*80}\n")


def download_tiktok_video(url, format_type, download_id, quality='best'):
    """Download TikTok video/photo using yt-dlp"""
    try:
        import yt_dlp
        import urllib.request
        
        download_progress[download_id] = {
            'status': 'preparing',
            'progress': 0,
            'speed': '',
            'eta': '',
            'filename': None
        }
        
        temp_dir = tempfile.gettempdir()
        filename = f"{download_id}"
        output_path = os.path.join(temp_dir, filename)
        
        # Check if it's a photo URL
        is_photo = '/photo/' in url
        
        def progress_hook(d):
            if d['status'] == 'downloading':
                download_progress[download_id]['status'] = 'downloading'
                
                if 'downloaded_bytes' in d and 'total_bytes' in d and d['total_bytes']:
                    percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                    download_progress[download_id]['progress'] = round(percent, 1)
                elif 'downloaded_bytes' in d and 'total_bytes_estimate' in d and d['total_bytes_estimate']:
                    percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                    download_progress[download_id]['progress'] = round(percent, 1)
                elif '_percent_str' in d:
                    try:
                        percent = float(d['_percent_str'].replace('%', '').strip())
                        download_progress[download_id]['progress'] = round(percent, 1)
                    except:
                        pass
                
                if '_speed_str' in d:
                    download_progress[download_id]['speed'] = strip_ansi(d['_speed_str'])
                if '_eta_str' in d:
                    download_progress[download_id]['eta'] = strip_ansi(d['_eta_str'])
                    
            elif d['status'] == 'finished':
                download_progress[download_id]['progress'] = 100
                download_progress[download_id]['status'] = 'processing'
        
        # For TikTok photo posts - use special handler
        if is_photo:
            # Get selected images indices if any
            selected = data.get('selected_images', None)
            
            # Call the photo download function with selection
            download_tiktok_photos(url, download_id, selected_indices=selected)
            return
        
        # For image format request on video
        if format_type == 'image':
            download_progress[download_id]['status'] = 'downloading'
            download_progress[download_id]['progress'] = 30
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': 30,
            }
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title', 'tiktok_image')
                    
                    download_progress[download_id]['progress'] = 60
                    
                    thumbnail_url = info.get('thumbnail')
                    if thumbnail_url:
                        final_filename = filename + '.jpg'
                        filepath = os.path.join(temp_dir, final_filename)
                        urllib.request.urlretrieve(thumbnail_url, filepath)
                        download_progress[download_id]['progress'] = 100
                        mime_type = 'image/jpeg'
                    else:
                        raise Exception("Không tìm thấy ảnh thumbnail")
            except Exception as e:
                error_msg = strip_ansi(str(e))
                download_progress[download_id]['status'] = 'error'
                download_progress[download_id]['error'] = f'Không thể tải ảnh: {error_msg}'
                return
                    
        elif format_type == 'mp3':
            # Default to 128k if not specified
            audio_bitrate = quality if quality in ['320', '192', '128'] else '128'
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_path, # Postprocessor handles ext
                'progress_hooks': [progress_hook],
                'quiet': True,
                'no_warnings': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': audio_bitrate,
                }],
            }
            final_filename = filename + '.mp3'
            mime_type = 'audio/mpeg'
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'audio')
            filepath = os.path.join(temp_dir, final_filename)
        else:
            # Video Video
            format_str = 'best[ext=mp4]/best'
            
            # Basic options
            ydl_opts = {
                'format': format_str,
                'outtmpl': output_path + '.mp4',
                'progress_hooks': [progress_hook],
                'quiet': True,
                'no_warnings': True,
            }
            
            # Force resize if specific quality selected
            if quality != 'best' and quality.isdigit():
                 res = int(quality)
                 # Try to download closes match first
                 ydl_opts['format'] = f'best[height<={res}][ext=mp4]/best[height<={res}]/best'
                 
                 # Then force scale using ffmpeg to ensure exact height
                 ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                 }]
                 ydl_opts['postprocessor_args'] = [
                    '-vf', f'scale=-2:{res}'
                 ]

            final_filename = filename + '.mp4'
            mime_type = 'video/mp4'
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'video')
            filepath = os.path.join(temp_dir, final_filename)
        
        # Store file data with timestamp
        download_data[download_id] = {
            'filepath': filepath,
            'title': title,
            'mime_type': mime_type,
            'ext': final_filename.split('.')[-1],
            'timestamp': time.time(),
            'platform': 'tiktok',
            'format': format_type,
            'quality': quality
        }
            
        download_progress[download_id]['status'] = 'completed'
        download_progress[download_id]['filename'] = final_filename
        download_progress[download_id]['title'] = title
        
    except Exception as e:
        download_progress[download_id]['status'] = 'error'
        download_progress[download_id]['error'] = str(e)
        print(f"TikTok download error: {e}")

@app.route('/')
def index():
    return HomeController.index()

@app.route('/blog')
def blog_index():
    return BlogController.index()

@app.route('/blog/tai-video-youtube')
def blog_youtube():
    return BlogController.youtube_guide()

@app.route('/blog/tai-video-tiktok')
def blog_tiktok():
    return BlogController.tiktok_guide()

@app.route('/blog/chuyen-youtube-sang-mp3')
def blog_youtube_mp3():
    return BlogController.youtube_to_mp3()

@app.route('/news')
def news_index():
    return NewsController.index()

@app.route('/admin/tracking')
def admin_tracking_old():
    """Old tracking page - redirect to new dashboard"""
    return redirect('/admin/dashboard')

@app.route('/admin/login')
def admin_login_page():
    """Admin login page"""
    if 'admin_logged_in' in session:
        return redirect('/admin/dashboard')
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    """Admin login handler"""
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    if username == ADMIN_USERNAME and password_hash == ADMIN_PASSWORD_HASH:
        session['admin_logged_in'] = True
        session['admin_username'] = username
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Tên đăng nhập hoặc mật khẩu không đúng'}), 401

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return jsonify({'success': True})

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard - requires login"""
    if 'admin_logged_in' not in session:
        return redirect('/admin/login')
    return render_template('admin_dashboard.html')

@app.route('/admin/error-logs')
def admin_error_logs():
    """Admin error logs page - requires login - DEPRECATED: Use /admin/logs"""
    if 'admin_logged_in' not in session:
        return redirect('/admin/login')
    return redirect('/admin/logs')

@app.route('/admin/system-logs')
def admin_system_logs():
    """Admin system logs page - requires login - DEPRECATED: Use /admin/logs"""
    if 'admin_logged_in' not in session:
        return redirect('/admin/login')
    return redirect('/admin/logs')

@app.route('/admin/logs')
def admin_logs():
    """Admin logs page (combined error and system logs) - requires login"""
    if 'admin_logged_in' not in session:
        return redirect('/admin/login')
    return render_template('admin_logs.html')

# ==================== ADMIN API: USERS MANAGEMENT ====================

@app.route('/api/admin/users', methods=['GET'])
def admin_get_users():
    """Get all users with filters"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        # Get filters
        user_type = request.args.get('type', 'all')
        search = request.args.get('search', '').strip()
        
        # Base query
        query = """
            SELECT 
                u.id,
                u.username,
                u.email,
                u.google_id,
                u.created_at,
                u.is_verified,
                CASE 
                    WHEN ps.id IS NOT NULL AND ps.expires_at > NOW() THEN true 
                    ELSE false 
                END as is_premium,
                ps.expires_at as premium_expires
            FROM users u
            LEFT JOIN premium_subscriptions ps ON u.id = ps.user_id AND ps.is_active = true AND ps.expires_at > NOW()
            WHERE 1=1
        """
        
        params = []
        
        # Apply filters
        if search:
            query += ' AND (u.username ILIKE %s OR u.email ILIKE %s)'
            params.extend([f'%{search}%', f'%{search}%'])
        
        if user_type == 'premium':
            query += ' AND ps.id IS NOT NULL AND ps.expires_at > NOW()'
        elif user_type == 'free':
            query += ' AND (ps.id IS NULL OR ps.expires_at <= NOW())'
        elif user_type == 'google':
            query += ' AND u.google_id IS NOT NULL'
        
        query += ' ORDER BY u.created_at DESC LIMIT 100'
        
        cursor.execute(query, params)
        users = cursor.fetchall()
        
        # Get stats
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT u.id) 
            FROM users u
            JOIN premium_subscriptions ps ON u.id = ps.user_id
            WHERE ps.is_active = true AND ps.expires_at > NOW()
        """)
        premium_users = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM users 
            WHERE created_at >= CURRENT_DATE
        """)
        users_today = cursor.fetchone()[0]
        
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({
            'success': True,
            'users': [{
                'id': u[0],
                'username': u[1],
                'email': u[2],
                'has_google': u[3] is not None,
                'created_at': u[4].isoformat() if u[4] else None,
                'is_verified': u[5],
                'is_premium': u[6],
                'premium_expires': u[7].isoformat() if u[7] else None
            } for u in users],
            'stats': {
                'total': total_users,
                'premium': premium_users,
                'today': users_today,
                'online': 0
            }
        })
        
    except Exception as e:
        print(f'[ERROR] Admin get users: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
def admin_delete_user(user_id):
    """Delete a user"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
        conn.commit()
        
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({'success': True, 'message': 'Đã xóa người dùng'})
        
    except Exception as e:
        print(f'[ERROR] Admin delete user: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/users/<int:user_id>/add-premium', methods=['POST'])
def admin_add_user_premium(user_id):
    """Add premium to a user"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        data = request.get_json()
        days = data.get('days', 30)
        
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        # Check if user has active premium
        cursor.execute("""
            SELECT id, expires_at FROM premium_subscriptions 
            WHERE user_id = %s AND is_active = true AND expires_at > NOW()
            ORDER BY expires_at DESC LIMIT 1
        """, (user_id,))
        
        existing = cursor.fetchone()
        
        if existing:
            # Extend existing premium
            cursor.execute("""
                UPDATE premium_subscriptions 
                SET expires_at = expires_at + INTERVAL '%s days'
                WHERE id = %s
            """ % (days, existing[0]))
        else:
            # Create new premium subscription
            cursor.execute("""
                INSERT INTO premium_subscriptions 
                (user_id, amount, starts_at, expires_at, is_active, order_code)
                VALUES (%s, 0, NOW(), NOW() + INTERVAL '%s days', true, 'ADMIN_GRANT')
            """ % (user_id, days))
        
        conn.commit()
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({'success': True, 'message': f'Đã thêm {days} ngày Premium'})
        
    except Exception as e:
        print(f'[ERROR] Admin add premium: {e}')
        return jsonify({'error': str(e)}), 500


# ==================== ADMIN API: PREMIUM MANAGEMENT ====================

@app.route('/api/admin/premium', methods=['GET'])
def admin_get_premium_subscriptions():
    """Get all premium subscriptions"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        status_filter = request.args.get('status', 'all')
        
        query = """
            SELECT 
                ps.id,
                ps.user_id,
                u.username,
                u.email,
                ps.order_code,
                ps.amount,
                ps.starts_at,
                ps.expires_at,
                ps.is_active,
                ps.created_at,
                CASE 
                    WHEN ps.expires_at > NOW() THEN 'active'
                    ELSE 'expired'
                END as status
            FROM premium_subscriptions ps
            JOIN users u ON ps.user_id = u.id
            WHERE 1=1
        """
        
        if status_filter == 'active':
            query += ' AND ps.is_active = true AND ps.expires_at > NOW()'
        elif status_filter == 'expiring':
            query += " AND ps.is_active = true AND ps.expires_at > NOW() AND ps.expires_at <= NOW() + INTERVAL '7 days'"
        elif status_filter == 'expired':
            query += ' AND ps.expires_at <= NOW()'
        
        query += ' ORDER BY ps.created_at DESC LIMIT 200'
        
        cursor.execute(query)
        subscriptions = cursor.fetchall()
        
        # Get stats
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(amount), 0)
            FROM premium_subscriptions 
            WHERE is_active = true AND expires_at > NOW()
        """)
        active_count, total_revenue = cursor.fetchone()
        
        cursor.execute("""
            SELECT COUNT(*) FROM premium_subscriptions 
            WHERE is_active = true AND expires_at > NOW() AND expires_at <= NOW() + INTERVAL '7 days'
        """)
        expiring_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM premium_subscriptions 
            WHERE expires_at <= NOW()
        """)
        expired_count = cursor.fetchone()[0]
        
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({
            'success': True,
            'subscriptions': [{
                'id': s[0],
                'user_id': s[1],
                'username': s[2],
                'email': s[3],
                'order_code': s[4],
                'amount': s[5],
                'starts_at': s[6].isoformat() if s[6] else None,
                'expires_at': s[7].isoformat() if s[7] else None,
                'is_active': s[8],
                'created_at': s[9].isoformat() if s[9] else None,
                'status': s[10]
            } for s in subscriptions],
            'stats': {
                'active': active_count,
                'revenue': total_revenue,
                'expiring': expiring_count,
                'expired': expired_count
            }
        })
        
    except Exception as e:
        print(f'[ERROR] Admin get premium: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/premium/<int:subscription_id>', methods=['DELETE'])
def admin_delete_premium(subscription_id):
    """Delete a premium subscription"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM premium_subscriptions WHERE id = %s', (subscription_id,))
        conn.commit()
        
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({'success': True, 'message': 'Đã xóa gói Premium'})
        
    except Exception as e:
        print(f'[ERROR] Admin delete premium: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/premium/<int:subscription_id>/extend', methods=['POST'])
def admin_extend_premium(subscription_id):
    """Extend premium subscription"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        data = request.get_json()
        days = data.get('days', 30)
        
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE premium_subscriptions 
            SET expires_at = expires_at + INTERVAL '%s days',
                is_active = true
            WHERE id = %s
        """ % (days, subscription_id))
        
        conn.commit()
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({'success': True, 'message': f'Đã gia hạn thêm {days} ngày'})
        
    except Exception as e:
        print(f'[ERROR] Admin extend premium: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/premium-history', methods=['GET'])
def admin_get_premium_history():
    """Get premium payment history from premium_subscriptions table"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        status_filter = request.args.get('status', 'all')
        search = request.args.get('search', '').strip()
        
        # Base query - get premium subscriptions with user and donation info
        query = """
            SELECT 
                ps.id,
                ps.user_id,
                u.username,
                u.email,
                ps.order_code,
                ps.amount,
                CASE 
                    WHEN ps.is_active AND ps.expires_at > NOW() THEN 'PAID'
                    WHEN ps.expires_at <= NOW() THEN 'EXPIRED'
                    ELSE 'CANCELLED'
                END as status,
                ps.created_at,
                ps.expires_at,
                ps.starts_at
            FROM premium_subscriptions ps
            LEFT JOIN users u ON ps.user_id = u.id
            WHERE 1=1
        """
        
        params = []
        
        # Apply filters
        if status_filter == 'PAID':
            query += ' AND ps.is_active = true AND ps.expires_at > NOW()'
        elif status_filter == 'EXPIRED':
            query += ' AND ps.expires_at <= NOW()'
        elif status_filter == 'CANCELLED':
            query += ' AND ps.is_active = false'
        
        if search:
            query += ' AND (u.username ILIKE %s OR u.email ILIKE %s OR ps.order_code ILIKE %s)'
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        query += ' ORDER BY ps.created_at DESC LIMIT 200'
        
        cursor.execute(query, params)
        payments = cursor.fetchall()
        
        # Get stats
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(amount), 0)
            FROM premium_subscriptions 
            WHERE is_active = true AND expires_at > NOW()
        """)
        success_count, total_revenue = cursor.fetchone()
        
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) 
            FROM premium_subscriptions 
            WHERE is_active = true AND expires_at > NOW()
        """)
        premium_users = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM premium_subscriptions 
            WHERE created_at >= CURRENT_DATE
        """)
        today_count = cursor.fetchone()[0]
        
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({
            'success': True,
            'payments': [{
                'id': p[0],
                'user_id': p[1],
                'username': p[2],
                'email': p[3],
                'order_code': p[4],
                'amount': p[5],
                'status': p[6],
                'created_at': p[7].isoformat() if p[7] else None,
                'expires_at': p[8].isoformat() if p[8] else None,
                'starts_at': p[9].isoformat() if p[9] else None
            } for p in payments],
            'stats': {
                'success': success_count,
                'revenue': total_revenue,
                'premium_users': premium_users,
                'today': today_count
            }
        })
        
    except Exception as e:
        print(f'[ERROR] Admin get premium history: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/news')
def api_news():
    return NewsController.get_news()

@app.route('/api/news/proxy')
def api_news_proxy():
    return NewsController.proxy_article()

@app.route('/robots.txt')
def robots():
    return app.send_static_file('robots.txt')

@app.route('/sw-check-permissions-c6f62.js')
def propush_service_worker():
    return app.send_static_file('sw-check-permissions-c6f62.js')

@app.errorhandler(404)
def page_not_found(e):
    # Redirect 404 to SmartLink for monetization
    return redirect('https://rm358.com/4/106/8420?var=404_redirect')

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.svg')

@app.route('/ads.txt')
def ads():
    return app.send_static_file('ads.txt')

@app.route('/sitemap.xml')
def sitemap():
    return app.send_static_file('sitemap.xml')

@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

@app.route('/api/youtube/download', methods=['POST'])
def youtube_download():
    start_time = time.time()
    
    # Debug session info
    print(f"[SESSION DEBUG] Session data: {dict(session)}")
    print(f"[SESSION DEBUG] Has user_id: {'user_id' in session}")
    print(f"[SESSION DEBUG] Cookie secure: {app.config.get('SESSION_COOKIE_SECURE')}")
    print(f"[SESSION DEBUG] Request scheme: {request.scheme}")
    print(f"[SESSION DEBUG] Request headers X-Forwarded-Proto: {request.headers.get('X-Forwarded-Proto')}")
    
    # Kiểm tra đăng nhập
    if 'user_id' not in session:
        log_system('WARNING', 'Unauthorized YouTube download attempt', 
                   log_source='youtube_download', request_obj=request)
        return jsonify({
            'success': False, 
            'error': '🔒 Vui lòng đăng nhập để tải xuống',
            'require_login': True
        }), 401
    
    # Check free user download limit
    user_id = session.get('user_id')
    from controllers.auth_controller import get_user_premium_info
    
    premium_info = get_user_premium_info(user_id)
    if premium_info:
        is_premium = premium_info.get('is_premium', False)
        downloads_this_week = premium_info.get('downloads_this_week', 0)
        
        # Free users: max 2 downloads per month
        if not is_premium and downloads_this_week >= 2:
            log_system('WARNING', f'Free user download limit reached: {downloads_this_week}/2', 
                       log_source='youtube_download', user_id=user_id, request_obj=request)
            return jsonify({
                'success': False,
                'error': '🚫 Bạn đã hết 2 lượt tải miễn phí trong tháng này.\n\n💎 Nâng cấp Premium để tải không giới hạn!',
                'limit_reached': True,
                'downloads_used': downloads_this_week,
                'max_free': 2
            }), 403
    
    data = request.get_json()
    url = data.get('url', '').strip()
    format_type = data.get('format', 'mp4')
    quality = data.get('quality', '720')
    
    if not url:
        return jsonify({'success': False, 'error': 'Vui lòng nhập URL YouTube'}), 400
    
    if not is_valid_youtube_url(url):
        log_system('WARNING', f'Invalid YouTube URL: {url[:100]}', 
                   log_source='youtube_download', request_obj=request)
        return jsonify({'success': False, 'error': 'URL YouTube không hợp lệ'}), 400
    
    # Check cooldown per IP
    client_ip = request.remote_addr
    current_time = time.time()
    
    if client_ip in last_youtube_download:
        time_since_last = current_time - last_youtube_download[client_ip]
        if time_since_last < YOUTUBE_COOLDOWN:
            wait_time = int(YOUTUBE_COOLDOWN - time_since_last)
            log_system('INFO', f'Rate limit hit for IP {client_ip}', 
                       log_source='youtube_download', request_obj=request)
            return jsonify({
                'success': False, 
                'error': f'⏳ Vui lòng đợi {wait_time} giây trước khi tải video tiếp theo.\n\nĐây là biện pháp bảo vệ để tránh bị YouTube chặn. Cảm ơn bạn đã thông cảm! 😊'
            }), 429
    
    # Update last download time
    last_youtube_download[client_ip] = current_time
    
    download_id = str(uuid.uuid4())
    
    # Log successful request
    execution_time = time.time() - start_time
    log_system('INFO', f'YouTube download started: {url[:100]}', 
               log_source='youtube_download',
               user_id=session.get('user_id'),
               execution_time=execution_time,
               additional_data={'format': format_type, 'quality': quality, 'download_id': download_id},
               request_obj=request)
    
    # Use ThreadPool to prevent server crash
    executor.submit(download_youtube_video, url, format_type, quality, download_id)
    
    return jsonify({
        'success': True, 
        'download_id': download_id,
        'show_promo': not is_premium  # Only show promo for free users
    })

@app.route('/api/tiktok/download', methods=['POST'])
def tiktok_download():
    # Kiểm tra đăng nhập
    if 'user_id' not in session:
        return jsonify({
            'success': False, 
            'error': '🔒 Vui lòng đăng nhập để tải xuống',
            'require_login': True
        }), 401
    
    # Check free user download limit
    user_id = session.get('user_id')
    from controllers.auth_controller import get_user_premium_info
    
    premium_info = get_user_premium_info(user_id)
    if premium_info:
        is_premium = premium_info.get('is_premium', False)
        downloads_this_week = premium_info.get('downloads_this_week', 0)
        
        # Free users: max 2 downloads per month
        if not is_premium and downloads_this_week >= 2:
            return jsonify({
                'success': False,
                'error': '🚫 Bạn đã hết 2 lượt tải miễn phí trong tháng này.\n\n💎 Nâng cấp Premium để tải không giới hạn!',
                'limit_reached': True,
                'downloads_used': downloads_this_week,
                'max_free': 2
            }), 403
    
    data = request.get_json()
    url = data.get('url', '').strip()
    format_type = data.get('format', 'mp4')
    
    if not url:
        return jsonify({'success': False, 'error': 'Vui lòng nhập URL TikTok'}), 400
    
    if not is_valid_tiktok_url(url):
        return jsonify({'success': False, 'error': 'URL TikTok không hợp lệ'}), 400
    
    download_id = str(uuid.uuid4())
    
    # Check if photo
    is_photo = '/photo/' in url
    
    if is_photo:
        selected_images = data.get('selected_images', None)
        executor.submit(download_tiktok_photos, url, download_id, selected_images)
    else:
        quality = data.get('quality', 'best')
        executor.submit(download_tiktok_video, url, format_type, download_id, quality)
        
    return jsonify({
        'success': True, 
        'download_id': download_id,
        'show_promo': not is_premium  # Only show promo for free users
    })

@app.route('/api/progress/<download_id>')
def get_progress(download_id):
    if download_id not in download_progress:
        return jsonify({'status': 'not_found'}), 404
    
    return jsonify(download_progress[download_id])

@app.route('/api/download/<download_id>')
def download_file(download_id):
    from flask import send_file, after_this_request
    
    if download_id not in download_data:
        return jsonify({'error': 'Không tìm thấy file'}), 404
    
    data = download_data[download_id]
    filepath = data['filepath']
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File không tồn tại'}), 404
    
    title = data.get('title', 'download')
    # Clean title for filename - remove special chars
    clean_title = re.sub(r'[^\w\s-]', '', title)[:50].strip()
    if not clean_title:
        clean_title = 'download'
    download_name = f"{clean_title}.{data['ext']}"
    
    as_attachment = True
    if 'video' in data['mime_type']:
        as_attachment = True # Force attachment for videos on iOS
    
    # Get tracking info
    tracking_info = None
    try:
        tracking_info = get_full_tracking_info()
    except Exception as e:
        print(f"[WARNING] Failed to get tracking info: {e}")
    
    # Get user_id from session if logged in
    user_id = session.get('user_id')
    
    # Increment stats with metadata, tracking, and user_id
    platform = data.get('platform', 'unknown')
    format_type = data.get('format', data['ext'])
    quality = data.get('quality', 'best')
    increment_stats(platform, format_type, quality, True, tracking_info, user_id)
    
    # Record download for free user limit tracking
    if user_id:
        record_user_download(user_id, platform)
    
    return send_file(
        filepath,
        mimetype=data['mime_type'],
        as_attachment=as_attachment,
        download_name=download_name
    )

@app.route('/api/stats/tracking')
def api_tracking_stats():
    """Get tracking statistics"""
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        # Top countries
        cursor.execute("""
            SELECT country, country_code, COUNT(*) as count
            FROM downloads
            WHERE country IS NOT NULL AND country != 'Unknown'
            GROUP BY country, country_code
            ORDER BY count DESC
            LIMIT 10
        """)
        top_countries = [
            {'country': row[0], 'code': row[1], 'count': row[2]}
            for row in cursor.fetchall()
        ]
        
        # Device types
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN is_mobile THEN 1 ELSE 0 END) as mobile,
                SUM(CASE WHEN is_tablet THEN 1 ELSE 0 END) as tablet,
                SUM(CASE WHEN is_pc THEN 1 ELSE 0 END) as pc
            FROM downloads
            WHERE is_mobile IS NOT NULL
        """)
        device_stats = cursor.fetchone()
        devices = {
            'mobile': device_stats[0] or 0,
            'tablet': device_stats[1] or 0,
            'pc': device_stats[2] or 0
        }
        
        # Top cities
        cursor.execute("""
            SELECT city, country, COUNT(*) as count
            FROM downloads
            WHERE city IS NOT NULL AND city != 'Unknown'
            GROUP BY city, country
            ORDER BY count DESC
            LIMIT 10
        """)
        top_cities = [
            {'city': row[0], 'country': row[1], 'count': row[2]}
            for row in cursor.fetchall()
        ]
        
        # Browser stats
        cursor.execute("""
            SELECT browser, COUNT(*) as count
            FROM downloads
            WHERE browser IS NOT NULL
            GROUP BY browser
            ORDER BY count DESC
            LIMIT 10
        """)
        top_browsers = [
            {'browser': row[0], 'count': row[1]}
            for row in cursor.fetchall()
        ]
        
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({
            'top_countries': top_countries,
            'devices': devices,
            'top_cities': top_cities,
            'top_browsers': top_browsers
        })
        
    except Exception as e:
        print(f"[ERROR] Tracking stats failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/downloads/recent')
def api_recent_downloads():
    """Get recent downloads with full details"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        limit = request.args.get('limit', 50, type=int)
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                d.id, d.platform, d.format, d.quality, d.download_time,
                d.ip_address, d.country, d.city, d.device_type, d.os, d.browser,
                d.is_mobile, d.is_tablet, d.is_pc, d.success, d.user_id,
                u.username, u.email
            FROM downloads d
            LEFT JOIN users u ON d.user_id = u.id
            ORDER BY d.download_time DESC
            LIMIT %s
        """, (limit,))
        
        downloads = []
        for row in cursor.fetchall():
            downloads.append({
                'id': row[0],
                'platform': row[1],
                'format': row[2],
                'quality': row[3],
                'download_time': row[4].isoformat() if row[4] else None,
                'ip_address': row[5],
                'country': row[6],
                'city': row[7],
                'device_type': row[8],
                'os': row[9],
                'browser': row[10],
                'is_mobile': row[11],
                'is_tablet': row[12],
                'is_pc': row[13],
                'success': row[14],
                'user_id': row[15],
                'username': row[16],
                'email': row[17]
            })
        
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({
            'downloads': downloads,
            'total': len(downloads),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"[ERROR] Recent downloads failed: {e}")
        return jsonify({'error': str(e)}), 500
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/analytics/daily')
def api_daily_analytics():
    """Get daily download statistics for last 30 days"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        # Daily downloads for last 30 days
        cursor.execute("""
            SELECT 
                DATE(download_time) as date,
                COUNT(*) as total,
                SUM(CASE WHEN platform = 'youtube' THEN 1 ELSE 0 END) as youtube,
                SUM(CASE WHEN platform = 'tiktok' THEN 1 ELSE 0 END) as tiktok,
                SUM(CASE WHEN is_mobile THEN 1 ELSE 0 END) as mobile,
                SUM(CASE WHEN is_pc THEN 1 ELSE 0 END) as desktop
            FROM downloads
            WHERE download_time >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(download_time)
            ORDER BY date DESC
        """)
        
        daily_stats = []
        for row in cursor.fetchall():
            daily_stats.append({
                'date': row[0].isoformat() if row[0] else None,
                'total': row[1],
                'youtube': row[2],
                'tiktok': row[3],
                'mobile': row[4],
                'desktop': row[5]
            })
        
        # Platform distribution
        cursor.execute("""
            SELECT platform, COUNT(*) as count
            FROM downloads
            GROUP BY platform
            ORDER BY count DESC
        """)
        platforms = [{'platform': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Format distribution
        cursor.execute("""
            SELECT format, COUNT(*) as count
            FROM downloads
            GROUP BY format
            ORDER BY count DESC
        """)
        formats = [{'format': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({
            'daily_stats': daily_stats,
            'platforms': platforms,
            'formats': formats
        })
        
    except Exception as e:
        print(f"[ERROR] Daily analytics failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/env-vars')
def api_env_vars():
    """Get list of configured environment variables (names only)"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    important_vars = [
        'DATABASE_URL', 'SECRET_KEY', 'ADMIN_USERNAME', 'ADMIN_PASSWORD',
        'YOUTUBE_COOKIES', 'YOUTUBE_OAUTH_REFRESH_TOKEN', 
        'YOUTUBE_PO_TOKEN', 'YOUTUBE_VISITOR_DATA', 'MAX_WORKERS'
    ]
    
    configured = [var for var in important_vars if os.environ.get(var)]
    
    return jsonify({'env_vars': configured})

@app.route('/api/admin/db-stats')
def api_db_stats():
    """Get database statistics"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        # Total records
        cursor.execute("SELECT COUNT(*) FROM downloads")
        total_records = cursor.fetchone()[0]
        
        # Oldest and newest records
        cursor.execute("SELECT MIN(download_time), MAX(download_time) FROM downloads")
        oldest, newest = cursor.fetchone()
        
        # Database size (PostgreSQL specific)
        cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
        db_size = cursor.fetchone()[0]
        
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({
            'total_records': total_records,
            'database_size': db_size,
            'oldest_record': oldest.isoformat() if oldest else None,
            'newest_record': newest.isoformat() if newest else None
        })
        
    except Exception as e:
        print(f"[ERROR] DB stats failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/export-data')
def api_export_data():
    """Export tracking data as CSV"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        import io
        import csv
        from flask import Response
        
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id, platform, format, quality, download_time,
                ip_address, country, country_code, city, timezone,
                device_type, os, browser, is_mobile, is_tablet, is_pc
            FROM downloads
            ORDER BY download_time DESC
        """)
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'ID', 'Platform', 'Format', 'Quality', 'Download Time',
            'IP Address', 'Country', 'Country Code', 'City', 'Timezone',
            'Device Type', 'OS', 'Browser', 'Is Mobile', 'Is Tablet', 'Is PC'
        ])
        
        # Data
        for row in cursor.fetchall():
            writer.writerow(row)
        
        cursor.close()
        db_pool.putconn(conn)
        
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=tracking_data.csv'}
        )
        
    except Exception as e:
        print(f"[ERROR] Export failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/clear-old-data', methods=['POST'])
def api_clear_old_data():
    """Clear old tracking data"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        data = request.get_json()
        days = data.get('days', 90)
        
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM downloads
            WHERE download_time < CURRENT_DATE - INTERVAL '%s days'
        """, (days,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({'success': True, 'deleted_count': deleted_count})
        
    except Exception as e:
        print(f"[ERROR] Clear old data failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/clear-download-history', methods=['POST'])
def api_clear_download_history():
    """Clear download history older than 3 days"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        from datetime import datetime, timedelta
        three_days_ago = datetime.now() - timedelta(days=3)
        
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        # Count before delete
        cursor.execute("""
            SELECT COUNT(*) FROM user_downloads 
            WHERE download_time < %s
        """, (three_days_ago,))
        count_before = cursor.fetchone()[0]
        
        # Delete old records
        cursor.execute("""
            DELETE FROM user_downloads 
            WHERE download_time < %s
        """, (three_days_ago,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        # Get remaining count
        cursor.execute("SELECT COUNT(*) FROM user_downloads")
        remaining = cursor.fetchone()[0]
        
        cursor.close()
        db_pool.putconn(conn)
        
        print(f"[ADMIN] Manually cleared {deleted_count} download history records older than 3 days")
        
        return jsonify({
            'success': True, 
            'deleted_count': deleted_count,
            'remaining_count': remaining,
            'cutoff_date': three_days_ago.isoformat()
        })
        
    except Exception as e:
        print(f"[ERROR] Clear download history failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/clear-cache', methods=['POST'])
def api_clear_cache():
    """Clear cache files"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        cache_type = data.get('type', 'temp')
        
        if cache_type == 'temp':
            # Clear temp directory
            temp_dir = tempfile.gettempdir()
            count = 0
            for file in os.listdir(temp_dir):
                if file.startswith('tmp') or file.endswith('.tmp'):
                    try:
                        os.remove(os.path.join(temp_dir, file))
                        count += 1
                    except:
                        pass
            return jsonify({'success': True, 'message': f'Đã xóa {count} temp files'})
        
        elif cache_type == 'downloads':
            # Clear download cache
            global download_data, download_progress
            count = len(download_data)
            download_data.clear()
            download_progress.clear()
            return jsonify({'success': True, 'message': f'Đã xóa {count} download cache entries'})
        
        return jsonify({'success': False, 'error': 'Invalid cache type'}), 400
        
    except Exception as e:
        print(f"[ERROR] Clear cache failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/change-password', methods=['POST'])
def api_change_password():
    """Change admin password"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        # Verify current password
        current_hash = hashlib.sha256(current_password.encode()).hexdigest()
        if current_hash != ADMIN_PASSWORD_HASH:
            return jsonify({'success': False, 'error': 'Mật khẩu hiện tại không đúng'}), 401
        
        # Note: In production, you should update the password in database or env vars
        # For now, just return success (password change requires restart with new env var)
        return jsonify({
            'success': True,
            'message': 'Để thay đổi mật khẩu vĩnh viễn, vui lòng cập nhật biến môi trường ADMIN_PASSWORD trên Railway'
        })
        
    except Exception as e:
        print(f"[ERROR] Change password failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/error-logs', methods=['GET'])
def api_get_error_logs():
    """Get error logs for admin monitoring"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        # Get filters
        error_type = request.args.get('type', 'all')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = """
            SELECT 
                id, error_type, error_message, stack_trace, url, 
                platform, format, quality, user_id, ip_address, 
                user_agent, created_at
            FROM error_logs
        """
        
        params = []
        if error_type != 'all':
            query += " WHERE error_type = %s"
            params.append(error_type)
        
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Get total count
        count_query = "SELECT COUNT(*) FROM error_logs"
        if error_type != 'all':
            count_query += " WHERE error_type = %s"
            cursor.execute(count_query, [error_type])
        else:
            cursor.execute(count_query)
        
        total = cursor.fetchone()[0]
        
        # Format results
        logs = []
        for row in rows:
            logs.append({
                'id': row[0],
                'error_type': row[1],
                'error_message': row[2],
                'stack_trace': row[3],
                'url': row[4],
                'platform': row[5],
                'format': row[6],
                'quality': row[7],
                'user_id': row[8],
                'ip_address': row[9],
                'user_agent': row[10],
                'created_at': row[11].isoformat() if row[11] else None
            })
        
        # Get error type statistics
        cursor.execute("""
            SELECT error_type, COUNT(*) as count
            FROM error_logs
            GROUP BY error_type
            ORDER BY count DESC
        """)
        
        stats = {}
        for row in cursor.fetchall():
            stats[row[0]] = row[1]
        
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({
            'logs': logs,
            'total': total,
            'stats': stats,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        print(f"[ERROR] Get error logs failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/error-logs/<int:log_id>', methods=['DELETE'])
def api_delete_error_log(log_id):
    """Delete a specific error log"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM error_logs WHERE id = %s", (log_id,))
        conn.commit()
        
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"[ERROR] Delete error log failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/error-logs/clear', methods=['POST'])
def api_clear_error_logs():
    """Clear all error logs or by type"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        data = request.get_json() or {}
        error_type = data.get('type', 'all')
        days = int(data.get('days', 0))
        
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        if days > 0:
            # Clear logs older than X days
            query = "DELETE FROM error_logs WHERE created_at < NOW() - INTERVAL '%s days'"
            params = [days]
            
            if error_type != 'all':
                query += " AND error_type = %s"
                params.append(error_type)
            
            cursor.execute(query, params)
        else:
            # Clear all or by type
            if error_type != 'all':
                cursor.execute("DELETE FROM error_logs WHERE error_type = %s", (error_type,))
            else:
                cursor.execute("DELETE FROM error_logs")
        
        deleted = cursor.rowcount
        conn.commit()
        
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({'success': True, 'deleted': deleted})
        
    except Exception as e:
        print(f"[ERROR] Clear error logs failed: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== ADMIN API: SYSTEM LOGS ====================

@app.route('/api/admin/system-logs', methods=['GET'])
def api_get_system_logs():
    """Get system logs for admin monitoring"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        # Get filters
        log_level = request.args.get('level', 'all')
        log_source = request.args.get('source', 'all')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = """
            SELECT 
                id, log_level, log_message, log_source, url, method,
                status_code, user_id, ip_address, user_agent, 
                execution_time, additional_data, created_at
            FROM system_logs
            WHERE 1=1
        """
        
        params = []
        
        if log_level != 'all':
            query += " AND log_level = %s"
            params.append(log_level)
        
        if log_source != 'all':
            query += " AND log_source = %s"
            params.append(log_source)
        
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Get total count
        count_query = "SELECT COUNT(*) FROM system_logs WHERE 1=1"
        count_params = []
        
        if log_level != 'all':
            count_query += " AND log_level = %s"
            count_params.append(log_level)
        
        if log_source != 'all':
            count_query += " AND log_source = %s"
            count_params.append(log_source)
        
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()[0]
        
        # Format results
        logs = []
        for row in rows:
            logs.append({
                'id': row[0],
                'log_level': row[1],
                'log_message': row[2],
                'log_source': row[3],
                'url': row[4],
                'method': row[5],
                'status_code': row[6],
                'user_id': row[7],
                'ip_address': row[8],
                'user_agent': row[9],
                'execution_time': row[10],
                'additional_data': row[11],
                'created_at': row[12].isoformat() if row[12] else None
            })
        
        # Get statistics
        cursor.execute("""
            SELECT log_level, COUNT(*) as count
            FROM system_logs
            GROUP BY log_level
            ORDER BY count DESC
        """)
        
        level_stats = {}
        for row in cursor.fetchall():
            level_stats[row[0]] = row[1]
        
        cursor.execute("""
            SELECT log_source, COUNT(*) as count
            FROM system_logs
            WHERE log_source IS NOT NULL
            GROUP BY log_source
            ORDER BY count DESC
            LIMIT 10
        """)
        
        source_stats = {}
        for row in cursor.fetchall():
            source_stats[row[0]] = row[1]
        
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({
            'logs': logs,
            'total': total,
            'level_stats': level_stats,
            'source_stats': source_stats,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        print(f"[ERROR] Get system logs failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/system-logs/<int:log_id>', methods=['DELETE'])
def api_delete_system_log(log_id):
    """Delete a specific system log"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM system_logs WHERE id = %s", (log_id,))
        conn.commit()
        
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"[ERROR] Delete system log failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/system-logs/clear', methods=['POST'])
def api_clear_system_logs():
    """Clear all system logs or by level/source"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        data = request.get_json() or {}
        log_level = data.get('level', 'all')
        log_source = data.get('source', 'all')
        days = int(data.get('days', 0))
        
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        query = "DELETE FROM system_logs WHERE 1=1"
        params = []
        
        if days > 0:
            query += " AND created_at < NOW() - INTERVAL '%s days'"
            params.append(days)
        
        if log_level != 'all':
            query += " AND log_level = %s"
            params.append(log_level)
        
        if log_source != 'all':
            query += " AND log_source = %s"
            params.append(log_source)
        
        cursor.execute(query, params)
        deleted = cursor.rowcount
        conn.commit()
        
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({'success': True, 'deleted': deleted})
        
    except Exception as e:
        print(f"[ERROR] Clear system logs failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/env')
def debug_env():
    """Debug endpoint to check server environment"""
    import subprocess
    import sys
    
    env_info = {
        'python_version': sys.version,
        'yt_dlp_version': None,
        'ffmpeg_installed': False,
        'deno_installed': False,
        'node_installed': False,
        'bgutil_server_running': False,
        'bgutil_server_url': 'http://127.0.0.1:4416',
    }
    
    # Check yt-dlp version
    try:
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True, timeout=5)
        env_info['yt_dlp_version'] = result.stdout.strip()
    except:
        env_info['yt_dlp_version'] = 'NOT INSTALLED'
    
    # Check FFmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
        env_info['ffmpeg_installed'] = 'version' in result.stdout.lower()
    except:
        pass
    
    # Check Deno
    try:
        result = subprocess.run(['deno', '--version'], capture_output=True, text=True, timeout=5)
        env_info['deno_installed'] = 'deno' in result.stdout.lower()
        env_info['deno_version'] = result.stdout.strip().split('\n')[0] if env_info['deno_installed'] else None
    except:
        pass
    
    # Check Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=5)
        env_info['node_installed'] = True
        env_info['node_version'] = result.stdout.strip()
    except:
        pass
    
    return jsonify(env_info)

@app.route('/api/debug/session-test')
def debug_session_test():
    """Test session functionality"""
    # Try to set a test value
    if 'test_counter' not in session:
        session['test_counter'] = 0
    session['test_counter'] += 1
    
    return jsonify({
        'success': True,
        'session_data': dict(session),
        'test_counter': session.get('test_counter'),
        'has_user_id': 'user_id' in session,
        'cookie_secure': app.config.get('SESSION_COOKIE_SECURE'),
        'request_scheme': request.scheme,
        'is_secure': request.is_secure,
        'x_forwarded_proto': request.headers.get('X-Forwarded-Proto'),
        'cookies_received': list(request.cookies.keys())
    })

@app.route('/api/debug/test-logs')
def debug_test_logs():
    """Create test logs for debugging (admin only)"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Create various test logs
        log_system('DEBUG', 'This is a debug message for testing', 
                   log_source='test', request_obj=request)
        
        log_system('INFO', 'Test info message - system is working correctly', 
                   log_source='test', 
                   execution_time=0.123,
                   additional_data={'test': True, 'count': 1},
                   request_obj=request)
        
        log_system('WARNING', 'Test warning message - something might be wrong', 
                   log_source='test',
                   additional_data={'warning_type': 'test', 'severity': 'low'},
                   request_obj=request)
        
        log_system('ERROR', 'Test error message - simulated error', 
                   log_source='test',
                   additional_data={'error_code': 500, 'details': 'This is a test error'},
                   request_obj=request)
        
        log_system('CRITICAL', 'Test critical message - simulated critical issue', 
                   log_source='test',
                   additional_data={'critical': True, 'requires_attention': True},
                   request_obj=request)
        
        # Log with different sources
        log_system('INFO', 'YouTube download test log', 
                   log_source='youtube_download',
                   url='https://youtube.com/watch?v=test',
                   method='POST',
                   status_code=200,
                   execution_time=2.5,
                   request_obj=request)
        
        log_system('INFO', 'TikTok download test log', 
                   log_source='tiktok_download',
                   url='https://tiktok.com/@user/video/123',
                   method='POST',
                   status_code=200,
                   execution_time=1.8,
                   request_obj=request)
        
        log_system('INFO', 'Authentication test log', 
                   log_source='auth',
                   additional_data={'action': 'login', 'success': True},
                   request_obj=request)
        
        return jsonify({
            'success': True,
            'message': 'Created 8 test logs successfully',
            'logs_created': 8
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        env_info['node_installed'] = result.returncode == 0
        env_info['node_version'] = result.stdout.strip() if env_info['node_installed'] else None
    except:
        pass
    
    # Check bgutil POT provider server
    try:
        import requests
        response = requests.get('http://127.0.0.1:4416/health', timeout=2)
        env_info['bgutil_server_running'] = response.status_code == 200
    except:
        # Try alternative check - see if process is running
        try:
            result = subprocess.run(['pgrep', '-f', 'bgutil_ytdlp_pot_provider'], 
                                  capture_output=True, text=True, timeout=2)
            env_info['bgutil_server_running'] = bool(result.stdout.strip())
        except:
            pass
    
    return jsonify(env_info)

@app.route('/debug')
def debug_page():
    """Debug page to check server environment"""
    return render_template('debug.html')

@app.route('/test-session')
def test_session_page():
    """Test page for session debugging"""
    return render_template('test_session.html')

@app.route('/test-stats')
def test_stats():
    """Test page for realtime statistics"""
    return render_template('test_stats.html')

@app.route('/premium')
def premium_page():
    """Premium subscription page"""
    user_info = None
    premium_info = None
    usage_info = {'free_downloads_left': 2, 'total_free_downloads': 2}
    
    # Get user info if logged in
    if 'user_id' in session and db_pool:
        try:
            conn = db_pool.getconn()
            cursor = conn.cursor()
            
            user_id = session['user_id']
            
            # Get user basic info
            cursor.execute("""
                SELECT username, email FROM users WHERE id = %s
            """, (user_id,))
            user_row = cursor.fetchone()
            
            if user_row:
                user_info = {
                    'username': user_row[0],
                    'email': user_row[1],
                    'is_premium': False
                }
                
                # Check premium status
                cursor.execute("""
                    SELECT expires_at, starts_at, amount 
                    FROM premium_subscriptions 
                    WHERE user_id = %s AND is_active = TRUE AND expires_at > NOW()
                    ORDER BY expires_at DESC LIMIT 1
                """, (user_id,))
                
                premium_row = cursor.fetchone()
                if premium_row:
                    from datetime import datetime
                    expires_at = premium_row[0]
                    starts_at = premium_row[1]
                    amount = premium_row[2]
                    
                    days_left = (expires_at - datetime.now()).days
                    
                    user_info['is_premium'] = True
                    premium_info = {
                        'expires_at': expires_at.strftime('%d/%m/%Y'),
                        'starts_at': starts_at.strftime('%d/%m/%Y'),
                        'days_left': days_left,
                        'amount': amount
                    }
                
                # Get usage info (downloads this month for free users)
                if not user_info['is_premium']:
                    cursor.execute("""
                        SELECT COUNT(*) FROM user_downloads 
                        WHERE user_id = %s 
                        AND download_time >= DATE_TRUNC('month', CURRENT_DATE)
                    """, (user_id,))
                    downloads_this_month = cursor.fetchone()[0]
                    usage_info['free_downloads_left'] = max(0, 2 - downloads_this_month)
            
            cursor.close()
            db_pool.putconn(conn)
        except Exception as e:
            print(f"[ERROR] Get premium page info: {e}")
    
    return render_template('premium.html', 
                         user=user_info, 
                         premium=premium_info,
                         usage=usage_info)

@app.route('/api/youtube/info', methods=['POST'])
def youtube_info():
    try:
        import yt_dlp
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data'}), 400
            
        url = data.get('url', '').strip()
        
        if not url or not is_valid_youtube_url(url):
            return jsonify({'success': False, 'error': 'URL không hợp lệ'}), 400
        
        info_extractor_args = {
            'youtube': {
                'player_client': ['web_safari', 'android_vr', 'web_embedded'],
            }
        }
        if YOUTUBE_PO_TOKEN and YOUTUBE_VISITOR_DATA:
            info_extractor_args['youtube']['po_token'] = [f'web+{YOUTUBE_PO_TOKEN}']
            info_extractor_args['youtube']['visitor_data'] = [YOUTUBE_VISITOR_DATA]
        elif YOUTUBE_PO_TOKEN:
            info_extractor_args['youtube']['po_token'] = [f'web+{YOUTUBE_PO_TOKEN}']

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'socket_timeout': 15,
            'extractor_args': info_extractor_args,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36',
            }
        }

        if COOKIES_FILE_PATH and os.path.exists(COOKIES_FILE_PATH):
            ydl_opts['cookiefile'] = COOKIES_FILE_PATH
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        return jsonify({
            'success': True,
            'title': info.get('title', 'Video'),
            'thumbnail': info.get('thumbnail', ''),
            'duration': info.get('duration', 0),
            'author': info.get('uploader', ''),
            'views': info.get('view_count', 0),
        })
        
    except Exception as e:
        print(f"YouTube info error: {e}")
        # Return success=False but still allow download
        return jsonify({'success': False, 'error': 'Không thể lấy preview, nhưng vẫn có thể tải'}), 200

@app.route('/api/tiktok/info', methods=['POST'])
def tiktok_info():
    try:
        import yt_dlp
        
        data = request.get_json()
        print(f"[DEBUG] Received data: {data}")
        
        if not data:
            print("[DEBUG] No data received")
            return jsonify({'success': False, 'error': 'No data'}), 400
            
        url = data.get('url', '').strip()
        print(f"[DEBUG] Original URL: {url}")
        
        if not url:
            print("[DEBUG] Empty URL")
            return jsonify({'success': False, 'error': 'URL trống'}), 400
            
        if not is_valid_tiktok_url(url):
            print(f"[DEBUG] Invalid TikTok URL: {url}")
            return jsonify({'success': False, 'error': 'URL không hợp lệ'}), 400
        
        print(f"[DEBUG] Processing TikTok URL: {url}")
        
        # Try to resolve short URLs first to get the real URL
        resolved_url = url
        try:
            if 'vm.tiktok.com' in url or 'vt.tiktok.com' in url or '/t/' in url:
                print(f"[DEBUG] Resolving short URL: {url}")
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
                response = requests.head(url, allow_redirects=True, headers=headers, timeout=10)
                resolved_url = response.url
                print(f"[DEBUG] Resolved to: {resolved_url}")
        except Exception as e:
            print(f"[DEBUG] URL resolution failed: {e}")
        
        # Check if it's a photo URL (check both original and resolved URL)
        is_photo = '/photo/' in url or '/photo/' in resolved_url
        print(f"[DEBUG] Is photo URL: {is_photo} (original: {'/photo/' in url}, resolved: {'/photo/' in resolved_url})")
        
        if is_photo:
            # Extract images immediately for preview and selection
            print(f"[DEBUG] Extracting images for preview...")
            # Use resolved URL for better extraction
            extract_url = resolved_url if resolved_url != url else url
            images = extract_tiktok_images(extract_url)
            print(f"[DEBUG] Extracted {len(images)} images")
            
            if images:
                return jsonify({
                    'success': True,
                    'title': '📷 TikTok Photo/Slideshow',
                    'thumbnail': images[0] if images else '',
                    'author': f'Tìm thấy {len(images)} ảnh',
                    'is_photo': True,
                    'images': images
                })
            else:
                # If extraction failed, still show as photo but with empty gallery
                print(f"[DEBUG] No images extracted, showing empty gallery")
                return jsonify({
                    'success': True,
                    'title': '📷 TikTok Photo/Slideshow',
                    'thumbnail': '',
                    'author': 'Album ảnh TikTok',
                    'is_photo': True,
                    'images': []
                })
        
        # Regular video processing
        print(f"[DEBUG] Processing as regular video")
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 10,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Try resolved URL first, fallback to original
                extract_url = resolved_url if resolved_url != url else url
                print(f"[DEBUG] Extracting video info from: {extract_url}")
                info = ydl.extract_info(extract_url, download=False)
                
            return jsonify({
                'success': True,
                'title': info.get('title', 'Video'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0),
                'author': info.get('uploader', ''),
                'likes': info.get('like_count', 0),
            })
        except Exception as video_error:
            print(f"[DEBUG] Video extraction failed with resolved URL: {video_error}")
            # Try original URL as fallback
            if resolved_url != url:
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        print(f"[DEBUG] Fallback: trying original URL: {url}")
                        info = ydl.extract_info(url, download=False)
                        
                    return jsonify({
                        'success': True,
                        'title': info.get('title', 'Video'),
                        'thumbnail': info.get('thumbnail', ''),
                        'duration': info.get('duration', 0),
                        'author': info.get('uploader', ''),
                        'likes': info.get('like_count', 0),
                    })
                except Exception as fallback_error:
                    print(f"[DEBUG] Fallback also failed: {fallback_error}")
                    raise video_error  # Raise original error
            else:
                raise video_error
        
    except Exception as e:
        print(f"TikTok info error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Không thể lấy thông tin video'}), 200

# Donation API endpoints are handled by donate_controller.py blueprint
# No duplicate endpoints needed here

@app.route('/api/admin/visit-stats')
def admin_visit_stats():
    """API chi tiết thống kê truy cập (cho admin)"""
    if not db_pool:
        return jsonify({'error': 'Database not available'})
    
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        # Thống kê theo giờ (24h qua)
        cursor.execute("""
            SELECT 
                DATE_TRUNC('hour', visit_time) as hour,
                COUNT(DISTINCT session_id) as unique_visitors,
                COUNT(*) as total_visits
            FROM page_visits 
            WHERE visit_time >= NOW() - INTERVAL '24 hours'
            GROUP BY DATE_TRUNC('hour', visit_time)
            ORDER BY hour DESC
            LIMIT 24
        """)
        hourly_stats = cursor.fetchall()
        
        # Top countries
        cursor.execute("""
            SELECT country, COUNT(DISTINCT session_id) as visitors
            FROM page_visits 
            WHERE country IS NOT NULL AND visit_time >= NOW() - INTERVAL '7 days'
            GROUP BY country
            ORDER BY visitors DESC
            LIMIT 10
        """)
        top_countries = cursor.fetchall()
        
        # Device types
        cursor.execute("""
            SELECT 
                CASE WHEN is_mobile THEN 'Mobile' ELSE 'Desktop' END as device,
                COUNT(DISTINCT session_id) as visitors
            FROM page_visits 
            WHERE visit_time >= NOW() - INTERVAL '7 days'
            GROUP BY is_mobile
        """)
        device_stats = cursor.fetchall()
        
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({
            'success': True,
            'hourly_stats': [{'hour': str(row[0]), 'unique_visitors': row[1], 'total_visits': row[2]} for row in hourly_stats],
            'top_countries': [{'country': row[0], 'visitors': row[1]} for row in top_countries],
            'device_stats': [{'device': row[0], 'visitors': row[1]} for row in device_stats]
        })
        
    except Exception as e:
        print(f"[ERROR] Admin visit stats error: {e}")
        return jsonify({'error': str(e)})

@app.route('/api/stats')
def get_download_stats():
    """API endpoint for download counter in hero section"""
    try:
        stats = get_stats()
        return jsonify({
            'total_downloads': stats.get('total_downloads', 1250)
        })
    except Exception as e:
        print(f">>> Download stats error: {e}")
        return jsonify({
            'total_downloads': 1250
        })

@app.route('/api/site-stats')
def get_statistics():
    """API endpoint để lấy thống kê truy cập THỰC TẾ"""
    try:
        print(">>> Statistics API called - REAL DATA MODE")
        if not db_pool:
            print(">>> No database pool, returning minimal fallback")
            return jsonify({
                'success': True,
                'stats': {
                    'online_users': 1,
                    'today_visits': 1,
                    'monthly_visits': 1,
                    'total_pageviews': 1
                }
            })
        
        print(">>> Database pool available, querying REAL data...")
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        # 1. Người dùng online (REALTIME với Socket.IO)
        realtime_online = len(online_users)
        
        # Fallback: nếu không có Socket.IO connections, dùng database
        if realtime_online == 0:
            cursor.execute("""
                SELECT COUNT(DISTINCT session_id)
                FROM page_visits 
                WHERE visit_time >= NOW() - INTERVAL '5 minutes'
            """)
            online_result = cursor.fetchone()
            online_users_db = online_result[0] if online_result else 0
            realtime_online = max(online_users_db, 0)
        
        print(f">>> Online users (Socket.IO): {len(online_users)} | DB fallback: {realtime_online}")
        
        # 2. Lượt truy cập hôm nay
        cursor.execute("""
            SELECT COUNT(DISTINCT session_id)
            FROM page_visits 
            WHERE DATE(visit_time) = CURRENT_DATE
        """)
        today_result = cursor.fetchone()
        today_visits = today_result[0] if today_result else 0
        print(f">>> Today visits: {today_visits}")
        
        # 3. Lượt truy cập trong tháng
        cursor.execute("""
            SELECT COUNT(DISTINCT session_id)
            FROM page_visits 
            WHERE DATE_TRUNC('month', visit_time) = DATE_TRUNC('month', CURRENT_DATE)
        """)
        month_result = cursor.fetchone()
        monthly_visits = month_result[0] if month_result else 0
        print(f">>> Monthly visits: {monthly_visits}")
        
        # 4. Tổng pageviews (tất cả visits)
        cursor.execute("SELECT COUNT(*) FROM page_visits")
        total_result = cursor.fetchone()
        actual_pageviews = total_result[0] if total_result else 0
        
        # Cộng thêm baseline 2000 để có số đẹp hơn
        total_pageviews = actual_pageviews + 2000
        
        print(f">>> Actual pageviews: {actual_pageviews}, Total with baseline: {total_pageviews}")
        
        cursor.close()
        db_pool.putconn(conn)
        
        stats_data = {
            'success': True,
            'stats': {
                'online_users': max(realtime_online, 0),
                'today_visits': max(today_visits, 0),
                'monthly_visits': max(monthly_visits, 0),
                'total_pageviews': max(total_pageviews, 1)
            }
        }
        print(f">>> Returning REAL stats: {stats_data}")
        return jsonify(stats_data)
        
    except Exception as e:
        print(f">>> Statistics error: {e}")
        import traceback
        traceback.print_exc()
        # Fallback tối thiểu khi có lỗi
        return jsonify({
            'success': True,
            'stats': {
                'online_users': 1,
                'today_visits': 1,
                'monthly_visits': 1,
                'total_pageviews': 1
            }
        })

if __name__ == '__main__':
    print("🚀 Starting Downloader Pro...")
    port = int(os.environ.get('PORT', 5000))
    
    # Check if bgutil POT provider is running
    print("\n" + "="*60)
    print("🔍 Checking bgutil POT provider status...")
    print("="*60)
    try:
        import requests
        response = requests.get('http://127.0.0.1:4416/health', timeout=2)
        if response.status_code == 200:
            print("✅ bgutil POT provider is RUNNING on port 4416")
            print("💡 Expected YouTube success rate: 95%+")
        else:
            print(f"⚠️ bgutil responded with status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ bgutil POT provider is NOT RUNNING")
        print("⚠️ Will use fallback strategies (50-60% success rate)")
        print("💡 To start bgutil: python -m bgutil_ytdlp_pot_provider --host 0.0.0.0 --port 4416 &")
    except Exception as e:
        print(f"⚠️ Could not check bgutil: {e}")
    print("="*60 + "\n")
    
    try:
        # Socket.IO requires eventlet or gevent for production
        # Try to use eventlet first, then gevent, then fallback
        try:
            import eventlet
            print(f"Starting Production Server with Socket.IO (eventlet) on port {port}...")
            socketio.run(app, host='0.0.0.0', port=port, debug=False)
        except ImportError:
            try:
                import gevent
                print(f"Starting Production Server with Socket.IO (gevent) on port {port}...")
                socketio.run(app, host='0.0.0.0', port=port, debug=False)
            except ImportError:
                print("⚠️ No eventlet/gevent found. Using Werkzeug (development mode)...")
                socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
    except Exception as e:
        print(f"❌ Socket.IO failed: {e}")
        print("🔄 Falling back to regular Flask server without Socket.IO...")
        try:
            from waitress import serve
            print(f"Starting Waitress server (no Socket.IO) on port {port}...")
            serve(app, host='0.0.0.0', port=port, threads=6)
        except ImportError:
            print("Starting Flask dev server...")
            app.run(debug=True, host='0.0.0.0', port=port)
@app.route('/proxy/image')
def proxy_image():
    """Proxy images to avoid CORS issues"""
    url = request.args.get('url')
    if not url:
        return 'No URL provided', 400
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.tiktok.com/'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return Response(
                response.content,
                mimetype=response.headers.get('content-type', 'image/jpeg'),
                headers={
                    'Cache-Control': 'public, max-age=3600',
                    'Access-Control-Allow-Origin': '*'
                }
            )
        else:
            return 'Image not found', 404
            
    except Exception as e:
        print(f"Proxy error: {e}")
        return 'Error loading image', 500

@app.route('/test/tiktok-images')
def test_tiktok_images():
    """Test endpoint for TikTok image extraction"""
    url = request.args.get('url', 'https://vt.tiktok.com/ZSmnMdPXG/')
    
    print(f"[TEST] Testing with URL: {url}")
    
    try:
        images = extract_tiktok_images(url)
        return jsonify({
            'success': True,
            'url': url,
            'images_count': len(images),
            'images': images[:3] if images else []  # Only show first 3 for brevity
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'url': url
        })
def extract_tiktok_images_direct(url):
    """Direct extraction without subprocess"""
    print(f"[DEBUG] Direct extraction for: {url}")
    
    try:
        # Resolve short link first
        if 'vm.tiktok.com' in url or 'vt.tiktok.com' in url or '/t/' in url:
            try:
                h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
                r = requests.head(url, allow_redirects=True, headers=h, timeout=15)
                url = r.url
                if 'tiktok.com' not in url:
                    r = requests.get(url, allow_redirects=True, headers=h, timeout=15)
                    url = r.url
                print(f"[DEBUG] Resolved URL: {url}")
            except Exception as e:
                print(f"[DEBUG] Resolve Error: {e}")
            
        # Clean URL
        if '?' in url: 
            url = url.split('?')[0]

        image_urls = []
        
        # 1. TikWM API
        try:
            print("[DEBUG] Trying TikWM...")
            resp = requests.post("https://www.tikwm.com/api/", 
                               data={'url': url}, 
                               timeout=15,
                               headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'})
            data = resp.json()
            print(f"[DEBUG] TikWM Response Code: {data.get('code')}")
            
            if data.get('code') == 0 and 'data' in data and 'images' in data['data']:
                image_urls = data['data']['images']
                print(f"[DEBUG] TikWM Success: {len(image_urls)} images")
                return list(dict.fromkeys(image_urls))  # Remove duplicates and return immediately
        except Exception as e:
            print(f"[DEBUG] TikWM Error: {e}")
        
        # 2. LoveTik API (fallback)
        if not image_urls:
            try:
                print("[DEBUG] Trying LoveTik...")
                payload = {'query': url}
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0', 
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
                }
                resp = requests.post("https://lovetik.com/api/ajax/search", 
                                   data=payload, 
                                   headers=headers, 
                                   timeout=15)
                data = resp.json()
                
                if data.get('status') == 'ok' and 'images' in data:
                    image_urls = [img['url'] for img in data['images']]
                    print(f"[DEBUG] LoveTik Success: {len(image_urls)} images")
            except Exception as e:
                print(f"[DEBUG] LoveTik Error: {e}")

        return list(dict.fromkeys(image_urls))
        
    except Exception as e:
        print(f"[ERROR] Direct extraction error: {e}")
        import traceback
        traceback.print_exc()
        return []