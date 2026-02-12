# ☕ Tính năng Donate qua PayOS

## Tổng quan

Đã tích hợp tính năng donate/ủng hộ qua PayOS vào website. Người dùng có thể ủng hộ bằng QR Banking hoặc Ví điện tử.

## Tính năng chính

### 1. Nút Donate nổi bật
- Vị trí: Đầu tiên trong header navigation
- Màu sắc: Gradient đỏ (#ff6b6b → #ee5a6f)
- Hiệu ứng: Pulse glow animation, hover effect
- Text: "☕ Ủng hộ"

### 2. Trang Donate (/donate)
- Form đẹp, dễ sử dụng
- Chọn số tiền: 10k, 20k, 50k, 100k, 200k hoặc tùy chỉnh
- Thông tin tùy chọn: Tên, Email, Lời nhắn
- Validation: Số tiền tối thiểu 1,000đ
- Loading state khi xử lý

### 3. Thanh toán
- Redirect đến PayOS checkout page
- Hỗ trợ: QR Banking, MoMo, ZaloPay, etc.
- Bảo mật: Signature verification
- Return URL: /payos/return (thành công)
- Cancel URL: /payos/cancel (hủy)

### 4. Trang kết quả
- Thành công: Hiển thị lời cảm ơn + mã đơn hàng
- Hủy: Hiển thị thông báo + nút thử lại
- Nút về trang chủ

## Cấu hình

### Environment Variables (Railway):
```bash
PAYOS_CLIENT_ID=your_client_id
PAYOS_API_KEY=your_api_key
PAYOS_CHECKSUM_KEY=your_checksum_key
```

### Lấy credentials:
1. Đăng ký tại: https://my.payos.vn
2. Vào Dashboard → API Keys
3. Copy 3 thông tin trên

## Files đã tạo

```
config/
  ├── __init__.py
  └── payos_config.py          # Cấu hình PayOS

controllers/
  ├── __init__.py
  └── donate_controller.py     # Routes donate

utils/
  └── payos_helper.py          # PayOS API helper

templates/
  ├── donate.html              # Trang donate
  └── donate_result.html       # Trang kết quả

static/css/
  └── style.css                # Thêm donate button styles

static/js/
  └── translations.js          # Thêm translation cho donate

app.py                         # Đã register donate_bp
```

## API Endpoints

```
GET  /donate                   # Trang donate
POST /api/donate/create        # Tạo payment link
GET  /payos/return            # Return URL (success)
GET  /payos/cancel            # Cancel URL
POST /payos/webhook           # Webhook (optional)
```

## Test

### Local:
```bash
# Thêm vào .env
PAYOS_CLIENT_ID=xxx
PAYOS_API_KEY=xxx
PAYOS_CHECKSUM_KEY=xxx

# Run
python app.py

# Truy cập
http://localhost:5000/donate
```

### Production:
1. Deploy lên Railway
2. Thêm environment variables
3. Test tại: https://your-app.railway.app/donate

## Bảo mật

- ✅ Signature verification cho mọi request
- ✅ HTTPS bắt buộc
- ✅ Input validation
- ✅ Không lưu thông tin thẻ
- ✅ Webhook signature verification

## Responsive

- ✅ Desktop: Form 2 cột, nút lớn
- ✅ Mobile: Form 1 cột, touch-friendly
- ✅ Tablet: Tự động điều chỉnh

## Đa ngôn ngữ

Hỗ trợ 3 ngôn ngữ:
- 🇻🇳 Tiếng Việt: "☕ Ủng hộ"
- 🇺🇸 English: "☕ Donate"
- 🇷🇺 Русский: "☕ Поддержать"

## Lưu ý

- Phí giao dịch: Tham khảo PayOS Dashboard
- Số tiền tối thiểu: 1,000 VNĐ
- Webhook là optional
- Không cần cài thêm dependencies

## Support

- PayOS Docs: https://payos.vn/docs
- PayOS Support: support@payos.vn

---

**Sẵn sàng deploy! 🚀**
