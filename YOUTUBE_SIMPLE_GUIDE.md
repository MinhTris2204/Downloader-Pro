# Hướng dẫn sử dụng YouTube Downloader đơn giản với yt-dlp

## Tổng quan

File `youtube_downloader_simple.py` cung cấp một giải pháp đơn giản, ổn định để tải video/audio từ YouTube sử dụng thư viện `yt-dlp`.

## Yêu cầu hệ thống

### 1. Cài đặt Python packages

```bash
pip install flask yt-dlp
```

### 2. Cài đặt FFmpeg (BẮT BUỘC)

FFmpeg cần thiết để:
- Hợp nhất video + audio cho MP4 chất lượng cao
- Chuyển đổi audio sang MP3

**Windows:**
- Tải từ: https://ffmpeg.org/download.html
- Giải nén và thêm thư mục `bin` vào PATH

**Ubuntu/Linux:**
```bash
sudo apt update && sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

## Cách sử dụng

### Sử dụng độc lập (Standalone)

```python
from youtube_downloader_simple import download_youtube_simple

# Tải video MP4
result = download_youtube_simple(
    url='https://www.youtube.com/watch?v=VIDEO_ID',
    format_type='mp4',
    quality='720'
)

print(f"Downloaded: {result['filepath']}")

# Tải audio MP3
result = download_youtube_simple(
    url='https://www.youtube.com/watch?v=VIDEO_ID',
    format_type='mp3',
    quality='192'
)
```

### Tích hợp vào Flask app

```python
from flask import Flask, request, jsonify, send_file
from youtube_downloader_simple import download_youtube_simple
import threading

app = Flask(__name__)

# Dictionary để lưu progress
download_progress = {}

@app.route('/api/download', methods=['POST'])
def download_video():
    data = request.get_json()
    url = data.get('url')
    format_type = data.get('format', 'mp4')
    quality = data.get('quality', 'best')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    # Generate download ID
    import uuid
    download_id = str(uuid.uuid4())
    
    # Progress callback
    def progress_callback(progress_data):
        download_progress[download_id] = progress_data
    
    # Download in background thread
    def download_task():
        try:
            result = download_youtube_simple(
                url=url,
                format_type=format_type,
                quality=quality,
                download_id=download_id,
                progress_callback=progress_callback
            )
            
            download_progress[download_id] = {
                'status': 'completed',
                'filepath': result['filepath'],
                'title': result['title']
            }
        except Exception as e:
            download_progress[download_id] = {
                'status': 'error',
                'error': str(e)
            }
    
    thread = threading.Thread(target=download_task)
    thread.start()
    
    return jsonify({'download_id': download_id})

@app.route('/api/progress/<download_id>')
def get_progress(download_id):
    progress = download_progress.get(download_id, {'status': 'not_found'})
    return jsonify(progress)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

## Tham số

### format_type
- `'mp4'`: Tải video (mặc định)
- `'mp3'`: Tải audio

### quality

**Cho video (mp4):**
- `'best'`: Chất lượng tốt nhất (mặc định)
- `'1080'`: Full HD 1080p
- `'720'`: HD 720p
- `'480'`: SD 480p
- `'360'`: 360p

**Cho audio (mp3):**
- `'320'`: 320kbps (chất lượng cao nhất)
- `'192'`: 192kbps (mặc định - cân bằng)
- `'128'`: 128kbps (tiết kiệm dung lượng)

## Xử lý lỗi

```python
try:
    result = download_youtube_simple(url=url)
except Exception as e:
    error_msg = str(e)
    
    if 'not available' in error_msg.lower():
        print("Video không khả dụng hoặc bị chặn vùng")
    elif 'Sign in' in error_msg or '429' in error_msg:
        print("YouTube phát hiện bot - cần thêm cookies hoặc proxy")
    elif 'age' in error_msg.lower():
        print("Video giới hạn độ tuổi - cần cookies")
    else:
        print(f"Lỗi: {error_msg}")
```

## Cấu hình nâng cao (Optional)

### Thêm Cookies (cho video giới hạn độ tuổi)

1. Export cookies từ trình duyệt (dùng extension như "Get cookies.txt")
2. Lưu vào file `cookies.txt`
3. Set biến môi trường:

```bash
export YOUTUBE_COOKIES_PATH=/path/to/cookies.txt
```

### Thêm Proxy (bypass IP blocks)

```bash
export HTTP_PROXY=http://proxy-server:port
# hoặc
export HTTPS_PROXY=https://proxy-server:port
```

## So sánh với pytube

| Tính năng | yt-dlp | pytube |
|-----------|--------|--------|
| Độ ổn định | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Cập nhật | Liên tục | Ít |
| Hỗ trợ format | Nhiều | Hạn chế |
| Tốc độ | Nhanh | Trung bình |
| Bypass bot detection | Tốt | Yếu |

## Troubleshooting

### Lỗi: "FFmpeg not found"
- Cài đặt FFmpeg (xem phần Yêu cầu hệ thống)
- Kiểm tra: `ffmpeg -version`

### Lỗi: "Sign in to confirm you're not a bot"
- Thêm cookies từ tài khoản YouTube đã đăng nhập
- Hoặc thêm proxy để đổi IP

### Lỗi: "Video unavailable"
- Video bị xóa, riêng tư, hoặc chặn vùng
- Thử video khác hoặc dùng VPN

### Lỗi: "HTTP Error 429"
- Quá nhiều requests - đợi 10-30 phút
- Thêm proxy để rotate IP

## Cập nhật yt-dlp

yt-dlp được cập nhật thường xuyên để theo kịp thay đổi của YouTube:

```bash
pip install -U yt-dlp
```

Nên cập nhật ít nhất 1 tháng/lần.

## Tài liệu tham khảo

- yt-dlp GitHub: https://github.com/yt-dlp/yt-dlp
- FFmpeg: https://ffmpeg.org/
- yt-dlp Documentation: https://github.com/yt-dlp/yt-dlp#usage-and-options
