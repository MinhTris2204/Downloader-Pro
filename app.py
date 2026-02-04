from flask import Flask, render_template, request, jsonify, redirect
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

app = Flask(__name__)
# Fix for Proxy (Railway SSL)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

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
                success BOOLEAN DEFAULT TRUE
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

def increment_stats(platform='unknown', format_type='mp4', quality='best', success=True):
    """Increment download counter in DB"""
    if db_pool:
        try:
            conn = db_pool.getconn()
            cursor = conn.cursor()
            
            # Insert download record
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

def download_youtube_video(url, format_type, quality, download_id):
    """Download YouTube video using yt-dlp"""
    try:
        import yt_dlp
        
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
        
        if format_type == 'mp3':
            # Default to 128k if not specified
            audio_bitrate = quality if quality in ['320', '192', '128'] else '128'
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_path, # No ext, postprocessor handles it
                'progress_hooks': [progress_hook],
                'quiet': True,
                'no_warnings': True,
                'noprogress': False,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': audio_bitrate,
                }],
            }
            final_filename = filename + '.mp3'
            mime_type = 'audio/mpeg'
        else:
            # Video
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': output_path + '.mp4',
                'progress_hooks': [progress_hook],
                'quiet': True,
                'no_warnings': True,
                'noprogress': False,
            }
            
            if quality != 'best' and quality.isdigit():
                res = int(quality)
                # Try close match
                ydl_opts['format'] = f'best[height<={res}][ext=mp4]/best[height<={res}]/best'
                # Force scale
                ydl_opts['postprocessors'] = [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}]
                ydl_opts['postprocessor_args'] = ['-vf', f'scale=-2:{res}']

            final_filename = filename + '.mp4'
            mime_type = 'video/mp4'
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'video')
        
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
        
    except Exception as e:
        download_progress[download_id]['status'] = 'error'
        download_progress[download_id]['error'] = str(e)
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
    return render_template('index.html')

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
    
    download_id = str(uuid.uuid4())
    
    # Use ThreadPool to prevent server crash
    executor.submit(download_youtube_video, url, format_type, quality, download_id)
    # thread = threading.Thread(target=download_youtube_video, args=(url, format_type, quality, download_id))
    # thread.start()
    
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
    
    # Increment stats with metadata
    platform = data.get('platform', 'unknown')
    format_type = data.get('format', data['ext'])
    quality = data.get('quality', 'best')
    increment_stats(platform, format_type, quality, True)
    
    return send_file(
        filepath,
        mimetype=data['mime_type'],
        as_attachment=as_attachment,
        download_name=download_name
    )

@app.route('/api/stats')
def api_stats():
    return jsonify(get_stats())

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
            'views': info.get('view_count', 0),
        })
        
    except Exception as e:
        print(f"YouTube info error: {e}")
        return jsonify({'success': False, 'error': 'Không thể lấy thông tin video'}), 200

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
    try:
        from waitress import serve
        print(f"Starting Production Server (Waitress) on port {port}...")
        serve(app, host='0.0.0.0', port=port, threads=6)
    except ImportError:
        print("Waitress not found. Running with Flask Dev Server.")
        app.run(debug=True, host='0.0.0.0', port=port)
