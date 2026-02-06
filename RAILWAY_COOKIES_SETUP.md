# 🍪 Hướng dẫn Setup YouTube Cookies cho Railway

## Tại sao cần Cookies?

Khi chạy trên Railway hoặc các cloud platform, YouTube dễ dàng phát hiện và chặn bot vì:
- IP của data center dễ bị nhận diện
- Nhiều người dùng chung IP
- Không có session/cookies như browser thật

**Cookies giúp bypass hoàn toàn** bằng cách giả lập session từ một tài khoản Google thật.

---

## 📋 Bước 1: Export Cookies từ Browser

### Chrome:
1. Cài extension: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. Đăng nhập YouTube bằng tài khoản Google
3. Mở YouTube.com
4. Click icon extension → "Export" → Lưu thành `cookies.txt`

### Firefox:
1. Cài extension: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
2. Đăng nhập YouTube
3. Mở YouTube.com
4. Click icon extension → Lưu thành `cookies.txt`

---

## 📋 Bước 2: Chuyển đổi sang Base64

### Windows (PowerShell):
```powershell
[Convert]::ToBase64String([System.IO.File]::ReadAllBytes("cookies.txt")) | Out-File -Encoding ASCII cookies_base64.txt
```

### Linux/Mac:
```bash
base64 -w 0 cookies.txt > cookies_base64.txt
```

---

## 📋 Bước 3: Thêm vào Railway

1. Mở Railway Dashboard
2. Chọn project của bạn
3. Vào tab **Variables**
4. Thêm biến mới:
   - **Name**: `YOUTUBE_COOKIES`
   - **Value**: Paste nội dung từ file `cookies_base64.txt`
5. Click **Deploy** để restart

---

## ✅ Kiểm tra

Sau khi deploy, kiểm tra logs Railway, bạn sẽ thấy:
```
[SUCCESS] YouTube cookies loaded from environment variable (XXXX bytes)
```

---

## ⚠️ Lưu ý Bảo mật

1. **Sử dụng tài khoản phụ** - Không dùng tài khoản Google chính
2. **Cookies có thể hết hạn** - Cập nhật lại sau 1-2 tuần nếu bị lỗi
3. **Không chia sẻ cookies** - Cookies = mật khẩu tạm thời
4. **Railway Variables an toàn** - Được mã hóa và không hiển thị trong logs

---

## 🔧 Troubleshooting

### Lỗi "Failed to decode YOUTUBE_COOKIES"
- Kiểm tra lại base64 encoding
- Đảm bảo không có ký tự xuống dòng thừa

### Lỗi "Sign in to confirm you're not a bot" vẫn xuất hiện
- Cookies có thể đã hết hạn → Export lại
- Tài khoản có thể bị YouTube flag → Thử tài khoản khác
- Thử xem vài video trên YouTube trước khi export cookies

### Video vẫn không tải được
- Một số video có DRM không thể tải
- Video riêng tư/xóa/chặn khu vực không thể tải
- Thử video khác để xác nhận hệ thống hoạt động

---

## 📞 Hỗ trợ

Nếu vẫn gặp vấn đề, hãy kiểm tra:
1. Logs trên Railway để xem chi tiết lỗi
2. Cập nhật yt-dlp: Redeploy để Railway tải version mới nhất
3. Thử video ngắn từ kênh phổ biến để test
