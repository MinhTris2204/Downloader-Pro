# 📊 Hướng Dẫn Tracking Người Dùng

## Tính Năng

Hệ thống tracking tự động thu thập thông tin khi người dùng tải video/audio:

### Thông tin được lưu:
- ✅ **Vị trí địa lý**: Quốc gia, thành phố, múi giờ, tọa độ
- ✅ **Thiết bị**: Loại thiết bị (Mobile/Tablet/PC)
- ✅ **Hệ điều hành**: Windows, macOS, iOS, Android, Linux...
- ✅ **Trình duyệt**: Chrome, Safari, Firefox, Edge...
- ✅ **IP Address**: Địa chỉ IP của người dùng
- ✅ **User Agent**: Thông tin chi tiết về trình duyệt

## Cài Đặt

### 1. Cài đặt thư viện mới

```bash
pip install -r requirements.txt
```

Thư viện mới được thêm:
- `user-agents>=2.2.0` - Phân tích User-Agent

### 2. Migration Database (Nếu đã có database cũ)

Nếu bạn đã có database từ trước, chạy script migration:

```bash
python migrate_tracking.py
```

Script này sẽ thêm các cột tracking vào bảng `downloads` hiện có.

### 3. Khởi động lại ứng dụng

```bash
python app.py
```

## Sử Dụng

### Xem Thống Kê Tracking

Truy cập trang admin:
```
https://your-domain.com/admin/tracking
```

Trang này hiển thị:
- 📱 Số lượng download theo thiết bị (Mobile/PC/Tablet)
- 🌍 Top 10 quốc gia
- 🏙️ Top 10 thành phố
- 🌐 Top 10 trình duyệt

### API Endpoint

Lấy dữ liệu tracking qua API:

```bash
GET /api/stats/tracking
```

Response:
```json
{
  "top_countries": [
    {"country": "Vietnam", "code": "VN", "count": 1250}
  ],
  "devices": {
    "mobile": 850,
    "pc": 350,
    "tablet": 50
  },
  "top_cities": [
    {"city": "Ho Chi Minh City", "country": "Vietnam", "count": 500}
  ],
  "top_browsers": [
    {"browser": "Chrome 120.0", "count": 800}
  ]
}
```

## Cấu Trúc Database

### Bảng `downloads` (đã cập nhật)

```sql
CREATE TABLE downloads (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(20) NOT NULL,
    format VARCHAR(10) NOT NULL,
    quality VARCHAR(20),
    download_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT TRUE,
    
    -- Tracking columns (mới)
    ip_address VARCHAR(45),
    country VARCHAR(100),
    country_code VARCHAR(5),
    region VARCHAR(100),
    city VARCHAR(100),
    timezone VARCHAR(50),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    device_type VARCHAR(50),
    os VARCHAR(100),
    browser VARCHAR(100),
    is_mobile BOOLEAN,
    is_tablet BOOLEAN,
    is_pc BOOLEAN,
    user_agent TEXT
);
```

## API Geolocation

Hệ thống sử dụng **ip-api.com** (miễn phí) để tra cứu vị trí từ IP:
- Giới hạn: 45 requests/phút
- Không cần API key
- Độ chính xác: Quốc gia/Thành phố

### Lưu ý:
- IP nội bộ (127.x.x.x, 192.168.x.x) sẽ được ghi là "Unknown"
- Nếu API geolocation lỗi, vẫn lưu thông tin thiết bị

## Bảo Mật & Privacy

⚠️ **Quan trọng:**
- Dữ liệu IP và vị trí là thông tin nhạy cảm
- Tuân thủ GDPR/CCPA nếu có người dùng từ EU/California
- Cân nhắc thêm Privacy Policy
- Có thể hash IP trước khi lưu để bảo vệ privacy

### Ẩn danh hóa IP (Tùy chọn)

Thêm vào `utils/tracking.py`:

```python
import hashlib

def anonymize_ip(ip):
    """Hash IP để bảo vệ privacy"""
    return hashlib.sha256(ip.encode()).hexdigest()[:16]
```

## Troubleshooting

### Lỗi: "Module 'user_agents' not found"
```bash
pip install user-agents
```

### Lỗi: "Column already exists"
Bạn đã chạy migration rồi, bỏ qua lỗi này.

### Tracking không hoạt động
1. Kiểm tra DATABASE_URL đã được set
2. Kiểm tra bảng downloads có các cột tracking
3. Xem log server khi download file

## Tính Năng Tương Lai

- [ ] Dashboard analytics với biểu đồ
- [ ] Export dữ liệu ra CSV/Excel
- [ ] Real-time tracking với WebSocket
- [ ] Heatmap vị trí người dùng
- [ ] A/B testing tracking
- [ ] Retention analysis

## Liên Hệ

Nếu có vấn đề, tạo issue trên GitHub hoặc liên hệ admin.
