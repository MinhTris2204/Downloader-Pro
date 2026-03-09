"""
Simple Flask Backend for YouTube Downloader
Using yt-dlp - Minimal and stable implementation
"""

import os
import uuid
import threading
from flask import Flask, request, jsonify, send_file
from youtube_downloader_simple import download_youtube_simple

app = Flask(__name__)

# Store download progress and data
download_progress = {}
download_data = {}


@app.route('/api/download', methods=['POST'])
def download_media():
    """
    Download YouTube video/audio
    
    Request JSON:
    {
        "url": "https://www.youtube.com/watch?v=VIDEO_ID",
        "format": "mp4" or "mp3",
        "quality": "best", "1080", "720", "480", "360" (for video) or "320", "192", "128" (for audio)
    }
    
    Response:
    {
        "download_id": "unique-id"
    }
    """
    data = request.get_json()
    
    # Validate input
    if not data or 'url' not in data:
        return jsonify({"error": "Vui lòng cung cấp URL YouTube (field: 'url')"}), 400
    
    url = data['url']
    format_type = data.get('format', 'mp4').lower()
    quality = data.get('quality', 'best')
    
    if format_type not in ['mp4', 'mp3']:
        return jsonify({"error": "Định dạng không hợp lệ. Chỉ hỗ trợ 'mp4' hoặc 'mp3'"}), 400
    
    # Generate unique download ID
    download_id = str(uuid.uuid4())
    
    # Initialize progress
    download_progress[download_id] = {
        'status': 'preparing',
        'progress': 0
    }
    
    # Progress callback function
    def progress_callback(progress_data):
        download_progress[download_id] = progress_data
    
    # Download task (runs in background thread)
    def download_task():
        try:
            result = download_youtube_simple(
                url=url,
                format_type=format_type,
                quality=quality,
                download_id=download_id,
                progress_callback=progress_callback
            )
            
            # Store download data
            download_data[download_id] = result
            
            # Update progress to completed
            download_progress[download_id] = {
                'status': 'completed',
                'progress': 100,
                'title': result['title']
            }
            
        except Exception as e:
            error_msg = str(e)
            
            # Friendly error messages
            if 'not available' in error_msg.lower():
                error = 'Video không khả dụng hoặc bị chặn vùng'
            elif 'Sign in' in error_msg or '429' in error_msg:
                error = 'YouTube phát hiện bot. Vui lòng thử lại sau 10-30 phút'
            elif 'age' in error_msg.lower():
                error = 'Video giới hạn độ tuổi. Cần thêm cookies'
            elif 'copyright' in error_msg.lower():
                error = 'Video bị chặn do bản quyền'
            else:
                error = f'Lỗi: {error_msg[:150]}'
            
            download_progress[download_id] = {
                'status': 'error',
                'error': error
            }
    
    # Start download in background thread
    thread = threading.Thread(target=download_task)
    thread.daemon = True
    thread.start()
    
    return jsonify({'download_id': download_id})


@app.route('/api/progress/<download_id>')
def get_progress(download_id):
    """
    Get download progress
    
    Response:
    {
        "status": "preparing" | "downloading" | "processing" | "completed" | "error",
        "progress": 0-100,
        "speed": "1.2MB/s",
        "eta": "00:05",
        "title": "Video Title",
        "error": "Error message" (if status is error)
    }
    """
    progress = download_progress.get(download_id, {'status': 'not_found'})
    return jsonify(progress)


@app.route('/api/file/<download_id>')
def get_file(download_id):
    """
    Download the completed file
    """
    if download_id not in download_data:
        return jsonify({'error': 'File not found'}), 404
    
    data = download_data[download_id]
    filepath = data['filepath']
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found on server'}), 404
    
    # Send file as attachment
    return send_file(
        filepath,
        as_attachment=True,
        download_name=f"{data['title']}.{data['ext']}",
        mimetype=data['mime_type']
    )


@app.route('/api/info', methods=['POST'])
def get_video_info():
    """
    Get video information without downloading
    
    Request JSON:
    {
        "url": "https://www.youtube.com/watch?v=VIDEO_ID"
    }
    
    Response:
    {
        "title": "Video Title",
        "duration": 180,
        "thumbnail": "https://...",
        "formats": [...]
    }
    """
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({"error": "URL is required"}), 400
    
    url = data['url']
    
    try:
        import yt_dlp
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            return jsonify({
                'title': info.get('title'),
                'duration': info.get('duration'),
                'thumbnail': info.get('thumbnail'),
                'uploader': info.get('uploader'),
                'view_count': info.get('view_count'),
                'description': info.get('description', '')[:200]
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/')
def index():
    """Simple test page"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>YouTube Downloader API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #333; }
            .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
            code { background: #e0e0e0; padding: 2px 5px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>YouTube Downloader API</h1>
        <p>Simple and stable YouTube downloader using yt-dlp</p>
        
        <div class="endpoint">
            <h3>POST /api/download</h3>
            <p>Start a download</p>
            <code>{"url": "...", "format": "mp4", "quality": "720"}</code>
        </div>
        
        <div class="endpoint">
            <h3>GET /api/progress/&lt;download_id&gt;</h3>
            <p>Check download progress</p>
        </div>
        
        <div class="endpoint">
            <h3>GET /api/file/&lt;download_id&gt;</h3>
            <p>Download the completed file</p>
        </div>
        
        <div class="endpoint">
            <h3>POST /api/info</h3>
            <p>Get video information</p>
            <code>{"url": "..."}</code>
        </div>
        
        <h2>Example with cURL:</h2>
        <pre>
# Download MP4
curl -X POST http://127.0.0.1:5000/api/download \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "format": "mp4"}'

# Download MP3
curl -X POST http://127.0.0.1:5000/api/download \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "format": "mp3", "quality": "192"}'
        </pre>
    </body>
    </html>
    '''


if __name__ == '__main__':
    print("="*60)
    print("YouTube Downloader API Server")
    print("="*60)
    print("Server running at: http://127.0.0.1:5000")
    print("API Documentation: http://127.0.0.1:5000")
    print("="*60)
    
    app.run(debug=True, port=5000)
