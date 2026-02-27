# Premium Download Limit Feature

## Tính năng mới

Hệ thống giới hạn tải xuống với tùy chọn nâng cấp Premium đã được thêm vào website.

### Cơ chế hoạt động

1. **Người dùng miễn phí**: 2 lượt tải/tuần
2. **Người dùng Premium**: Không giới hạn trong 30 ngày

### Các file đã thêm/sửa đổi

#### Files mới:
- `utils/download_limit.py` - Logic quản lý giới hạn và premium
- `static/js/download-limit.js` - UI modal và xử lý frontend
- `migrate_premium_tables.py` - Script migration database

#### Files đã sửa:
- `app.py` - Thêm API endpoints và kiểm tra giới hạn
- `controllers/donate_controller.py` - Xử lý thanh toán premium
- `static/js/app.js` - Xử lý lỗi limit exceeded
- `static/js/translations.js` - Thêm text đa ngôn ngữ
- `static/css/style.css` - Thêm styles cho modal
- `templates/index.html` - Thêm script và status badge

### Database Schema

#### Bảng `user_downloads`
```sql
CREATE TABLE user_downloads (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    platform VARCHAR(20) NOT NULL,
    download_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_user_downloads_user_time ON user_downloads(user_id, download_time);
```

#### Bảng `premium_users`
```sql
CREATE TABLE premium_users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    order_code VARCHAR(50) NOT NULL,
    amount INTEGER NOT NULL,
    activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    UNIQUE(user_id, order_code)
);
CREATE INDEX idx_premium_users_user_expires ON premium_users(user_id, expires_at);
```

### Cách chạy Migration

```bash
python migrate_premium_tables.py
```

### API Endpoints mới

1. **GET /api/user/status**
   - Lấy thông tin trạng thái người dùng
   - Response: `{can_download, remaining_downloads, is_premium, premium_expires}`

2. **POST /api/donate/create** (đã cập nhật)
   - Thêm params: `is_premium`, `user_id`
   - Tạo payment link cho premium

### Luồng hoạt động

1. User nhấn "Tải xuống"
2. Backend kiểm tra `check_download_limit()`
3. Nếu hết lượt:
   - Trả về HTTP 403 với `error: 'limit_exceeded'`
   - Frontend hiển thị modal premium
4. User chọn số tiền và thanh toán
5. Sau khi thanh toán thành công:
   - `activate_premium()` được gọi
   - User có quyền premium 30 ngày
6. Mỗi lần tải thành công:
   - `record_user_download()` ghi nhận
   - Frontend cập nhật số lượt còn lại

### User Identification

User được nhận diện qua hash của `IP + User-Agent`:
```python
identifier = hashlib.sha256(f"{ip}:{user_agent}".encode()).hexdigest()
```

### Đa ngôn ngữ

Modal hỗ trợ 3 ngôn ngữ:
- Tiếng Việt (vi)
- English (en)
- Русский (ru)

### Tùy chỉnh

Để thay đổi giới hạn, sửa trong `utils/download_limit.py`:
```python
FREE_DOWNLOADS_PER_WEEK = 2  # Số lượt miễn phí
PREMIUM_DURATION_DAYS = 30   # Thời hạn premium
```

### Testing

1. Tải 2 video để hết lượt miễn phí
2. Lần thứ 3 sẽ hiện modal premium
3. Thanh toán thử nghiệm (nếu có PayOS sandbox)
4. Sau thanh toán, kiểm tra tải không giới hạn

### Notes

- User được track theo IP + User-Agent (không cần đăng nhập)
- Premium tự động hết hạn sau 30 ngày
- Lượt miễn phí reset sau 7 ngày
- Số tiền tối thiểu: 10,000 VNĐ
