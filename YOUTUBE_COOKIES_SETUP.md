# 🔧 Hướng Dẫn Cấu Hình YouTube Cookies

## ⚠️ Vấn Đề
YouTube yêu cầu xác thực cookies để chống bot. Khi cookies hết hạn, bạn sẽ thấy lỗi:
```
ERROR: Sign in to confirm you're not a bot
```

**Dấu hiệu cookies đã hết hạn:**
- Tất cả video YouTube đều báo lỗi bot detection
- Log hiển thị: `[FAILED] ❌ Strategy 'ios_cookies' failed`
- Người dùng không thể tải được bất kỳ video YouTube nào

**Tần suất cập nhật:** Cookies thường hết hạn sau 1-2 tháng, cần refresh định kỳ.

---

## ✅ Giải Pháp: Cập Nhật Cookies Mới

### 🎯 Cách 1: Sử dụng Extension (Khuyến nghị - Dễ nhất)

#### Bước 1: Cài Extension

**Chrome/Edge:**
- Truy cập: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
- Click "Add to Chrome"

**Firefox:**
- Truy cập: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
- Click "Add to Firefox"

#### Bước 2: Export Cookies

1. **Đăng nhập YouTube:**
   - Mở trình duyệt đã cài extension
   - Truy cập https://www.youtube.com
   - Đăng nhập tài khoản YouTube (nên dùng tài khoản phụ)
   - Xem 1-2 video để "làm ấm" cookies

2. **Export cookies:**
   - Ở trang youtube.com, click vào icon extension (góc trên bên phải)
   - Click "Export" hoặc "Download"
   - Lưu file với tên `cookies.txt`

#### Bước 3: Upload lên Railway

**Option A: Sử dụng Environment Variable (Khuyến nghị)**

```bash
# Trên máy local (Linux/Mac):
base64 -w 0 cookies.txt > cookies_base64.txt

# Trên Windows (PowerShell):
[Convert]::ToBase64String([IO.File]::ReadAllBytes("cookies.txt")) | Out-File -Encoding ASCII cookies_base64.txt
```

Sau đó:
1. Mở file `cookies_base64.txt`
2. Copy toàn bộ nội dung (1 dòng dài)
3. Vào Railway Dashboard → Project → Variables
4. Thêm biến mới:
   - Name: `YOUTUBE_COOKIES`
   - Value: Paste nội dung đã copy
5. Click "Add" → Railway sẽ tự động restart

**Option B: Upload trực tiếp vào Git (Không khuyến nghị - kém bảo mật)**

```bash
# Copy cookies.txt vào thư mục gốc project
cp cookies.txt /path/to/Downloader-Pro/

# Commit và push
git add cookies.txt
git commit -m "Update YouTube cookies"
git push
```

⚠️ **Lưu ý:** Không nên commit cookies.txt vào Git vì lý do bảo mật. Nên dùng Option A.

### 🔧 Cách 2: Sử dụng yt-dlp CLI (Cho người dùng nâng cao)

```bash
# Export cookies từ Chrome
yt-dlp --cookies-from-browser chrome --cookies cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Hoặc từ Firefox
yt-dlp --cookies-from-browser firefox --cookies cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Hoặc từ Edge
yt-dlp --cookies-from-browser edge --cookies cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

Sau khi có file `cookies.txt`, làm theo Bước 3 ở Cách 1.

---

## 🧪 Kiểm Tra Cookies Đã Hoạt Động

### Cách 1: Xem Log Server

Sau khi thêm cookies và restart server, kiểm tra log:

```
✅ Thành công:
[SUCCESS] YouTube cookies loaded from environment variable (4578 bytes)
[DEBUG] Using cookies from: /tmp/yt_cookies.txt

❌ Thất bại:
[WARNING] No YouTube auth configured!
[WARNING] Failed to decode YOUTUBE_COOKIES: ...
```

### Cách 2: Thử Tải Video

1. Vào trang chủ website
2. Thử tải 1 video YouTube bất kỳ
3. Nếu thành công → Cookies đã hoạt động ✅
4. Nếu vẫn lỗi bot → Kiểm tra lại cookies

---

## 📝 Lưu Ý Quan Trọng

### Bảo Mật
- ⚠️ **Không chia sẻ file cookies** - Chứa thông tin đăng nhập của bạn
- 🔐 **Nên dùng tài khoản phụ** - Không dùng tài khoản YouTube chính
- 🗑️ **Xóa cookies.txt local** sau khi upload lên Railway

### Thời Hạn
- ⏰ Cookies thường hết hạn sau **1-2 tháng**
- 📅 Nên đặt lịch nhắc refresh cookies định kỳ
- 🔄 Khi thấy lỗi bot detection → Cập nhật cookies mới ngay

### Hiệu Suất
- ✅ Cookies hợp lệ → Tỷ lệ thành công 95-98%
- ❌ Không có cookies → Tỷ lệ thành công 50-60%
- 🚀 Kết hợp cookies + bgutil POT provider → Tỷ lệ thành công 99%

---

## 🔍 Troubleshooting

### Vấn đề 1: Lỗi vẫn còn sau khi thêm cookies

**Nguyên nhân:**
- Cookies đã hết hạn ngay sau khi export
- Cookies bị lỗi khi encode/decode base64
- Chưa restart server sau khi thêm cookies

**Giải pháp:**
1. Kiểm tra cookies chưa hết hạn (đăng nhập lại YouTube)
2. Export lại cookies mới
3. Kiểm tra base64 encode đúng (không có xuống dòng)
4. Restart server Railway: Settings → Restart

### Vấn đề 2: Cookies bị reject sau vài ngày

**Nguyên nhân:**
- YouTube phát hiện cookies được dùng từ nhiều IP khác nhau
- Tài khoản bị đánh dấu đáng ngờ

**Giải pháp:**
- Dùng tài khoản phụ mới
- Export cookies từ cùng vị trí địa lý với server
- Xem xét dùng VPN cố định cho server

### Vấn đề 3: Base64 encode không đúng

**Triệu chứng:**
```
[WARNING] Failed to decode YOUTUBE_COOKIES: Invalid base64-encoded string
```

**Giải pháp:**
```bash
# Linux/Mac - Đảm bảo không có xuống dòng
base64 -w 0 cookies.txt | tr -d '\n' > cookies_base64.txt

# Windows PowerShell
$bytes = [IO.File]::ReadAllBytes("cookies.txt")
$base64 = [Convert]::ToBase64String($bytes)
$base64 | Out-File -Encoding ASCII -NoNewline cookies_base64.txt
```

### Vấn đề 4: Một số video vẫn bị lỗi

**Nguyên nhân:**
- Video có giới hạn vùng địa lý
- Video giới hạn độ tuổi (cần tài khoản đã xác minh)
- Video bị chặn bản quyền

**Giải pháp:**
- Dùng tài khoản đã xác minh tuổi khi export cookies
- Xem xét thêm VPN nếu nhiều video bị chặn vùng
- Một số video không thể tải do chính sách YouTube

---

## 📞 Hỗ Trợ

Nếu vẫn gặp vấn đề sau khi làm theo hướng dẫn:

1. Kiểm tra log server để xem lỗi cụ thể
2. Đảm bảo đã làm đúng các bước
3. Thử với video khác để xác định vấn đề
4. Liên hệ: duongminhtri9311@gmail.com

---

## 🎯 Checklist Nhanh

- [ ] Đã cài extension "Get cookies.txt LOCALLY"
- [ ] Đã đăng nhập YouTube và xem vài video
- [ ] Đã export cookies.txt từ youtube.com
- [ ] Đã encode cookies thành base64 (không có xuống dòng)
- [ ] Đã thêm biến YOUTUBE_COOKIES vào Railway
- [ ] Đã restart server Railway
- [ ] Đã kiểm tra log thấy "SUCCESS" message
- [ ] Đã test tải video thành công
- [ ] Đã xóa file cookies.txt local
- [ ] Đã đặt lịch nhắc refresh sau 1-2 tháng
