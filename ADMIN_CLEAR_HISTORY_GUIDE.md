# Hướng dẫn Xóa Lịch sử Tải xuống Thủ công

## Tổng quan

Trang Admin Dashboard đã được thêm nút **"Xóa lịch sử cũ (>3 ngày)"** để admin có thể xóa thủ công lịch sử tải xuống cũ khi cần thiết.

## Cách sử dụng

### Bước 1: Truy cập Admin Dashboard
1. Đăng nhập vào `/admin/login`
2. Nhập username và password admin
3. Chuyển đến trang Dashboard

### Bước 2: Mở trang Lịch sử tải xuống
1. Click vào menu **"Lịch sử tải"** bên trái
2. Trang sẽ hiển thị danh sách các lượt tải gần đây

### Bước 3: Xóa lịch sử cũ
1. Click nút **"🗑️ Xóa lịch sử cũ (>3 ngày)"** ở góc trên bên phải
2. Popup xác nhận sẽ hiện ra:
   ```
   ⚠️ Bạn có chắc muốn xóa lịch sử tải xuống cũ hơn 3 ngày?
   
   Thao tác này không thể hoàn tác!
   ```
3. Click **OK** để xác nhận
4. Hệ thống sẽ xóa và hiển thị thông báo:
   ```
   ✅ Đã xóa thành công 150 bản ghi lịch sử tải xuống cũ hơn 3 ngày!
   ```
5. Bảng lịch sử sẽ tự động reload

## Giao diện

```
┌─────────────────────────────────────────────────────────┐
│  Lịch sử tải xuống                                      │
│  [🔄 Làm mới]  [🗑️ Xóa lịch sử cũ (>3 ngày)]          │
├─────────────────────────────────────────────────────────┤
│  Hiển thị: [50 gần nhất ▼]                             │
├─────────────────────────────────────────────────────────┤
│  Thời gian    │ Tài khoản │ Platform │ Format │ ...    │
│  09/03 10:30  │ user123   │ YOUTUBE  │ mp4    │ ...    │
│  09/03 10:25  │ user456   │ TIKTOK   │ mp3    │ ...    │
│  ...                                                     │
└─────────────────────────────────────────────────────────┘
```

## Khi nào nên xóa thủ công?

### Nên xóa khi:
- Database đầy, cần giải phóng dung lượng ngay
- Muốn xóa dữ liệu trước khi backup
- Kiểm tra xem cleanup tự động có hoạt động không
- Sau khi thay đổi cấu hình database

### Không cần xóa khi:
- Hệ thống đang chạy bình thường
- Thread tự động cleanup đang hoạt động (chạy mỗi 24h)
- Database còn nhiều dung lượng

## API Endpoint

### Request
```http
POST /api/admin/clear-download-history
Content-Type: application/json
Cookie: session=YOUR_SESSION_COOKIE
```

### Response Success
```json
{
  "success": true,
  "deleted_count": 150,
  "remaining_count": 45,
  "cutoff_date": "2026-03-06T10:30:00"
}
```

### Response Error
```json
{
  "success": false,
  "error": "Database not available"
}
```

## Kiểm tra kết quả

### Trong Admin Dashboard:
- Xem số bản ghi đã xóa trong popup thông báo
- Reload trang để xem danh sách mới

### Trong Database:
```sql
-- Xem số lượng bản ghi còn lại
SELECT COUNT(*) FROM user_downloads;

-- Xem bản ghi cũ nhất
SELECT MIN(download_time) FROM user_downloads;

-- Xem phân bố theo ngày
SELECT DATE(download_time), COUNT(*) 
FROM user_downloads 
GROUP BY DATE(download_time) 
ORDER BY DATE(download_time) DESC;
```

### Trong Log:
```
[ADMIN] Manually cleared 150 download history records older than 3 days
```

## Lưu ý quan trọng

### ⚠️ Cảnh báo
- Thao tác này **KHÔNG THỂ HOÀN TÁC**
- Chỉ xóa bảng `user_downloads` (tracking giới hạn)
- **KHÔNG** xóa bảng `downloads` (thống kê tổng)
- Badge "🔥 X lượt tải đã xử lý" vẫn giữ nguyên

### ✅ An toàn
- Chỉ xóa bản ghi cũ hơn 3 ngày
- Không ảnh hưởng đến user đang hoạt động
- Không ảnh hưởng đến thống kê tổng
- Có xác nhận trước khi xóa

## Troubleshooting

### Lỗi: "Unauthorized"
- Kiểm tra đã đăng nhập admin chưa
- Session có thể đã hết hạn, đăng nhập lại

### Lỗi: "Database not available"
- Kiểm tra DATABASE_URL environment variable
- Kiểm tra kết nối database
- Xem log server để biết chi tiết

### Nút không hoạt động
- Kiểm tra console browser (F12) xem có lỗi JavaScript
- Xóa cache browser và reload
- Kiểm tra file `admin-dashboard.js` đã load chưa

### Không xóa được bản ghi
- Kiểm tra có bản ghi cũ hơn 3 ngày không
- Xem log server để biết lỗi cụ thể
- Thử chạy script Python: `python cleanup_download_history.py`

## So sánh các phương pháp cleanup

| Phương pháp | Tự động | Thủ công | Tần suất | Khi nào dùng |
|-------------|---------|----------|----------|--------------|
| Thread tự động | ✅ | ❌ | 24h | Chạy nền, không cần can thiệp |
| Nút Admin Dashboard | ❌ | ✅ | Khi cần | Cần xóa ngay, kiểm tra |
| Script Python | ❌ | ✅ | Khi cần | Chạy từ terminal, cron job |
| API Endpoint | ❌ | ✅ | Khi cần | Tích hợp với hệ thống khác |

## Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra log server
2. Kiểm tra console browser (F12)
3. Thử phương pháp khác (script Python hoặc API)
4. Kiểm tra database connection

---

**Cập nhật**: 2026-03-09  
**Version**: 1.0.0
