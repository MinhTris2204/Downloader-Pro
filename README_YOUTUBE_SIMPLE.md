# YouTube Downloader - Phiên bản đơn giản với yt-dlp

## 📋 Tổng quan

Đây là phiên bản đơn giản, ổn định và dễ bảo trì của YouTube Downloader sử dụng thư viện **yt-dlp** - một fork mạnh mẽ và được cập nhật liên tục từ youtube-dl.

### ✨ Ưu điểm của yt-dlp

- ⭐ **Ổn định**: Được cập nhật liên tục để theo kịp thay đổi của YouTube
- 🚀 **Nhanh**: Tốc độ download tốt hơn pytube
- 🛡️ **Bypass bot detection**: Xử lý tốt các biện pháp chống bot của YouTube
- 📦 **Hỗ trợ nhiều format**: MP4, MP3, WebM, và nhiều format khác
- 🔧 **Dễ bảo trì**: Code đơn giản, ít lỗi

## 📁 Files trong package

```
Downloader-Pro/
├── youtube_downloader_simple.py    # Module chính - hàm download
├── app_simple_example.py           # Flask API server mẫu
├── YOUTUBE_SIMPLE_GUIDE.md         # Hướng dẫn chi tiết
└── README_YOUTUBE_SIMPLE.md        # File này
```

## 🚀 Quick Start

### 1. Cài đặt dependencies

```bash
# Cài đặt Python packages
pip install flask yt-dlp

# Cài đặt FFmpeg (BẮT BUỘC)
# Windows: Tải từ https://ffmpeg.org/download.html
# Ubuntu/Linux:
sudo apt update && sudo apt install ffmpeg

# macOS:
brew install ffmpeg
```

### 2. Test download đơn giản

```python
from youtube_downloader_simple import download_youtube_simple

# Tải video MP4 720p
result = download_youtube_simple(
    url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    format_type='mp4',
    quality='720'
)

print(f"Downloaded: {result['title']}")
print(f"File path: {result['filepath']}")
```

### 3. Chạy Flask API server

```bash
python app_simple_example.py
```

Server sẽ chạy tại: http://127.0.0.1:5000

### 4. Test API với cURL

```bash
# Tải video MP4
curl -X POST http://127.0.0.1:5000/api/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "format": "mp4", "quality": "720"}'

# Response: {"download_id": "unique-id"}

# Kiểm tra progress
curl http://127.0.0.1:5000/api/progress/unique-id

# Tải file về
curl http://127.0.0.1:5000/api/file/unique-id --output video.mp4
```

## 📖 API Endpoints

### POST /api/download
Bắt đầu download video/audio

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "format": "mp4",
  "quality": "720"
}
```

**Response:**
```json
{
  "download_id": "unique-id"
}
```

### GET /api/progress/:download_id
Kiểm tra tiến trình download

**Response:**
```json
{
  "status": "downloading",
  "progress": 45.5,
  "speed": "1.2MB/s",
  "eta": "00:05",
  "title": "Video Title"
}
```

### GET /api/file/:download_id
Download file đã hoàn thành

### POST /api/info
Lấy thông tin video (không download)

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

## ⚙️ Cấu hình

### Format & Quality

**Video (MP4):**
- `quality`: `'best'`, `'1080'`, `'720'`, `'480'`, `'360'`

**Audio (MP3):**
- `quality`: `'320'`, `'192'`, `'128'` (kbps)

### Cookies (Optional - cho video giới hạn độ tuổi)

```bash
# Export cookies từ trình duyệt (dùng extension "Get cookies.txt")
# Lưu vào file cookies.txt
export YOUTUBE_COOKIES_PATH=/path/to/cookies.txt
```

### Proxy (Optional - bypass IP blocks)

```bash
export HTTP_PROXY=http://proxy-server:port
# hoặc
export HTTPS_PROXY=https://proxy-server:port
```

## 🔧 Troubleshooting

### Lỗi: "FFmpeg not found"
**Giải pháp:** Cài đặt FFmpeg (xem phần Quick Start)

### Lỗi: "Sign in to confirm you're not a bot"
**Giải pháp:** 
- Thêm cookies từ tài khoản YouTube đã đăng nhập
- Hoặc thêm proxy để đổi IP
- Đợi 10-30 phút rồi thử lại

### Lỗi: "Video unavailable"
**Giải pháp:**
- Video bị xóa, riêng tư, hoặc chặn vùng
- Thử video khác hoặc dùng VPN

### Lỗi: "HTTP Error 429"
**Giải pháp:**
- Quá nhiều requests - đợi 10-30 phút
- Thêm proxy để rotate IP

## 🔄 Cập nhật yt-dlp

YouTube thường xuyên thay đổi API, nên cập nhật yt-dlp định kỳ:

```bash
pip install -U yt-dlp
```

Khuyến nghị: Cập nhật ít nhất 1 tháng/lần.

## 📊 So sánh với pytube

| Tính năng | yt-dlp | pytube |
|-----------|--------|--------|
| Độ ổn định | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Cập nhật | Liên tục (hàng tuần) | Ít (hàng tháng) |
| Hỗ trợ format | Rất nhiều | Hạn chế |
| Tốc độ download | Nhanh | Trung bình |
| Bypass bot detection | Tốt | Yếu |
| Xử lý lỗi | Tốt | Hay bị lỗi |
| Community | Lớn, active | Nhỏ hơn |

## 🔗 Tích hợp vào app hiện tại

Để tích hợp vào `app.py` hiện tại của bạn:

1. Import module:
```python
from youtube_downloader_simple import download_youtube_simple
```

2. Thay thế hàm `download_youtube_video()` hiện tại bằng:
```python
def download_youtube_video(url, format_type, quality, download_id):
    try:
        def progress_callback(data):
            download_progress[download_id] = data
        
        result = download_youtube_simple(
            url=url,
            format_type=format_type,
            quality=quality,
            download_id=download_id,
            progress_callback=progress_callback
        )
        
        download_data[download_id] = result
        download_progress[download_id]['status'] = 'completed'
        
    except Exception as e:
        download_progress[download_id] = {
            'status': 'error',
            'error': str(e)
        }
```

## 📚 Tài liệu tham khảo

- **yt-dlp GitHub**: https://github.com/yt-dlp/yt-dlp
- **yt-dlp Documentation**: https://github.com/yt-dlp/yt-dlp#usage-and-options
- **FFmpeg**: https://ffmpeg.org/
- **Flask**: https://flask.palletsprojects.com/

## 💡 Tips

1. **Luôn cập nhật yt-dlp**: `pip install -U yt-dlp`
2. **Sử dụng proxy** nếu gặp lỗi bot detection thường xuyên
3. **Thêm cookies** cho video giới hạn độ tuổi
4. **Cleanup files cũ** trong temp directory định kỳ
5. **Monitor logs** để phát hiện lỗi sớm

## 📝 License

Code này sử dụng yt-dlp (Unlicense license) và có thể tự do sử dụng cho mục đích cá nhân và thương mại.

## 🤝 Support

Nếu gặp vấn đề:
1. Kiểm tra phần Troubleshooting
2. Cập nhật yt-dlp: `pip install -U yt-dlp`
3. Kiểm tra FFmpeg: `ffmpeg -version`
4. Xem logs để biết lỗi cụ thể

---

**Lưu ý**: Hãy tôn trọng bản quyền và chỉ download video bạn có quyền sử dụng.
