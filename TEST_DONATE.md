# Test Donate Feature

## Các file đã tạo:

### Backend:
1. `config/payos_config.py` - Cấu hình PayOS từ environment variables
2. `utils/payos_helper.py` - Helper class xử lý PayOS API
3. `controllers/donate_controller.py` - Controller xử lý donate routes

### Frontend:
1. `templates/donate.html` - Trang donate với form đẹp
2. `templates/donate_result.html` - Trang kết quả thanh toán
3. `static/css/style.css` - Thêm styles cho nút donate (màu đỏ, glow effect)
4. `templates/layouts/base.html` - Thêm nút "☕ Ủng hộ" vào header

### Documentation:
1. `PAYOS_SETUP_GUIDE.md` - Hướng dẫn cấu hình chi tiết

## Test Steps:

### 1. Test Local (Không có PayOS credentials):
```bash
python app.py
```
- Truy cập: http://localhost:5000
- Kiểm tra nút "☕ Ủng hộ" ở header (màu đỏ, hiệu ứng glow)
- Click vào nút → Chuyển đến /donate
- Kiểm tra giao diện form donate
- Thử submit form → Sẽ báo lỗi vì chưa có credentials (expected)

### 2. Test với PayOS credentials:

#### Thêm vào `.env`:
```bash
PAYOS_CLIENT_ID=your_client_id
PAYOS_API_KEY=your_api_key
PAYOS_CHECKSUM_KEY=your_checksum_key
```

#### Test flow:
1. Truy cập /donate
2. Chọn số tiền (ví dụ: 10,000đ)
3. Nhập tên: "Test User"
4. Nhập email: "test@example.com"
5. Nhập lời nhắn: "Test donation"
6. Click "💝 Ủng hộ ngay"
7. Kiểm tra:
   - Button chuyển sang "⏳ Đang xử lý..."
   - Redirect đến PayOS checkout page
   - Có QR code để scan
   - Có thông tin đơn hàng

#### Test thanh toán:
- **Thành công**: Quay về /payos/return → Hiển thị trang cảm ơn
- **Hủy**: Quay về /payos/cancel → Hiển thị trang hủy

### 3. Test trên Railway:

#### Deploy:
```bash
git add .
git commit -m "Add PayOS donate feature"
git push
```

#### Thêm Environment Variables trên Railway:
```
PAYOS_CLIENT_ID=xxx
PAYOS_API_KEY=xxx
PAYOS_CHECKSUM_KEY=xxx
```

#### Test:
1. Truy cập: https://your-app.railway.app
2. Click nút "☕ Ủng hộ"
3. Test toàn bộ flow như local

### 4. Test Webhook (Optional):

#### Cấu hình trên PayOS Dashboard:
- URL: https://your-app.railway.app/payos/webhook
- Event: Payment Success

#### Test:
1. Thực hiện donation thành công
2. Kiểm tra logs trên Railway
3. Xem webhook data được log ra

## Expected Results:

### UI/UX:
- ✅ Nút donate nổi bật ở header (màu đỏ, hiệu ứng pulse)
- ✅ Form donate đẹp, dễ sử dụng
- ✅ Responsive trên mobile
- ✅ Loading state khi submit
- ✅ Trang kết quả rõ ràng (success/cancel)

### Functionality:
- ✅ Tạo payment link thành công
- ✅ Redirect đến PayOS checkout
- ✅ Return URL hoạt động
- ✅ Cancel URL hoạt động
- ✅ Webhook nhận được data (nếu cấu hình)

### Security:
- ✅ Signature verification
- ✅ HTTPS redirect
- ✅ Input validation (min 1,000đ)
- ✅ No sensitive data in frontend

## Troubleshooting:

### Lỗi "No credentials":
- Kiểm tra environment variables
- Restart server sau khi thêm env vars

### Lỗi "Invalid signature":
- Kiểm tra PAYOS_CHECKSUM_KEY
- Đảm bảo không có khoảng trắng

### Lỗi "API_ERROR":
- Kiểm tra PAYOS_CLIENT_ID và PAYOS_API_KEY
- Kiểm tra network/firewall

### Nút donate không hiển thị:
- Clear browser cache
- Kiểm tra CSS đã load

## Notes:

- Số tiền tối thiểu: 1,000 VNĐ
- PayOS hỗ trợ: Banking QR, MoMo, ZaloPay, etc.
- Không cần cài thêm dependencies (đã có requests trong requirements.txt)
- Webhook là optional, không bắt buộc

---

**Ready to deploy! 🚀**
