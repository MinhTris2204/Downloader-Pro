# Hướng dẫn Tự động Xóa Lịch sử Tải xuống

## Tổng quan

Hệ thống đã được cập nhật để tự động xóa lịch sử tải xuống cũ hơn 3 ngày nhằm:
- Giảm dung lượng database
- Tối ưu hiệu suất truy vấn
- Tuân thủ quy định bảo vệ dữ liệu cá nhân

## Các thay đổi đã thực hiện

### 1. Tự động cleanup trong ứng dụng
- File: `app.py`
- Chức năng: Thread chạy nền tự động xóa lịch sử sau 3 ngày
- Tần suất: Mỗi 24 giờ
- Bảng ảnh hưởng: `user_downloads`

### 2. Script cleanup thủ công
- File: `cleanup_download_history.py`
- Sử dụng: Chạy thủ công khi cần thiết
- Lệnh: `python cleanup_download_history.py`

### 3. Cập nhật thông báo giới hạn tải
- User free tải lần thứ 3 sẽ thấy: **"🚫 Bạn đã hết 2 lượt tải miễn phí trong tuần này. Vui lòng mua Premium để tải không giới hạn!"**
- Nút hành động: **"👑 Mua Premium - Tải không giới hạn"**

## Lưu ý quan trọng

### Số liệu thống kê KHÔNG bị ảnh hưởng
- Badge "🔥 8.013 lượt tải đã xử lý" vẫn giữ nguyên
- Bảng `downloads` (thống kê tổng) không bị xóa
- Chỉ xóa bảng `user_downloads` (tracking giới hạn user)

### Cấu trúc database
```sql
-- Bảng tracking giới hạn (SẼ BỊ XÓA sau 3 ngày)
user_downloads:
  - id
  - user_id
  - platform
  - download_time

-- Bảng thống kê tổng (KHÔNG BỊ XÓA)
downloads:
  - id
  - platform
  - format
  - quality
  - download_time
  - ip_address
  - country
  - ... (tracking chi tiết)
```

## Cách chạy thủ công

### Trên server production:
```bash
cd Downloader-Pro
python cleanup_download_history.py
```

### Thiết lập Cron Job (tùy chọn):
```bash
# Chạy mỗi ngày lúc 3:00 AM
0 3 * * * cd /path/to/Downloader-Pro && python cleanup_download_history.py >> /var/log/cleanup_history.log 2>&1
```

### Trên Railway/Heroku:
Không cần thiết lập cron vì app đã có thread tự động chạy nền.

## Kiểm tra hoạt động

### Xem log cleanup:
```bash
# Trong console app
[CLEANUP] Deleted 150 download history records older than 3 days
```

### Kiểm tra database:
```sql
-- Xem số lượng bản ghi
SELECT COUNT(*) FROM user_downloads;

-- Xem bản ghi cũ nhất
SELECT MIN(download_time) FROM user_downloads;

-- Xem bản ghi theo ngày
SELECT DATE(download_time), COUNT(*) 
FROM user_downloads 
GROUP BY DATE(download_time) 
ORDER BY DATE(download_time) DESC;
```

## Khôi phục nếu cần

Nếu cần giữ lịch sử lâu hơn, chỉnh sửa trong `app.py`:

```python
# Thay đổi từ 3 ngày sang 7 ngày
three_days_ago = datetime.now() - timedelta(days=7)
```

## Hỗ trợ

Nếu có vấn đề, kiểm tra:
1. Log server: `[CLEANUP]` messages
2. Database connection: `DATABASE_URL` environment variable
3. Thread status: Xem console khi app khởi động
