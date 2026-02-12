# Hướng dẫn cấu hình PayOS Donate

## 1. Đăng ký tài khoản PayOS

1. Truy cập: https://my.payos.vn
2. Đăng ký tài khoản doanh nghiệp/cá nhân
3. Hoàn tất xác thực KYC

## 2. Lấy thông tin API

Sau khi đăng nhập vào PayOS Dashboard:

1. Vào mục **Cài đặt** → **API Keys**
2. Lấy 3 thông tin sau:
   - **Client ID**: Mã định danh ứng dụng
   - **API Key**: Khóa API để gọi API
   - **Checksum Key**: Khóa để tạo chữ ký bảo mật

## 3. Cấu hình trên Railway

### Thêm Environment Variables

Vào Railway Dashboard → Project → Variables, thêm 3 biến sau:

```bash
PAYOS_CLIENT_ID=your_client_id_here
PAYOS_API_KEY=your_api_key_here
PAYOS_CHECKSUM_KEY=your_checksum_key_here
```

### Cấu hình Webhook (Tùy chọn)

Nếu muốn nhận thông báo khi có donation thành công:

1. Vào PayOS Dashboard → **Webhook**
2. Thêm URL webhook: `https://your-domain.railway.app/payos/webhook`
3. Chọn sự kiện: **Payment Success**

## 4. Test trên Local

Tạo file `.env` trong thư mục gốc:

```bash
PAYOS_CLIENT_ID=your_client_id_here
PAYOS_API_KEY=your_api_key_here
PAYOS_CHECKSUM_KEY=your_checksum_key_here
```

Chạy server:

```bash
python app.py
```

Truy cập: http://localhost:5000/donate

## 5. Tính năng

### Người dùng có thể:
- Chọn số tiền donate (10k, 20k, 50k, 100k, 200k hoặc tùy chỉnh)
- Nhập tên (tùy chọn)
- Nhập email (tùy chọn)
- Để lại lời nhắn (tùy chọn)
- Thanh toán qua QR Banking hoặc Ví điện tử

### Sau khi thanh toán:
- Thành công: Hiển thị trang cảm ơn với mã đơn hàng
- Hủy: Hiển thị trang thông báo và cho phép thử lại

## 6. Giao diện

- Nút **☕ Ủng hộ** nổi bật ở đầu header (màu đỏ, hiệu ứng glow)
- Trang donate đẹp mắt, dễ sử dụng
- Responsive trên mobile

## 7. Bảo mật

- Signature verification cho mọi request
- HTTPS bắt buộc trên production
- Không lưu thông tin thẻ
- Webhook signature verification

## 8. Lưu ý

- Số tiền tối thiểu: 1,000 VNĐ
- PayOS hỗ trợ: Banking QR, Ví điện tử (MoMo, ZaloPay, etc.)
- Phí giao dịch: Tham khảo tại PayOS Dashboard
- File tải xuống tự động xóa sau 30 phút

## 9. Troubleshooting

### Lỗi "No credentials"
- Kiểm tra lại environment variables trên Railway
- Đảm bảo không có khoảng trắng thừa

### Lỗi "Invalid signature"
- Kiểm tra lại PAYOS_CHECKSUM_KEY
- Đảm bảo copy đúng từ PayOS Dashboard

### Webhook không hoạt động
- Kiểm tra URL webhook trên PayOS Dashboard
- Đảm bảo domain đã deploy thành công
- Kiểm tra logs trên Railway

## 10. Support

- PayOS Documentation: https://payos.vn/docs
- PayOS Support: support@payos.vn
- Hotline: 1900 xxxx (check PayOS website)

---

**Chúc bạn triển khai thành công! 🎉**
