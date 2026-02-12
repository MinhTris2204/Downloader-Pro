# 💬 Tính năng Lời nhắn Donation

## Tổng quan

Sau khi donate thành công, người dùng có thể để lại lời nhắn (1 lần duy nhất cho mỗi đơn hàng). Lời nhắn sẽ được hiển thị trên trang chủ.

## Tính năng

### 1. Form lời nhắn (sau khi donate thành công)
- Hiển thị trên trang `/payos/return` (khi thanh toán thành công)
- Người dùng nhập:
  - Tên (tùy chọn, mặc định "Anonymous")
  - Lời nhắn (bắt buộc, tối đa 500 ký tự)
- Có character counter
- Chỉ cho phép post 1 lần duy nhất cho mỗi order_code
- Session-based security

### 2. Widget hiển thị lời nhắn (trang chủ)
- Vị trí: Cuối trang chủ, trước footer
- Thiết kế: Gradient đẹp (purple-blue), glass effect
- Hiển thị 10 lời nhắn mới nhất
- Auto-scroll nếu nhiều messages
- Responsive trên mobile
- Real-time relative time ("5 phút trước", "2 giờ trước", etc.)

### 3. Database
Bảng mới: `donation_messages`
```sql
CREATE TABLE donation_messages (
    id SERIAL PRIMARY KEY,
    order_code VARCHAR(50) UNIQUE NOT NULL,
    donor_name VARCHAR(100) DEFAULT 'Anonymous',
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_approved BOOLEAN DEFAULT TRUE
);
```

## API Endpoints

### POST /api/donate/message
Lưu lời nhắn sau khi donate

Request:
```json
{
  "order_code": "1234567890",
  "donor_name": "Nguyễn Văn A",
  "message": "Cảm ơn bạn đã tạo công cụ hữu ích!"
}
```

Response (Success):
```json
{
  "success": true,
  "message": "Cảm ơn bạn đã chia sẻ!"
}
```

Response (Error):
```json
{
  "success": false,
  "error": "Bạn đã gửi lời nhắn cho đơn hàng này rồi"
}
```

### GET /api/donate/messages?limit=10
Lấy danh sách lời nhắn

Response:
```json
{
  "success": true,
  "messages": [
    {
      "donor_name": "Nguyễn Văn A",
      "message": "Cảm ơn bạn!",
      "created_at": "2026-02-12T10:30:00"
    }
  ]
}
```

## Security

### Session-based validation
- Khi thanh toán thành công, lưu `order_code` vào session
- Khi post message, kiểm tra session có khớp không
- Sau khi post thành công, xóa khỏi session

### Database constraints
- `order_code` là UNIQUE → Mỗi đơn hàng chỉ post được 1 lần
- Check duplicate trước khi insert

### Input validation
- Tên: Tối đa 100 ký tự
- Message: 1-500 ký tự (bắt buộc)
- XSS protection: Escape HTML khi hiển thị

## Files đã tạo/sửa

### Mới:
```
templates/components/donation_messages.html  # Widget hiển thị
migrate_donation_messages.py                 # Migration script
DONATION_MESSAGES_FEATURE.md                 # Documentation này
```

### Đã sửa:
```
app.py                              # Thêm table creation
controllers/donate_controller.py    # Thêm 2 endpoints mới
templates/donate_result.html        # Thêm form lời nhắn
templates/index.html                # Include widget
```

## Migration

### Nếu app đã deploy:
```bash
# Local
python migrate_donation_messages.py

# Railway
# Table sẽ tự động tạo khi app restart (có trong init_db())
```

### Nếu app mới:
- Không cần làm gì, table tự động tạo khi khởi động

## Test

### 1. Test flow donate + message:
1. Truy cập `/donate`
2. Donate với số tiền bất kỳ
3. Thanh toán thành công → Redirect về `/payos/return`
4. Thấy form "💬 Để lại lời nhắn của bạn"
5. Nhập tên và lời nhắn
6. Click "📤 Gửi lời nhắn"
7. Thấy "🎉 Lời nhắn của bạn đã được gửi thành công!"

### 2. Test hiển thị trên trang chủ:
1. Truy cập `/`
2. Scroll xuống cuối trang
3. Thấy widget "💝 Lời nhắn từ những người ủng hộ"
4. Thấy lời nhắn vừa gửi hiển thị

### 3. Test duplicate prevention:
1. Sau khi gửi lời nhắn thành công
2. Refresh trang `/payos/return?orderCode=xxx`
3. Thử gửi lại → Báo lỗi "Bạn đã gửi lời nhắn cho đơn hàng này rồi"

### 4. Test validation:
- Message rỗng → Báo lỗi
- Message > 500 ký tự → Báo lỗi
- Tên > 100 ký tự → Tự động cắt hoặc báo lỗi

## UI/UX

### Desktop:
- Widget full width, gradient background
- Messages hiển thị dạng cards
- Hover effect trên cards
- Smooth scroll

### Mobile:
- Responsive layout
- Touch-friendly
- Cards stack vertically
- Smaller font sizes

## Moderation (Tùy chọn)

Hiện tại: `is_approved = TRUE` (auto-approve)

Nếu muốn moderate:
1. Set `is_approved = FALSE` mặc định
2. Tạo admin panel để approve/reject
3. Chỉ hiển thị messages có `is_approved = TRUE`

## Analytics (Tùy chọn)

Có thể thêm tracking:
- Số lượng messages per day
- Top donors (by message count)
- Average message length
- Most active times

## Lưu ý

- Messages không thể edit sau khi gửi
- Messages không thể delete (chỉ admin có thể)
- Không có reply/comment feature
- Không có like/reaction feature
- Simple & clean design

## Future enhancements

- [ ] Admin panel để moderate messages
- [ ] Report spam feature
- [ ] Pagination cho widget (load more)
- [ ] Filter by date range
- [ ] Search messages
- [ ] Export messages to CSV

---

**Feature hoàn chỉnh và sẵn sàng sử dụng! 🎉**
