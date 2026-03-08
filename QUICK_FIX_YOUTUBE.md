# 🚨 SỬA LỖI YOUTUBE NHANH - DÀNH CHO ADMIN

## Triệu Chứng
```
ERROR: Sign in to confirm you're not a bot
```
- Tất cả video YouTube đều báo lỗi
- Người dùng không tải được YouTube

## Nguyên Nhân
**Cookies YouTube đã HẾT HẠN** (thường sau 1-2 tháng)

## Giải Pháp Nhanh (5 phút)

### Bước 1: Export Cookies Mới
1. Mở Chrome/Edge
2. Cài extension: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
3. Đăng nhập https://www.youtube.com (dùng tài khoản phụ)
4. Xem 1-2 video
5. Click icon extension → Export → Lưu `cookies.txt`

### Bước 2: Encode Base64

**Linux/Mac:**
```bash
base64 -w 0 cookies.txt > cookies_base64.txt
```

**Windows PowerShell:**
```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("cookies.txt")) | Out-File -Encoding ASCII cookies_base64.txt
```

### Bước 3: Cập Nhật Railway
1. Mở file `cookies_base64.txt`
2. Copy toàn bộ nội dung (1 dòng dài)
3. Vào Railway → Project → Variables
4. Tìm biến `YOUTUBE_COOKIES`
5. Paste nội dung mới → Save
6. Railway tự động restart

### Bước 4: Kiểm Tra
- Đợi 1-2 phút server restart
- Vào website thử tải 1 video YouTube
- Nếu thành công → Xong! ✅

## Kiểm Tra Log

Vào Railway → Deployments → View Logs, tìm:

✅ **Thành công:**
```
[SUCCESS] YouTube cookies loaded from environment variable (4578 bytes)
```

❌ **Thất bại:**
```
[WARNING] No YouTube auth configured!
```

## Lưu Ý
- Cookies hết hạn sau 1-2 tháng → Đặt lịch nhắc
- Dùng tài khoản YouTube phụ, không dùng tài khoản chính
- Xóa file `cookies.txt` local sau khi upload

## Hướng Dẫn Chi Tiết
Xem file: `YOUTUBE_COOKIES_SETUP.md`

## Liên Hệ
Email: duongminhtri9311@gmail.com
