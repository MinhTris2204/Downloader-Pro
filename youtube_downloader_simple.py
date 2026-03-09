"""
Simple YouTube Downloader using yt-dlp
Optimized version - stable and minimal code
"""

import os
import tempfile
import time
import yt_dlp


def download_youtube_simple(url, format_type='mp4', quality='best', download_id=None, progress_callback=None):
    """
    Download YouTube video/audio using yt-dlp
    
    Args:
        url: YouTube video URL
        format_type: 'mp4' for video or 'mp3' for audio
        quality: 'best', '1080', '720', '480', '360' for video; '320', '192', '128' for audio
        download_id: Unique ID for this download
        progress_callback: Function to call with progress updates
    
    Returns:
        dict with filepath, title, mime_type, ext
    """
    
    # Use temp directory for downloads
    temp_dir = tempfile.gettempdir()
    filename = download_id or f"download_{int(time.time())}"
    output_path = os.path.join(temp_dir, filename)
    
    def progress_hook(d):
        """Track download progress"""
        if progress_callback and d['status'] == 'downloading':
            # Calculate percentage
            if 'downloaded_bytes' in d and 'total_bytes' in d and d['total_bytes']:
                percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                progress_callback({
                    'status': 'downloading',
                    'progress': round(percent, 1),
                    'speed': d.get('_speed_str', ''),
                    'eta': d.get('_eta_str', '')
                })
        elif progress_callback and d['status'] == 'finished':
            progress_callback({
                'status': 'processing',
                'progress': 100
            })
    
    # Configure yt-dlp options
    if format_type == 'mp3':
        # Audio download - extract best audio and convert to MP3
        audio_bitrate = quality if quality in ['320', '192', '128'] else '192'
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'noplaylist': True,
            'progress_hooks': [progress_hook],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': audio_bitrate,
            }],
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
            'progress_hooks': [progress_hook],
        }
        final_filename = filename + '.mp4'
        mime_type = 'video/mp4'
    
    # Add cookies if available (optional - helps with age-restricted videos)
    cookies_path = os.environ.get('YOUTUBE_COOKIES_PATH')
    if cookies_path and os.path.exists(cookies_path):
        ydl_opts['cookiefile'] = cookies_path
        print(f"[INFO] Using cookies from: {cookies_path}")
    
    # Add proxy if configured (optional - helps bypass IP blocks)
    proxy = os.environ.get('HTTP_PROXY') or os.environ.get('HTTPS_PROXY')
    if proxy:
        ydl_opts['proxy'] = proxy
        print(f"[INFO] Using proxy")
    
    # Download the video/audio
    print(f"[INFO] Starting download: {url}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get('title', 'video')
    
    filepath = os.path.join(temp_dir, final_filename)
    
    print(f"[SUCCESS] Download completed: {title}")
    
    return {
        'filepath': filepath,
        'title': title,
        'mime_type': mime_type,
        'ext': final_filename.split('.')[-1],
        'timestamp': time.time()
    }


# Example usage
if __name__ == '__main__':
    # Test download
    url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
    
    def progress_callback(data):
        print(f"Progress: {data.get('progress', 0)}% - {data.get('status')}")
    
    try:
        result = download_youtube_simple(
            url=url,
            format_type='mp4',
            quality='720',
            progress_callback=progress_callback
        )
        print(f"\nDownloaded: {result['title']}")
        print(f"File: {result['filepath']}")
    except Exception as e:
        print(f"Error: {e}")
