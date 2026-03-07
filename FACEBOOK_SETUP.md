# Hướng dẫn cấu hình Facebook Login

## Bước 1: Tạo Facebook App

1. Truy cập https://developers.facebook.com/apps/
2. Nhấn "Create App" (Tạo ứng dụng)
3. Chọn "Consumer" hoặc "None" làm use case
4. Điền thông tin:
   - App Name: Tên ứng dụng của bạn (vd: Downloader Pro)
   - App Contact Email: Email liên hệ
5. Nhấn "Create App"

## Bước 2: Thêm Facebook Login

1. Trong Dashboard của App, tìm "Add Products"
2. Tìm "Facebook Login" và nhấn "Set Up"
3. Chọn "Web" platform
4. Nhập URL website của bạn (vd: https://downloaderpro.io.vn)

## Bước 3: Cấu hình OAuth Redirect URIs

1. Vào "Facebook Login" > "Settings" trong menu bên trái
2. Trong "Valid OAuth Redirect URIs", thêm:
   ```
   https://your-domain.com/
   https://your-domain.com/login
   ```
3. Nhấn "Save Changes"

## Bước 4: Lấy App ID và App Secret

1. Vào "Settings" > "Basic" trong menu bên trái
2. Copy "App ID" và "App Secret"
3. Thêm vào file `.env`:
   ```
   FACEBOOK_APP_ID=your_app_id_here
   FACEBOOK_APP_SECRET=your_app_secret_here
   ```

## Bước 5: Chạy Migration

Chạy script để thêm cột `facebook_id` vào database:

```bash
python add_facebook_column.py
```

## Bước 6: Chuyển App sang Live Mode

1. Vào "Settings" > "Basic"
2. Kéo xuống "App Mode"
3. Chuyển từ "Development" sang "Live"
4. Điền đầy đủ thông tin yêu cầu:
   - Privacy Policy URL
   - Terms of Service URL
   - App Icon
   - Category

## Bước 7: Yêu cầu Permissions (nếu cần)

Nếu cần thêm permissions ngoài `public_profile` và `email`:

1. Vào "App Review" > "Permissions and Features"
2. Request các permissions cần thiết
3. Cung cấp video demo và giải thích use case

## Lưu ý

- App ở chế độ Development chỉ cho phép admin, developers, và testers đăng nhập
- Để cho phép tất cả mọi người đăng nhập, cần chuyển sang Live Mode
- Email permission có thể không luôn có (user có thể từ chối)
- Cần xử lý trường hợp user không cung cấp email

## Test

1. Mở trang login: https://your-domain.com/login
2. Nhấn nút "Đăng nhập với Facebook"
3. Cho phép ứng dụng truy cập thông tin
4. Kiểm tra đăng nhập thành công

## Troubleshooting

### Lỗi "App Not Setup"
- Kiểm tra App ID trong .env có đúng không
- Kiểm tra domain đã được thêm vào Valid OAuth Redirect URIs

### Lỗi "Invalid Scope"
- Chỉ sử dụng `public_profile` và `email` trong scope
- Các permissions khác cần được Facebook approve

### User không có email
- Code đã xử lý trường hợp này
- Sẽ tạo username từ Facebook name hoặc ID
