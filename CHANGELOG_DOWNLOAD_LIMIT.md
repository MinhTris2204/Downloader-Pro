# Changelog - Cập nhật Giới hạn Tải & Cleanup Lịch sử

## Ngày: 2026-03-09

### ✅ Các thay đổi đã thực hiện

#### 1. Tự động xóa lịch sử tải xuống sau 3 ngày
- **File thay đổi**: `app.py`
- **Chức năng mới**: Thread `cleanup_download_history()` chạy nền
- **Tần suất**: Mỗi 24 giờ
- **Mục đích**: Giảm dung lượng database, chỉ giữ lịch sử 3 ngày gần nhất
- **Bảng ảnh hưởng**: `user_downloads` (tracking giới hạn user)
- **Bảng KHÔNG ảnh hưởng**: `downloads` (thống kê tổng)

#### 2. Nút xóa thủ công trong Admin Dashboard
- **File thay đổi**: 
  - `templates/admin_dashboard.html` - Thêm nút "Xóa lịch sử cũ (>3 ngày)"
  - `static/js/admin-dashboard.js` - Thêm hàm `clearDownloadHistory()`
  - `app.py` - Thêm API endpoint `/api/admin/clear-download-history`

- **Vị trí**: Trang Admin Dashboard → Lịch sử tải xuống
- **Chức năng**: 
  - Xóa thủ công lịch sử tải xuống cũ hơn 3 ngày
  - Hiển thị số bản ghi đã xóa
  - Xác nhận trước khi xóa
  - Tự động reload bảng sau khi xóa

#### 3. Cập nhật thông báo giới hạn tải
- **File thay đổi**: 
  - `controllers/auth_controller.py`
  - `static/js/translations.js`

- **Thông báo mới**:
  - Tiếng Việt: "🚫 Bạn đã hết 2 lượt tải miễn phí trong tuần này. Vui lòng mua Premium để tải không giới hạn!"
  - English: "🚫 You have used all 2 free downloads this week. Please purchase Premium for unlimited downloads!"
  - Русский: "🚫 Вы использовали все 2 бесплатные загрузки на этой неделе. Пожалуйста, купите Premium для неограниченных загрузок!"

- **Nút hành động mới**:
  - Tiếng Việt: "👑 Mua Premium - Tải không giới hạn"
  - English: "👑 Purchase Premium - Unlimited Downloads"
  - Русский: "👑 Купить Premium - Неограниченные загрузки"

#### 3. Script cleanup thủ công
- **File mới**: `cleanup_download_history.py`
- **Sử dụng**: Chạy thủ công khi cần
- **Lệnh**: `python cleanup_download_history.py`

#### 4. Cập nhật thông báo giới hạn tải
- **File mới**: `CLEANUP_HISTORY_GUIDE.md`
- **Nội dung**: Hướng dẫn chi tiết về cleanup, cron job, kiểm tra

### 🎯 Cách sử dụng nút xóa thủ công

#### Trong Admin Dashboard:
1. Đăng nhập vào Admin Dashboard
2. Chọn menu "Lịch sử tải xuống"
3. Click nút **"🗑️ Xóa lịch sử cũ (>3 ngày)"**
4. Xác nhận trong popup
5. Hệ thống sẽ xóa và hiển thị số bản ghi đã xóa

#### Qua API:
```bash
curl -X POST http://localhost:5000/api/admin/clear-download-history \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

Response:
```json
{
  "success": true,
  "deleted_count": 150,
  "remaining_count": 45,
  "cutoff_date": "2026-03-06T10:30:00"
}
```

### 📊 Số liệu thống kê KHÔNG bị ảnh hưởng

Badge hiển thị trên trang chủ vẫn hoạt động bình thường:
```html
<div class="stats-badge" id="stats-badge">
    <span class="stats-icon">🔥</span>
    <span id="total-downloads">8.013</span> 
    <span>lượt tải đã xử lý</span>
</div>
```

- Số liệu lấy từ bảng `downloads` (không bị xóa)
- API endpoint: `/api/stats`
- Cập nhật real-time mỗi 3 giây

### 🔄 Luồng hoạt động

#### User Free (chưa đăng nhập):
1. Truy cập trang → Yêu cầu đăng nhập
2. Đăng ký miễn phí → Nhận 2 lượt tải/tuần
3. Tải lần 1 → OK
4. Tải lần 2 → OK
5. Tải lần 3 → **Hiển thị modal giới hạn với thông báo mới**

#### User Premium:
- Tải không giới hạn
- Không bị ảnh hưởng bởi cleanup

### 🗄️ Database Schema

```sql
-- Bảng tracking giới hạn (XÓA sau 3 ngày)
CREATE TABLE user_downloads (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    platform VARCHAR(20) NOT NULL,
    download_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index để tối ưu cleanup
CREATE INDEX idx_user_downloads_user_time 
ON user_downloads(user_id, download_time);

-- Bảng thống kê tổng (KHÔNG XÓA)
CREATE TABLE downloads (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(20),
    format VARCHAR(10),
    quality VARCHAR(20),
    download_time TIMESTAMP,
    ip_address VARCHAR(45),
    country VARCHAR(100),
    city VARCHAR(100),
    device_type VARCHAR(20),
    os VARCHAR(50),
    browser VARCHAR(50),
    is_mobile BOOLEAN,
    is_tablet BOOLEAN,
    is_pc BOOLEAN,
    success BOOLEAN,
    user_id INTEGER
);
```

### 🚀 Deployment

#### Trên Railway/Heroku:
1. Push code lên repository
2. Deploy tự động
3. Thread cleanup sẽ tự động chạy khi app khởi động
4. Không cần cấu hình thêm

#### Kiểm tra hoạt động:
```bash
# Xem log
[INFO] Cleanup threads started - Files: 30min, Download history: 3 days
[CLEANUP] Deleted 150 download history records older than 3 days
```

### 📝 Testing Checklist

- [x] Thread cleanup khởi động thành công
- [x] Xóa bản ghi cũ hơn 3 ngày
- [x] Giữ nguyên bản ghi mới hơn 3 ngày
- [x] Thống kê tổng không bị ảnh hưởng
- [x] Thông báo giới hạn hiển thị đúng
- [x] Nút "Mua Premium" hoạt động
- [x] Script thủ công chạy được
- [x] Đa ngôn ngữ (vi, en, ru)
- [x] Nút xóa thủ công trong Admin Dashboard
- [x] API endpoint `/api/admin/clear-download-history`
- [x] Xác nhận trước khi xóa
- [x] Hiển thị số bản ghi đã xóa

### 🔧 Maintenance

#### Chạy cleanup thủ công:

**Cách 1: Qua Admin Dashboard (Khuyến nghị)**
1. Truy cập `/admin/dashboard`
2. Chọn "Lịch sử tải xuống"
3. Click nút "Xóa lịch sử cũ (>3 ngày)"

**Cách 2: Qua script Python**
```bash
python cleanup_download_history.py
```

**Cách 3: Qua API**
```bash
curl -X POST http://localhost:5000/api/admin/clear-download-history
```

#### Thay đổi thời gian giữ lịch sử:
Chỉnh sửa trong `app.py`:
```python
# Từ 3 ngày sang 7 ngày
three_days_ago = datetime.now() - timedelta(days=7)
```

#### Tắt auto cleanup:
Comment dòng trong `app.py`:
```python
# threading.Thread(target=cleanup_download_history, daemon=True).start()
```

### 📞 Support

Nếu có vấn đề:
1. Kiểm tra log server
2. Verify DATABASE_URL environment variable
3. Test script thủ công: `python cleanup_download_history.py`
4. Kiểm tra database: `SELECT COUNT(*) FROM user_downloads;`

---

**Tác giả**: Kiro AI Assistant  
**Ngày**: 2026-03-09  
**Version**: 1.0.0
