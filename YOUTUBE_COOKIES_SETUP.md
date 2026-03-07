# Hướng Dẫn Cấu Hình YouTube Cookies

## Vấn Đề
YouTube yêu cầu xác thực cookies để chống bot. Lỗi:
```
ERROR: Sign in to confirm you're not a bot
```

## Giải Pháp: Thêm Cookies

### Cách 1: Sử dụng Extension (Dễ nhất)

1. **Cài Extension:**
   - Chrome/Edge: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - Firefox: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

2. **Export Cookies:**
   - Đăng nhập YouTube trên trình duyệt
   - Mở trang youtube.com
   - Click vào icon extension
   - Click "Export" → Lưu file `cookies.txt`

3. **Upload lên Server:**
   
   **Railway:**
   ```bash
   # Encode cookies thành base64
   base64 -w 0 cookies.txt > cookies_base64.txt
   
   # Copy nội dung cookies_base64.txt
   # Vào Railway → Variables → Add:
   # YOUTUBE_COOKIES=<paste nội dung cookies_base64.txt>
   ```
   
   **Hoặc upload trực tiếp:**
   - Upload file `cookies.txt` vào thư mục gốc project
   - Commit và push lên Git

### Cách 2: Sử dụng yt-dlp CLI

```bash
# Export cookies từ Chrome
yt-dlp --cookies-from-browser chrome --cookies cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Hoặc từ Firefox
yt-dlp --cookies-from-browser firefox --cookies cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

## Kiểm Tra

Sau khi thêm cookies, restart server và thử tải video. Log sẽ hiển thị:
```
[DEBUG] Using cookies from: /tmp/yt_cookies.txt
```

## Lưu Ý

- Cookies có thời hạn (thường 1-2 tháng)
- Cần refresh cookies định kỳ
- Không chia sẻ file cookies (chứa thông tin đăng nhập)
- Nên dùng tài khoản phụ, không dùng tài khoản chính

## Troubleshooting

**Lỗi vẫn còn sau khi thêm cookies:**
1. Kiểm tra cookies chưa hết hạn
2. Đảm bảo đã đăng nhập YouTube khi export
3. Thử export lại cookies mới
4. Restart server sau khi thêm cookies

**Cookies bị reject:**
- YouTube phát hiện cookies từ nhiều IP khác nhau
- Giải pháp: Export cookies mới từ cùng IP với server
