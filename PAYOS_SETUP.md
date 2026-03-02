# Hướng dẫn cấu hình PayOS

## Hiện tại
- Hệ thống đang chạy ở **chế độ demo** vì chưa có cấu hình PayOS
- Khi nhấn nút ủng hộ sẽ mô phỏng thanh toán thành công
- Không có giao dịch thật nào được thực hiện

## Để kích hoạt thanh toán thật

### 1. Đăng ký tài khoản PayOS
- Truy cập: https://my.payos.vn
- Đăng ký tài khoản doanh nghiệp
- Xác thực thông tin theo yêu cầu

### 2. Lấy thông tin API
Sau khi đăng ký thành công, lấy các thông tin sau:
- **Client ID**: Mã định danh ứng dụng
- **API Key**: Khóa API để gọi dịch vụ
- **Checksum Key**: Khóa để tạo chữ ký bảo mật

### 3. Cấu hình biến môi trường

#### Trên Railway (Production):
1. Vào Railway Dashboard
2. Chọn project của bạn
3. Vào tab **Variables**
4. Thêm các biến sau:
```
PAYOS_CLIENT_ID=your_client_id_here
PAYOS_API_KEY=your_api_key_here  
PAYOS_CHECKSUM_KEY=your_checksum_key_here
```

#### Trên máy local (Development):
Tạo file `.env` trong thư mục gốc:
```bash
# PayOS Configuration
PAYOS_CLIENT_ID=your_client_id_here
PAYOS_API_KEY=your_api_key_here
PAYOS_CHECKSUM_KEY=your_checksum_key_here
```

### 4. Restart ứng dụng
- Railway: Deploy lại hoặc restart
- Local: Restart server Python

## Kiểm tra cấu hình
Khi cấu hình đúng, bạn sẽ thấy log:
```
>>> PayOS Client ID: abc12345***
>>> PayOS API Key: def67890***
>>> PayOS Checksum Key length: 64 chars
```

## Lưu ý bảo mật
- **KHÔNG** commit file `.env` vào Git
- **KHÔNG** chia sẻ API keys công khai
- Sử dụng biến môi trường cho production