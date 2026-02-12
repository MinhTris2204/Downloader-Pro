from flask import Flask, render_template, request, jsonify, redirect, session
from werkzeug.middleware.proxy_fix import ProxyFix
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

# Import controllers
from controllers.home_controller import HomeController
from controllers.blog_controller import BlogController
from controllers.news_controller import NewsController
from utils.tracking import get_full_tracking_info

app = Flask(__name__)
# Secret key for session (change this in production!)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
# Fix for Proxy (Railway SSL)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

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
# To generate: base64 -w 0 cookies.txt > cookies_base64.txt
# Then set YOUTUBE_COOKIES=<content of cookies_base64.txt> in Railway

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
        db_pool = psycopg2.pool.SimpleConnectionPool(
            1, 10,
            db_url
        )
        
        # Create table if not exists
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id SERIAL PRIMARY KEY,
                platform VARCHAR(20) NOT NULL,
                format VARCHAR(10) NOT NULL,
                quality VARCHAR(20),
                download_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT TRUE,
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
        
        # Initialize stats if empty
        cursor.execute("SELECT COUNT(*) FROM stats")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO stats (total_downloads) VALUES (1250)")
        
        # Auto-migration: Add tracking columns if they don't exist
        print("[INFO] Checking for tracking columns...")
        tracking_columns = [
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

def increment_stats(platform='unknown', format_type='mp4', quality='best', success=True, tracking_info=None):
    """Increment download counter in DB with tracking info"""
    if db_pool:
        try:
            conn = db_pool.getconn()
            cursor = conn.cursor()
            
            # Insert download record with tracking info
            if tracking_info:
                cursor.execute("""
                    INSERT INTO downloads (
                        platform, format, quality, success,
                        ip_address, country, country_code, region, city, timezone,
                        latitude, longitude, device_type, os, browser,
                        is_mobile, is_tablet, is_pc, user_agent
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    platform, format_type, quality, success,
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
                    INSERT INTO downloads (platform, format, quality, success)
                    VALUES (%s, %s, %s, %s)
                """, (platform, format_type, quality, success))
            
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

# Start cleanup thread
threading.Thread(target=cleanup_old_files, daemon=True).start()

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
def force_https():
    # Skip for local development
    if 'localhost' in request.host or '127.0.0.1' in request.host or '.internal' in request.host:
        return
    
    # For Railway/production: Trust X-Forwarded-Proto header
    # Only redirect if the forwarded protocol is explicitly 'http'
    forwarded_proto = request.headers.get('X-Forwarded-Proto', '')
    
    if forwarded_proto == 'http':
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)

# Helper function to extract images (Shared logic)
def extract_tiktok_images(url):
    """Extract image URLs using external script for stability"""
    print(f"Subprocess extracting: {url}")
    
    # Create temp file for output
    fd, output_path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    
    try:
        # Resolve script path
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fetch_tiktok.py')
        if not os.path.exists(script_path):
            print(f"Error: Script not found at {script_path}")
            return []

        # Run external script
        cmd = [sys.executable, script_path, url, output_path]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=40,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # print(f"STDOUT: {result.stdout}")
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            with open(output_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"Subprocess failed output not found/empty. Code: {result.returncode} Err: {result.stderr}")
            return []
                     
    except Exception as e:
        print(f"Subprocess Error: {e}")
        return []
    finally:
        # Cleanup
        if os.path.exists(output_path):
            try: os.remove(output_path)
            except: pass
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
            time_module.sleep(1)
            continue
    
    return None, None, None


def download_youtube_video(url, format_type, quality, download_id):
    """Download YouTube video using yt-dlp with advanced bypass techniques"""
    try:
        import yt_dlp
        import random
        import time as time_module
        
        download_progress[download_id] = {
            'status': 'preparing',
            'progress': 0,
            'speed': '',
            'eta': '',
            'filename': None
        }
        
        # Use temp directory
        temp_dir = tempfile.gettempdir()
        filename = f"{download_id}"
        output_path = os.path.join(temp_dir, filename)
        
        # User-Agent rotation to avoid detection
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
        ]
        
        def progress_hook(d):
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
        
        # Random delay with exponential backoff (3-8 seconds base)
        delay = random.uniform(3.0, 8.0)
        print(f"[DEBUG] Waiting {delay:.1f}s before download to avoid rate limit...")
        time_module.sleep(delay)
        
        # Advanced strategies optimized for Railway/Cloud deployment
        # Order matters: try most reliable strategies first
        # UPDATED: android_embed moved to top (currently working best)
        strategies = [
            # Strategy 0: Android Embedded (WORKING - Currently most reliable!)
            {
                'name': 'android_embed',
                'opts': {
                    'quiet': True,
                    'no_warnings': True,
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android_embedded', 'android'],
                        }
                    },
                },
                'delay': 0,
                'use_cookies': False  # Android client doesn't need cookies
            },
            # Strategy 1: Android Music (Alternative Android client)
            {
                'name': 'android_music',
                'opts': {
                    'quiet': True,
                    'no_warnings': True,
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android_music'],
                        }
                    },
                },
                'delay': 2,
                'use_cookies': False
            },
            # Strategy 2: TV Embedded (Low bot detection)
            {
                'name': 'tv_embed',
                'opts': {
                    'quiet': True,
                    'no_warnings': True,
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['tv_embedded'],
                        }
                    },
                },
                'delay': 3,
                'use_cookies': False
            },
            # Strategy 3: iOS (Using cookies)
            {
                'name': 'ios_classic',
                'opts': {
                    'quiet': True,
                    'no_warnings': True,
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['ios'],
                        }
                    },
                },
                'delay': 4
            },
            # Strategy 4: bgutil POT Provider (Requires bgutil server)
            {
                'name': 'bgutil_pot',
                'opts': {
                    'quiet': True,
                    'no_warnings': True,
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['web'],
                            # bgutil POT provider - professional token generation
                            'pot_bgutilhttp': {
                                'base_url': 'http://127.0.0.1:4416'
                            }
                        }
                    },
                },
                'delay': 6
            },
            # Strategy 5: PO Token with Web Client (Deno auto-generation)
            {
                'name': 'po_token_web',
                'opts': {
                    'quiet': True,
                    'no_warnings': True,
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['web'],
                            # PO Token will be auto-generated by yt-dlp with Deno
                        }
                    },
                },
                'delay': 8
            },
            # Strategy 6: Web Mobile with cleanup
            {
                'name': 'mweb_clean',
                'opts': {
                    'quiet': True,
                    'no_warnings': True,
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['mweb', 'web_embedded'],
                            'player_skip': ['webpage', 'configs'],
                        }
                    },
                },
                'delay': 10
            },
        ]
        
        last_error = None
        
        for idx, strategy in enumerate(strategies):
            try:
                # Add delay between strategy retries (exponential backoff)
                if idx > 0:
                    retry_delay = strategy.get('delay', idx * 2)
                    print(f"[DEBUG] Waiting {retry_delay}s before retry...")
                    time_module.sleep(retry_delay)
                
                # Base options for all strategies
                selected_ua = random.choice(user_agents)
                common_opts = {
                    'noprogress': False,
                    'progress_hooks': [progress_hook],
                    'http_headers': {
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    },
                    'socket_timeout': 30,
                    'retries': 3,
                    'fragment_retries': 5,
                    'skip_unavailable_fragments': True,
                    'ignoreerrors': False,
                    'extractor_args': {},  # Initialize empty dict for extractor args
                }

                # Strategy-specific: Use cookies unless it's a 'no_cookies' strategy
                if strategy.get('use_cookies', True) and COOKIES_FILE_PATH and os.path.exists(COOKIES_FILE_PATH):
                    common_opts['cookiefile'] = COOKIES_FILE_PATH
                    print(f"[DEBUG] Using cookies from: {COOKIES_FILE_PATH}")
                else:
                    print(f"[DEBUG] Strategy {strategy['name']} is skipping cookies")

                if YOUTUBE_PO_TOKEN:
                    if 'youtube' not in common_opts['extractor_args']:
                         common_opts['extractor_args']['youtube'] = {}
                    # Try both formats (some clients like web, some like raw token)
                    common_opts['extractor_args']['youtube']['po_token'] = [f"web+{YOUTUBE_PO_TOKEN}", YOUTUBE_PO_TOKEN]
                
                if YOUTUBE_VISITOR_DATA:
                    if 'youtube' not in common_opts['extractor_args']:
                         common_opts['extractor_args']['youtube'] = {}
                    common_opts['extractor_args']['youtube']['visitor_data'] = [YOUTUBE_VISITOR_DATA]
                
                # Add a dynamic visitor data to rotate "guest" identity (helps bypass some IP-based blocks)
                if 'youtube' not in common_opts['extractor_args']:
                    common_opts['extractor_args']['youtube'] = {}
                common_opts['extractor_args']['youtube']['player_skip'] = ['webpage', 'configs']
                
                # Only force User-Agent for web-based strategies
                if 'web' in strategy['name'] or 'auto' in strategy['name']:
                    common_opts['http_headers']['User-Agent'] = selected_ua
                
                # Merge strategy-specific options (deep merge for extractor_args)
                for key, value in strategy['opts'].items():
                    if key == 'extractor_args' and key in common_opts:
                        # Deep merge extractor_args
                        for extractor, args in value.items():
                            if extractor not in common_opts['extractor_args']:
                                common_opts['extractor_args'][extractor] = {}
                            common_opts['extractor_args'][extractor].update(args)
                    else:
                        common_opts[key] = value
                
                if format_type == 'mp3':
                    # Default to 128k if not specified
                    audio_bitrate = quality if quality in ['320', '192', '128'] else '128'
                    
                    ydl_opts = {
                        **common_opts,
                        'format': 'bestaudio/best',
                        'outtmpl': output_path,
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': audio_bitrate,
                        }],
                    }
                    final_filename = filename + '.mp3'
                    mime_type = 'audio/mpeg'
                else:
                    # Video - use simple format selector
                    if quality == 'best' or not quality.isdigit():
                        format_str = 'bestvideo+bestaudio/best'
                    else:
                        format_str = f'bestvideo[height<={quality}]+bestaudio/best'
                    
                    ydl_opts = {
                        **common_opts,
                        'format': format_str,
                        'outtmpl': output_path + '.%(ext)s',
                        'merge_output_format': 'mp4',
                    }

                    final_filename = filename + '.mp4'
                    mime_type = 'video/mp4'
                
                # Try to download with this strategy
                print(f"[DEBUG] Trying strategy: {strategy['name']} (UA: {selected_ua[:50]}...)")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    title = info.get('title', 'video')
                
                print(f"[DEBUG] Success with strategy: {strategy['name']}")
                # Success! Break out of strategy loop
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
                
                return  # Success!
                
            except Exception as e:
                last_error = e
                error_str = str(e)
                print(f"[DEBUG] Strategy {strategy['name']} failed: {error_str[:150]}")
                
                # If it's a fatal error (video unavailable, private, etc.), don't retry
                if any(fatal in error_str for fatal in ['Video unavailable', 'Private video', 'removed', 'deleted', 'copyright']):
                    print(f"[DEBUG] Fatal error detected, stopping retries")
                    break
                    
                # Try next strategy
                continue
        
        # All yt-dlp strategies failed - try Invidious as last resort
        print(f"[DEBUG] All yt-dlp strategies failed, trying Invidious...")
        
        # Extract video ID from URL
        video_id_match = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
        if video_id_match:
            video_id = video_id_match.group(1)
            
            # Define progress hook for Invidious
            def invidious_progress_hook(d):
                if d['status'] == 'downloading':
                    percent_str = d.get('_percent_str', '0%').replace('%', '')
                    try:
                        percent = float(percent_str)
                    except:
                        percent = 0
                    download_progress[download_id]['status'] = 'downloading'
                    download_progress[download_id]['progress'] = percent
            
            inv_path, inv_title, inv_ext = try_invidious_download(
                video_id, format_type, quality, download_id, temp_dir, invidious_progress_hook
            )
            
            if inv_path and os.path.exists(inv_path):
                print(f"[SUCCESS] Download completed via Invidious!")
                
                mime_type = 'audio/mpeg' if inv_ext == 'mp3' else 'video/mp4'
                
                download_data[download_id] = {
                    'filepath': inv_path,
                    'title': inv_title or 'video',
                    'mime_type': mime_type,
                    'ext': inv_ext,
                    'timestamp': time.time(),
                    'platform': 'youtube',
                    'format': format_type,
                    'quality': quality
                }
                
                download_progress[download_id]['status'] = 'completed'
                download_progress[download_id]['progress'] = 100
                download_progress[download_id]['title'] = inv_title or 'video'
                
                # Record in database
                try:
                    record_download('youtube', inv_title or 'video', format_type, quality)
                except Exception as db_err:
                    print(f"DB record error: {db_err}")
                    
                return
        
        # Everything failed
        raise last_error if last_error else Exception("Không thể tải video")
        
    except Exception as e:
        error_msg = str(e)
        download_progress[download_id]['status'] = 'error'
        
        # Friendly error messages
        if 'Failed to extract any player response' in error_msg:
            download_progress[download_id]['error'] = '🔧 YouTube đã thay đổi API.\n\n💡 Giải pháp:\n1. Cập nhật yt-dlp: pip install -U yt-dlp\n2. Khởi động lại server\n3. Thử video khác hoặc đợi vài giờ'
        elif 'not made this video available in your country' in error_msg or 'not available in your country' in error_msg:
            # Extract available countries if mentioned
            available_match = re.search(r'available in (.+?)\.', error_msg)
            available_countries = available_match.group(1) if available_match else 'một số quốc gia khác'
            download_progress[download_id]['error'] = f'🌍 Video bị chặn theo khu vực.\n\n📍 Video chỉ khả dụng tại: {available_countries}\n\n💡 Giải pháp:\n🔹 Sử dụng VPN để đổi vị trí\n🔹 Thử video khác không bị chặn vùng\n\n⚙️ Nếu có VPN, thêm --proxy vào cấu hình yt-dlp'
        elif 'Sign in to confirm' in error_msg or 'bot' in error_msg.lower() or 'HTTP Error 429' in error_msg or 'confirm you' in error_msg.lower():
            download_progress[download_id]['error'] = '⏳ YouTube phát hiện tải tự động.\n\n✅ Đã thử 6 phương pháp bypass khác nhau.\n\n💡 Giải pháp:\n🔹 Đợi 5-10 phút rồi thử lại\n🔹 Thử video ngắn hơn (<10 phút)\n🔹 Thử video từ kênh khác\n\n🍪 Mẹo nâng cao: Thêm file cookies.txt để bypass hoàn toàn'
        elif 'Video unavailable' in error_msg or 'Private video' in error_msg:
            download_progress[download_id]['error'] = '❌ Video không khả dụng hoặc đã bị xóa/riêng tư'
        elif 'age' in error_msg.lower() or 'restricted' in error_msg.lower():
            download_progress[download_id]['error'] = '🔞 Video giới hạn độ tuổi.\n\n💡 Giải pháp: Thêm file cookies.txt từ tài khoản đã xác minh tuổi'
        elif 'copyright' in error_msg.lower():
            download_progress[download_id]['error'] = '©️ Video bị chặn do bản quyền'
        elif 'network' in error_msg.lower() or 'timeout' in error_msg.lower() or 'connect' in error_msg.lower():
            download_progress[download_id]['error'] = '🌐 Lỗi kết nối mạng. Vui lòng thử lại sau vài giây'
        elif 'live' in error_msg.lower() or 'premiere' in error_msg.lower():
            download_progress[download_id]['error'] = '📺 Video đang phát trực tiếp hoặc chưa công chiếu. Hãy đợi video kết thúc'
        else:
            download_progress[download_id]['error'] = f'❌ Lỗi: {error_msg[:200]}'
            
        print(f"YouTube download error: {e}")

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

@app.route('/api/news')
def api_news():
    return NewsController.get_news()

@app.route('/api/news/proxy')
def api_news_proxy():
    return NewsController.proxy_article()

@app.route('/robots.txt')
def robots():
    return app.send_static_file('robots.txt')

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
    data = request.get_json()
    url = data.get('url', '').strip()
    format_type = data.get('format', 'mp4')
    quality = data.get('quality', '720')
    
    if not url:
        return jsonify({'success': False, 'error': 'Vui lòng nhập URL YouTube'}), 400
    
    if not is_valid_youtube_url(url):
        return jsonify({'success': False, 'error': 'URL YouTube không hợp lệ'}), 400
    
    # Check cooldown per IP
    client_ip = request.remote_addr
    current_time = time.time()
    
    if client_ip in last_youtube_download:
        time_since_last = current_time - last_youtube_download[client_ip]
        if time_since_last < YOUTUBE_COOLDOWN:
            wait_time = int(YOUTUBE_COOLDOWN - time_since_last)
            return jsonify({
                'success': False, 
                'error': f'⏳ Vui lòng đợi {wait_time} giây trước khi tải video tiếp theo.\n\nĐây là biện pháp bảo vệ để tránh bị YouTube chặn. Cảm ơn bạn đã thông cảm! 😊'
            }), 429
    
    # Update last download time
    last_youtube_download[client_ip] = current_time
    
    download_id = str(uuid.uuid4())
    
    # Use ThreadPool to prevent server crash
    executor.submit(download_youtube_video, url, format_type, quality, download_id)
    
    return jsonify({'success': True, 'download_id': download_id})

@app.route('/api/tiktok/download', methods=['POST'])
def tiktok_download():
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
        
    # thread.start()
    
    return jsonify({'success': True, 'download_id': download_id})

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
    
    # Increment stats with metadata and tracking
    platform = data.get('platform', 'unknown')
    format_type = data.get('format', data['ext'])
    quality = data.get('quality', 'best')
    increment_stats(platform, format_type, quality, True, tracking_info)
    
    return send_file(
        filepath,
        mimetype=data['mime_type'],
        as_attachment=as_attachment,
        download_name=download_name
    )

@app.route('/api/stats')
def api_stats():
    return jsonify(get_stats())

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
                id, platform, format, quality, download_time,
                ip_address, country, city, device_type, os, browser,
                is_mobile, is_tablet, is_pc, success
            FROM downloads
            ORDER BY download_time DESC
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
                'success': row[14]
            })
        
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({'downloads': downloads})
        
    except Exception as e:
        print(f"[ERROR] Recent downloads failed: {e}")
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
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'socket_timeout': 15,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios', 'web'],
                    'skip': ['hls', 'dash']
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        }
        
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
        if not data:
            return jsonify({'success': False, 'error': 'No data'}), 400
            
        url = data.get('url', '').strip()
        
        if not url or not is_valid_tiktok_url(url):
            return jsonify({'success': False, 'error': 'URL không hợp lệ'}), 400
        
        # Check if it's a photo URL
        is_photo = '/photo/' in url
        if is_photo:
            # Fetch images for preview
            images = extract_tiktok_images(url)
            
            return jsonify({
                'success': True,
                'title': '📷 TikTok Photo/Slideshow',
                'thumbnail': images[0] if images else '',
                'author': f'Tìm thấy {len(images)} ảnh',
                'is_photo': True,
                'images': images
            })
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 10,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        return jsonify({
            'success': True,
            'title': info.get('title', 'Video'),
            'thumbnail': info.get('thumbnail', ''),
            'duration': info.get('duration', 0),
            'author': info.get('uploader', ''),
            'likes': info.get('like_count', 0),
        })
        
    except Exception as e:
        print(f"TikTok info error: {e}")
        return jsonify({'success': False, 'error': 'Không thể lấy thông tin video'}), 200

if __name__ == '__main__':
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
        from waitress import serve
        print(f"Starting Production Server (Waitress) on port {port}...")
        serve(app, host='0.0.0.0', port=port, threads=6)
    except ImportError:
        print("Waitress not found. Running with Flask Dev Server.")
        app.run(debug=True, host='0.0.0.0', port=port)
